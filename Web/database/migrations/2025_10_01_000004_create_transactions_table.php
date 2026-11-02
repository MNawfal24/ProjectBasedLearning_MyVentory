<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('transactions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('outlet_id')->constrained()->cascadeOnDelete();
            $table->string('receipt_number', 64)->nullable()->unique();
            $table->timestamp('occurred_at');
            // Denormalised from occurred_at so grouping by day stays portable across sqlite and postgres.
            $table->date('business_date');
            $table->unsignedTinyInteger('hour');
            $table->string('payment_method', 32);
            $table->boolean('uses_loyalty_card')->default(false);
            $table->decimal('net_sales', 14, 2)->default(0);
            $table->decimal('tax', 14, 2)->default(0);
            $table->decimal('total_amount', 14, 2)->default(0);
            $table->unsignedSmallInteger('total_items')->default(0);
            $table->string('source', 16)->default('manual');
            $table->string('note')->nullable();
            $table->timestamps();

            $table->index(['business_date', 'outlet_id']);
            $table->index('hour');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('transactions');
    }
};
