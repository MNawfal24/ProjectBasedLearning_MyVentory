<?php

namespace App\Http\Controllers;

use App\Models\Outlet;
use App\Models\Transaction;
use App\Services\DashboardStats;
use App\Services\MlClient;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;
use RuntimeException;

class DashboardController extends Controller
{
    public function index(Request $request, DashboardStats $stats, MlClient $ml): Response
    {
        $days = $request->integer('days', 30);
        $days = in_array($days, DashboardStats::PERIODS, true) ? $days : 30;
        $outletId = $request->integer('outlet') ?: null;
        try {
            $response = $ml->post('/sales-forecast', [
                'outlet' => $outletId ? Outlet::query()->find($outletId)?->code : null,
                'horizon_days' => 7,
            ]);
            $salesForecast = $response->successful() ? $response->json() : ['error' => 'Prediksi penjualan tidak tersedia.'];
        } catch (RuntimeException) {
            $salesForecast = ['error' => 'Layanan prediksi sedang tidak tersedia.'];
        }

        return Inertia::render('Dashboard', [
            'stats' => $stats->build($days, $outletId),
            'filters' => [
                'days' => $days,
                'outlet' => $outletId,
            ],
            'outlets' => Outlet::query()->orderBy('code')->get(['id', 'code', 'name']),
            'recent' => Transaction::query()
                ->with(['outlet:id,code', 'items.product:id,name'])
                ->latest('occurred_at')
                ->limit(6)
                ->get()
                ->map(fn (Transaction $transaction) => [
                    'id' => $transaction->id,
                    'receipt_number' => $transaction->receipt_number,
                    'outlet' => $transaction->outlet->code,
                    'occurred_at' => $transaction->occurred_at->toIso8601String(),
                    'total_amount' => (float) $transaction->total_amount,
                    'items' => $transaction->items->map(fn ($item) => [
                        'name' => $item->product->name,
                        'quantity' => $item->quantity,
                    ])->all(),
                ]),
            'sales_forecast' => $salesForecast,
        ]);
    }
}
