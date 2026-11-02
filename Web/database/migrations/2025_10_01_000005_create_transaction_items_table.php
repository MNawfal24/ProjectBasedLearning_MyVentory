<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('transaction_items', function (Blueprint $table) {
            $table->id();
            $table->foreignId('transaction_id')->constrained()->cascadeOnDelete();
            $table->foreignId('product_id')->constrained()->restrictOnDelete();
            $table->unsignedSmallInteger('quantity')->default(1);
            // Receipt-level NetSales is split evenly across its item lines, so line revenue is a proxy.
            $table->decimal('line_revenue', 14, 2)->default(0);
            $table->timestamps();

            $table->index(['product_id', 'transaction_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('transaction_items');
    }
};
