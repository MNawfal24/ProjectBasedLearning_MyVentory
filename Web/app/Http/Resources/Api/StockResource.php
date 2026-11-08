<?php

namespace App\Http\Resources\Api;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class StockResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'outlet_id' => $this->outlet_id,
            'product_id' => $this->product_id,
            'outlet' => $this->whenLoaded('outlet', fn () => [
                'id' => $this->outlet->id,
                'code' => $this->outlet->code,
                'name' => $this->outlet->name,
            ]),
            'product' => $this->whenLoaded('product', fn () => [
                'id' => $this->product->id,
                'name' => $this->product->name,
                'sku' => $this->product->sku,
                'unit' => $this->product->unit,
            ]),
            'quantity' => (float) $this->quantity,
            'min_quantity' => (float) $this->min_quantity,
            'is_low' => $this->isLow(),
            'updated_at' => $this->updated_at?->toIso8601String(),
        ];
    }
}
