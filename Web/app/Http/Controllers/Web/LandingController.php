<?php

namespace App\Http\Controllers\Web;

use App\Http\Controllers\Controller;
use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\Transaction;
use App\Services\DashboardStats;
use Illuminate\Http\Request;
use Inertia\Inertia;
use Inertia\Response;

class LandingController extends Controller
{
    public function index(Request $request, DashboardStats $stats): Response
    {
        if ($request->user()) {
            return to_route('dashboard');
        }

        return Inertia::render('Landing/Index', [
            'stats' => [
                'products' => Product::query()->where('is_active', true)->count(),
                'outlets' => Outlet::query()->count(),
                'units_on_hand' => (float) Stock::query()->sum('quantity'),
                'transactions' => Transaction::query()->count(),
                'revenue' => (float) Transaction::query()->sum('net_sales'),
            ],
        ]);
    }
}
