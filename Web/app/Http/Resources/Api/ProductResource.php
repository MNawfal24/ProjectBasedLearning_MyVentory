<?php

namespace App\Http\Resources\Api;

use App\Models\Stock;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class ProductResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        /** @var Stock|null $stock */
        $stock = $this->relationLoaded('stocks') ? $this->stocks->first() : null;

        return [
            'id' => $this->id,
            'sku' => $this->sku,
            'name' => $this->name,
            'category' => $this->category,
            'unit' => $this->unit,
            'sell_price' => (float) $this->sell_price,
            'buy_price' => (float) $this->buy_price,
            'is_active' => (bool) $this->is_active,
            'sold_quantity' => (int) ($this->sold_quantity ?? 0),
            'outlet_id' => $stock?->outlet_id,
            'stock_id' => $stock?->id,
            'stock' => $stock ? (float) $stock->quantity : 0.0,
            'min_stock' => $stock ? (float) $stock->min_quantity : 0.0,
            'created_at' => $this->created_at?->toIso8601String(),
            'updated_at' => $this->updated_at?->toIso8601String(),
        ];
    }
}
