<?php

use App\Http\Controllers\DashboardController;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\StockController;
use App\Http\Controllers\TransactionController;
use Illuminate\Support\Facades\Route;

Route::get('/', [DashboardController::class, 'index'])->name('dashboard');

Route::get('/transactions', [TransactionController::class, 'index'])->name('transactions.index');
Route::post('/transactions', [TransactionController::class, 'store'])->name('transactions.store');

Route::get('/stock', [StockController::class, 'index'])->name('stock.index');
Route::post('/stock', [StockController::class, 'store'])->name('stock.store');
Route::post('/stock/rebuild', [StockController::class, 'rebuild'])->name('stock.rebuild');
Route::patch('/stock/{stock}', [StockController::class, 'update'])->name('stock.update');

Route::get('/products', [ProductController::class, 'index'])->name('products.index');
Route::post('/products', [ProductController::class, 'store'])->name('products.store');
Route::patch('/products/{product}', [ProductController::class, 'update'])->name('products.update');
