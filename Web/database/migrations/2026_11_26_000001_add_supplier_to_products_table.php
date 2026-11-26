<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('products', function (Blueprint $table) {
            // Kontak pemasok produk; nomor disimpan apa adanya (0812..., +62812..., dst.)
            // dan dinormalisasi ke format wa.me/62... oleh aplikasi mobile.
            $table->string('supplier_name', 120)->nullable()->after('buy_price');
            $table->string('supplier_phone', 20)->nullable()->after('supplier_name');
        });
    }

    public function down(): void
    {
        Schema::table('products', function (Blueprint $table) {
            $table->dropColumn(['supplier_name', 'supplier_phone']);
        });
    }
};
