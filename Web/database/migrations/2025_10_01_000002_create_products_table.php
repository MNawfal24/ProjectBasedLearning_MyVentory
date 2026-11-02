<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            // SKU is optional: products typed in by hand may not have one yet.
            $table->string('sku', 32)->nullable()->unique();
            $table->string('name')->unique();
            $table->string('category', 48)->nullable();
            $table->string('unit', 16)->default('pcs');
            $table->decimal('sell_price', 12, 2)->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('products');
    }
};
