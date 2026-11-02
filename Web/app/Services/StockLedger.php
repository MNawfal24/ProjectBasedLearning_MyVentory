<?php

namespace App\Services;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\StockMovement;
use Carbon\CarbonInterface;

/**
 * Single place where stock balances change. Every write appends a movement and
 * rebuilds the cached balance on `stocks`, so the two never disagree.
 */
class StockLedger
{
    public function record(
        Outlet $outlet,
        Product $product,
        string $type,
        float $quantity,
        ?string $reference = null,
        ?string $note = null,
        ?CarbonInterface $occurredAt = null,
    ): StockMovement {
        $movement = StockMovement::create([
            'outlet_id' => $outlet->id,
            'product_id' => $product->id,
            'type' => $type,
            'quantity' => $this->signed($type, $quantity),
            'reference' => $reference,
            'note' => $note,
            'occurred_at' => $occurredAt ?? now(),
        ]);

        $this->refreshBalance($outlet, $product);

        return $movement;
    }

    public function setMinimum(Outlet $outlet, Product $product, float $minimum): Stock
    {
        $stock = $this->stockRow($outlet, $product);
        $stock->update(['min_quantity' => $minimum]);

        return $stock;
    }

    public function refreshBalance(Outlet $outlet, Product $product): Stock
    {
        $stock = $this->stockRow($outlet, $product);
        $balance = StockMovement::query()
            ->where('outlet_id', $outlet->id)
            ->where('product_id', $product->id)
            ->sum('quantity');

        $stock->update(['quantity' => $balance]);

        return $stock;
    }

    private function stockRow(Outlet $outlet, Product $product): Stock
    {
        return Stock::firstOrCreate(
            ['outlet_id' => $outlet->id, 'product_id' => $product->id],
            ['quantity' => 0, 'min_quantity' => 0],
        );
    }

    private function signed(string $type, float $quantity): float
    {
        return in_array($type, ['out', 'sale'], true) ? -abs($quantity) : $quantity;
    }
}
