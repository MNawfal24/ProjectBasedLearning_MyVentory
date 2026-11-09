<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\Api\StoreStockMovementRequest;
use App\Http\Requests\Api\UpdateStockRequest;
use App\Http\Resources\Api\StockMovementResource;
use App\Http\Resources\Api\StockResource;
use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\StockMovement;
use App\Services\StockLedger;
use Carbon\CarbonImmutable;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class StockController extends Controller
{
    public function index(Request $request): AnonymousResourceCollection
    {
        $query = Stock::query()
            ->with(['outlet:id,code,name', 'product:id,name,sku,unit'])
            ->whereHas('product');

        if ($outletId = $request->integer('outlet_id')) {
            $query->where('outlet_id', $outletId);
        }

        $status = $request->string('status')->toString();
        if ($status === 'low') {
            $query->whereColumn('quantity', '<=', 'min_quantity')->where('quantity', '>', 0);
        } elseif ($status === 'out') {
            $query->where('quantity', '<=', 0);
        }

        if ($search = $request->string('search')->trim()->toString()) {
            $query->whereHas('product', function ($query) use ($search) {
                $query->where('name', 'like', "%{$search}%")
                    ->orWhere('sku', 'like', "%{$search}%");
            });
        }

        $perPage = min(max($request->integer('per_page', 50), 1), 100);

        return StockResource::collection($query->orderBy('quantity')->paginate($perPage));
    }

    public function show(Stock $stock): StockResource
    {
        $stock->load(['outlet:id,code,name', 'product:id,name,sku,unit']);

        return new StockResource($stock);
    }

    public function store(StoreStockMovementRequest $request, StockLedger $ledger): JsonResponse
    {
        $data = $request->validated();
        $outlet = $this->resolveOutlet($data['outlet_id'] ?? null);
        $product = Product::query()->findOrFail($data['product_id']);
        $occurredAt = isset($data['occurred_at']) ? CarbonImmutable::parse($data['occurred_at']) : null;

        if ($data['type'] === 'adjustment') {
            $current = (float) StockMovement::query()
                ->where('outlet_id', $outlet->id)
                ->where('product_id', $product->id)
                ->sum('quantity');
            $delta = (float) $data['quantity'] - $current;

            if (abs($delta) < 0.005) {
                throw ValidationException::withMessages([
                    'quantity' => ['Jumlah tersebut sama dengan saldo saat ini.'],
                ]);
            }

            $movement = $ledger->record(
                $outlet,
                $product,
                'adjustment',
                $delta,
                'stock-opname',
                $data['note'] ?? null,
                $occurredAt,
            );
        } else {
            if ((float) $data['quantity'] <= 0) {
                throw ValidationException::withMessages([
                    'quantity' => ['Jumlah harus lebih dari nol.'],
                ]);
            }

            $movement = $ledger->record(
                $outlet,
                $product,
                $data['type'],
                (float) $data['quantity'],
                null,
                $data['note'] ?? null,
                $occurredAt,
            );
        }

        $stock = Stock::query()
            ->where('outlet_id', $outlet->id)
            ->where('product_id', $product->id)
            ->with(['outlet:id,code,name', 'product:id,name,sku,unit'])
            ->firstOrFail();

        return response()->json([
            'movement' => new StockMovementResource($movement->load(['outlet:id,code,name', 'product:id,name,unit'])),
            'stock' => new StockResource($stock),
        ], 201);
    }

    public function update(UpdateStockRequest $request, Stock $stock, StockLedger $ledger): StockResource
    {
        $ledger->setMinimum($stock->outlet, $stock->product, (float) $request->validated('min_quantity'));

        $stock = $stock->fresh(['outlet:id,code,name', 'product:id,name,sku,unit']);

        return new StockResource($stock);
    }

    public function rebuild(): JsonResponse
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

        return response()->json([
            'message' => 'Saldo stok dihitung ulang.',
            'series' => $balances->count(),
        ]);
    }

    private function resolveOutlet(?int $outletId): Outlet
    {
        if ($outletId) {
            return Outlet::query()->findOrFail($outletId);
        }

        $outlet = Outlet::query()->orderBy('id')->first();

        if (! $outlet) {
            throw ValidationException::withMessages([
                'outlet_id' => ['Belum ada outlet. Jalankan seeder terlebih dahulu.'],
            ]);
        }

        return $outlet;
    }
}
