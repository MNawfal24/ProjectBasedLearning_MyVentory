<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\DashboardController;
use App\Http\Controllers\Api\OutletController;
use App\Http\Controllers\Api\PredictionController;
use App\Http\Controllers\Api\ProductController;
use App\Http\Controllers\Api\StockController;
use App\Http\Controllers\Api\TransactionController;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->name('api.')->group(function () {
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

        // Read-only surface shared by the mobile app and any future client.
        Route::middleware('abilities:read')->group(function () {
            Route::apiResource('outlets', OutletController::class)->only(['index', 'show']);
            Route::apiResource('products', ProductController::class)->only(['index', 'show']);
            Route::get('stocks', [StockController::class, 'index']);
            Route::get('stocks/{stock}', [StockController::class, 'show']);
            Route::apiResource('transactions', TransactionController::class)->only(['index', 'show']);
            Route::get('dashboard/summary', [DashboardController::class, 'summary']);
            Route::get('predictions/sales-forecast', [PredictionController::class, 'salesForecast']);
            Route::get('predictions/demand-forecast', [PredictionController::class, 'demandForecast']);
            Route::get('predictions/stock', [PredictionController::class, 'stockPrediction']);
        });

        // Writes stay in the dashboard. Mobile tokens never carry the write ability.
        Route::middleware(['abilities:write', 'role:admin'])->group(function () {
            Route::apiResource('products', ProductController::class)->only(['store', 'update', 'destroy']);
            Route::post('stocks/movements', [StockController::class, 'store']);
            Route::post('stocks/rebuild', [StockController::class, 'rebuild']);
            Route::patch('stocks/{stock}', [StockController::class, 'update']);
            Route::apiResource('transactions', TransactionController::class)->only(['store', 'destroy']);
        });
    });
});
