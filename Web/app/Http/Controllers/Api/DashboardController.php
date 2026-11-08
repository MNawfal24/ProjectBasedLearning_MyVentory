<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Resources\Api\OutletResource;
use App\Models\Outlet;
use App\Services\DashboardStats;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function summary(Request $request, DashboardStats $stats): JsonResponse
    {
        $days = $request->integer('days', 30);
        $days = in_array($days, DashboardStats::PERIODS, true) ? $days : 30;
        $outletId = $request->integer('outlet_id') ?: null;

        return response()->json([
            'stats' => $stats->build($days, $outletId),
            'filters' => [
                'days' => $days,
                'outlet_id' => $outletId,
            ],
            'outlets' => OutletResource::collection(
                Outlet::query()->orderBy('code')->get(['id', 'code', 'name', 'city'])
            ),
        ]);
    }
}
