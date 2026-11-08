<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\DashboardController;
use App\Http\Controllers\Api\OutletController;
use App\Http\Controllers\Api\ProductController;
use App\Http\Controllers\Api\StockController;
use App\Http\Controllers\Api\TransactionController;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function () {
    Route::get('health', function () {
        DB::connection()->select('select 1');

        return response()->json([
            'status' => 'ok',
            'database' => DB::connection()->getDatabaseName(),
            'time' => now()->toIso8601String(),
        ]);
    });

    Route::post('auth/login', [AuthController::class, 'login'])->middleware('throttle:10,1');

    Route::middleware('auth:sanctum')->group(function () {
        Route::get('auth/me', [AuthController::class, 'me']);
        Route::post('auth/logout', [AuthController::class, 'logout']);

        Route::apiResource('outlets', OutletController::class)->only(['index', 'show']);

        Route::apiResource('products', ProductController::class);

        Route::get('stocks', [StockController::class, 'index']);
        Route::post('stocks/movements', [StockController::class, 'store']);
        Route::post('stocks/rebuild', [StockController::class, 'rebuild']);
        Route::get('stocks/{stock}', [StockController::class, 'show']);
        Route::patch('stocks/{stock}', [StockController::class, 'update']);

        Route::apiResource('transactions', TransactionController::class)->only(['index', 'store', 'show', 'destroy']);

        Route::get('dashboard/summary', [DashboardController::class, 'summary']);
    });
});
