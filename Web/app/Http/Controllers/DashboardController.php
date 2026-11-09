<?php

namespace App\Http\Controllers;

use App\Models\Outlet;
use App\Models\Transaction;
use App\Services\DashboardStats;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    public function index(Request $request, DashboardStats $stats): Response
    {
        $days = $request->integer('days', 30);
        $days = in_array($days, DashboardStats::PERIODS, true) ? $days : 30;
        $outletId = $request->integer('outlet') ?: null;

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
        ]);
    }
}
