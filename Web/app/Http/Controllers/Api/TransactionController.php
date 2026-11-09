<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\Api\StoreTransactionRequest;
use App\Http\Resources\Api\TransactionResource;
use App\Models\Outlet;
use App\Models\Product;
use App\Models\StockMovement;
use App\Models\Transaction;
use App\Services\SalesRecorder;
use App\Services\StockLedger;
use Carbon\CarbonImmutable;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class TransactionController extends Controller
{
    public function index(Request $request): AnonymousResourceCollection
    {
        $request->validate([
            'from' => ['nullable', 'date_format:Y-m-d'],
            'to' => ['nullable', 'date_format:Y-m-d'],
        ]);

        $query = Transaction::query()
            ->with(['outlet:id,code,name', 'items.product:id,name'])
            ->latest('occurred_at');

        if ($search = $request->string('search')->trim()->toString()) {
            $query->where('receipt_number', 'like', "%{$search}%");
        }
        if ($outletId = $request->integer('outlet_id')) {
            $query->where('outlet_id', $outletId);
        }
        if ($method = $request->string('payment')->trim()->toString()) {
            $query->where('payment_method', $method);
        }
        if ($from = $request->string('from')->toString()) {
            $query->where('business_date', '>=', $from);
        }
        if ($to = $request->string('to')->toString()) {
            $query->where('business_date', '<=', $to);
        }

        $perPage = min(max($request->integer('per_page', 25), 1), 100);

        return TransactionResource::collection($query->paginate($perPage));
    }

    public function store(StoreTransactionRequest $request, SalesRecorder $recorder): JsonResponse
    {
        $data = $request->validated();

        $transaction = $recorder->record(
            outlet: Outlet::query()->findOrFail($data['outlet_id']),
            lines: $data['items'],
            occurredAt: isset($data['occurred_at']) ? CarbonImmutable::parse($data['occurred_at']) : null,
            paymentMethod: $data['payment_method'],
            usesLoyaltyCard: (bool) ($data['uses_loyalty_card'] ?? false),
            note: $data['note'] ?? null,
        );

        return (new TransactionResource($transaction->load(['outlet:id,code,name', 'items.product:id,name'])))
            ->response()
            ->setStatusCode(201);
    }

    public function show(Transaction $transaction): TransactionResource
    {
        $transaction->load(['outlet:id,code,name', 'items.product:id,name']);

        return new TransactionResource($transaction);
    }

    public function destroy(Transaction $transaction, StockLedger $ledger): JsonResponse
    {
        if ($transaction->source !== 'manual') {
            throw ValidationException::withMessages([
                'transaction' => ['Transaksi hasil impor tidak dapat dihapus.'],
            ]);
        }

        DB::transaction(function () use ($transaction, $ledger) {
            $movements = StockMovement::query()
                ->where('reference', "receipt:{$transaction->id}")
                ->where('type', 'sale')
                ->get();

            foreach ($movements as $movement) {
                $outlet = Outlet::query()->find($movement->outlet_id);
                $product = Product::query()->withTrashed()->find($movement->product_id);

                if ($outlet && $product) {
                    $ledger->record(
                        $outlet,
                        $product,
                        'in',
                        abs((float) $movement->quantity),
                        "void:{$transaction->id}",
                        'Pembatalan transaksi.',
                    );
                }
            }

            $transaction->delete();
        });

        return response()->json(['message' => 'Transaksi dibatalkan dan stok dikembalikan.']);
    }
}
