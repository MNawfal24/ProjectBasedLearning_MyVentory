<?php

namespace App\Http\Resources\Api;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class StockMovementResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'outlet_id' => $this->outlet_id,
            'product_id' => $this->product_id,
            'type' => $this->type,
            'quantity' => (float) $this->quantity,
            'reference' => $this->reference,
            'note' => $this->note,
            'occurred_at' => $this->occurred_at?->toIso8601String(),
            'outlet' => $this->whenLoaded('outlet', fn () => [
                'id' => $this->outlet->id,
                'code' => $this->outlet->code,
                'name' => $this->outlet->name,
            ]),
            'product' => $this->whenLoaded('product', fn () => [
                'id' => $this->product->id,
                'name' => $this->product->name,
                'unit' => $this->product->unit,
            ]),
        ];
    }
}
