<?php

namespace App\Http\Controllers;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\StockMovement;
use App\Services\StockLedger;
use Carbon\CarbonImmutable;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;
use Inertia\Inertia;
use Inertia\Response;

class StockController extends Controller
{
    public function index(Request $request): Response
    {
        $query = Stock::query()->with(['outlet:id,code', 'product:id,name,unit,sku']);

        if ($outletId = $request->integer('outlet')) {
            $query->where('outlet_id', $outletId);
        }

        $status = $request->string('status')->toString();
        if ($status === 'low') {
            $query->whereColumn('quantity', '<=', 'min_quantity')->where('quantity', '>', 0);
        } elseif ($status === 'out') {
            $query->where('quantity', '<=', 0);
        }

        $rows = $query->orderBy('quantity')->paginate(25)->withQueryString();

        return Inertia::render('Stock/Index', [
            'stocks' => $rows->through(fn (Stock $stock) => [
                'id' => $stock->id,
                'outlet_id' => $stock->outlet_id,
                'product_id' => $stock->product_id,
                'outlet' => $stock->outlet->code,
                'product' => $stock->product->name,
                'sku' => $stock->product->sku,
                'unit' => $stock->product->unit,
                'quantity' => (float) $stock->quantity,
                'min_quantity' => (float) $stock->min_quantity,
            ]),
            'movements' => StockMovement::query()
                ->with(['outlet:id,code', 'product:id,name,unit'])
                ->latest('occurred_at')
                ->limit(12)
                ->get()
                ->map(fn (StockMovement $movement) => [
                    'id' => $movement->id,
                    'outlet' => $movement->outlet->code,
                    'product' => $movement->product->name,
                    'unit' => $movement->product->unit,
                    'type' => $movement->type,
                    'quantity' => (float) $movement->quantity,
                    'note' => $movement->note,
                    'occurred_at' => $movement->occurred_at->toIso8601String(),
                ]),
            'filters' => [
                'outlet' => $request->integer('outlet') ?: null,
                'status' => $status,
            ],
            'outlets' => Outlet::query()->orderBy('code')->get(['id', 'code']),
            'products' => Product::query()->where('is_active', true)->orderBy('name')->get(['id', 'name', 'sku', 'unit']),
            'summary' => [
                'series' => Stock::query()->count(),
                'low' => Stock::query()->whereColumn('quantity', '<=', 'min_quantity')->where('quantity', '>', 0)->count(),
                'out' => Stock::query()->where('quantity', '<=', 0)->count(),
                'units' => (float) Stock::query()->sum('quantity'),
            ],
        ]);
    }

    public function store(Request $request, StockLedger $ledger)
    {
        $data = $request->validate([
            'outlet_id' => ['required', 'exists:outlets,id'],
            'product_id' => ['required', 'exists:products,id'],
            'type' => ['required', 'in:in,out,adjustment'],
            'quantity' => ['required', 'numeric', 'min:0', 'max:1000000'],
            'note' => ['nullable', 'string', 'max:255'],
            'occurred_at' => ['nullable', 'date'],
        ]);

        $outlet = Outlet::query()->findOrFail($data['outlet_id']);
        $product = Product::query()->findOrFail($data['product_id']);
        $occurredAt = isset($data['occurred_at']) ? CarbonImmutable::parse($data['occurred_at']) : null;

        if ($data['type'] === 'adjustment') {
            $current = (float) StockMovement::query()
                ->where('outlet_id', $outlet->id)
                ->where('product_id', $product->id)
                ->sum('quantity');
            $delta = (float) $data['quantity'] - $current;
            if (abs($delta) < 0.005) {
                throw ValidationException::withMessages(['quantity' => 'Jumlah tersebut sama dengan saldo saat ini.']);
            }
            $ledger->record($outlet, $product, 'adjustment', $delta, 'stock-opname', $data['note'] ?? null, $occurredAt);
        } else {
            if ((float) $data['quantity'] <= 0) {
                throw ValidationException::withMessages(['quantity' => 'Jumlah harus lebih dari nol.']);
            }
            $ledger->record($outlet, $product, $data['type'], (float) $data['quantity'], null, $data['note'] ?? null, $occurredAt);
        }

        return back()->with('success', 'Pergerakan stok tercatat.');
    }

    public function update(Request $request, Stock $stock, StockLedger $ledger)
    {
        $data = $request->validate([
            'min_quantity' => ['required', 'numeric', 'min:0', 'max:1000000'],
        ]);

        $ledger->setMinimum($stock->outlet, $stock->product, (float) $data['min_quantity']);

        return back()->with('success', 'Batas minimum stok diperbarui.');
    }

    /**
     * Rebuilds the cached balance of every row from its movements. Useful after a
     * manual database edit, and it is what the test suite asserts against.
     */
    public function rebuild()
    {
        $balances = StockMovement::query()
            ->select('outlet_id', 'product_id', DB::raw('SUM(quantity) as balance'))
            ->groupBy('outlet_id', 'product_id')
            ->get();

        foreach ($balances as $balance) {
            Stock::query()
                ->where('outlet_id', $balance->outlet_id)
                ->where('product_id', $balance->product_id)
                ->update(['quantity' => $balance->balance]);
        }

        return back()->with('success', 'Saldo stok dihitung ulang.');
    }
}
