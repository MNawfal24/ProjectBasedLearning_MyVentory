<?php

namespace App\Http\Controllers;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Transaction;
use App\Services\SalesRecorder;
use Carbon\CarbonImmutable;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class TransactionController extends Controller
{
    public function index(Request $request): Response
    {
        $request->validate([
            'from' => ['nullable', 'date_format:Y-m-d'],
            'to' => ['nullable', 'date_format:Y-m-d'],
        ]);

        $query = Transaction::query()
            ->with(['outlet:id,code', 'items.product:id,name'])
            ->latest('occurred_at');

        if ($search = $request->string('search')->trim()->toString()) {
            $query->where('receipt_number', 'like', "%{$search}%");
        }
        if ($outletId = $request->integer('outlet')) {
            $query->where('outlet_id', $outletId);
        }
        if ($method = $request->string('payment')->toString()) {
            $query->where('payment_method', $method);
        }
        if ($from = $request->string('from')->toString()) {
            $query->where('business_date', '>=', $from);
        }
        if ($to = $request->string('to')->toString()) {
            $query->where('business_date', '<=', $to);
        }

        $transactions = $query->paginate(25)->withQueryString();

        return Inertia::render('Transactions/Index', [
            'transactions' => $transactions->through(fn (Transaction $transaction) => [
                'id' => $transaction->id,
                'receipt_number' => $transaction->receipt_number,
                'occurred_at' => $transaction->occurred_at->toIso8601String(),
                'outlet' => $transaction->outlet->code,
                'payment_method' => $transaction->payment_method,
                'uses_loyalty_card' => $transaction->uses_loyalty_card,
                'total_items' => $transaction->total_items,
                'net_sales' => (float) $transaction->net_sales,
                'tax' => (float) $transaction->tax,
                'total_amount' => (float) $transaction->total_amount,
                'source' => $transaction->source,
                'items' => $transaction->items->map(fn ($item) => [
                    'name' => $item->product->name,
                    'quantity' => $item->quantity,
                ])->all(),
            ]),
            'filters' => [
                'search' => $request->string('search')->toString(),
                'outlet' => $request->integer('outlet') ?: null,
                'payment' => $request->string('payment')->toString(),
                'from' => $request->string('from')->toString(),
                'to' => $request->string('to')->toString(),
            ],
            'outlets' => Outlet::query()->orderBy('code')->get(['id', 'code']),
            'payments' => Transaction::query()->distinct()->orderBy('payment_method')->pluck('payment_method'),
            'products' => Product::query()
                ->where('is_active', true)
                ->orderBy('name')
                ->get(['id', 'name', 'sku', 'unit', 'sell_price']),
        ]);
    }

    public function store(Request $request, SalesRecorder $recorder)
    {
        $data = $request->validate([
            'outlet_id' => ['required', 'exists:outlets,id'],
            'occurred_at' => ['nullable', 'date'],
            'payment_method' => ['required', 'string', 'max:32'],
            'uses_loyalty_card' => ['boolean'],
            'note' => ['nullable', 'string', 'max:255'],
            'items' => ['required', 'array', 'min:1', 'max:20'],
            'items.*.product_id' => ['required', 'distinct', 'exists:products,id'],
            'items.*.quantity' => ['required', 'integer', 'min:1', 'max:999'],
        ]);

        $transaction = $recorder->record(
            outlet: Outlet::query()->findOrFail($data['outlet_id']),
            lines: $data['items'],
            occurredAt: isset($data['occurred_at']) ? CarbonImmutable::parse($data['occurred_at']) : null,
            paymentMethod: $data['payment_method'],
            usesLoyaltyCard: (bool) ($data['uses_loyalty_card'] ?? false),
            note: $data['note'] ?? null,
        );

        return redirect()
            ->route('transactions.index')
            ->with('success', "Transaksi {$transaction->id} tercatat.");
    }
}
