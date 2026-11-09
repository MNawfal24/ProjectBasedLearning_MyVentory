<?php

namespace App\Http\Resources\Api;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class TransactionResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'receipt_number' => $this->receipt_number,
            'outlet_id' => $this->outlet_id,
            'outlet' => $this->whenLoaded('outlet', fn () => [
                'id' => $this->outlet->id,
                'code' => $this->outlet->code,
                'name' => $this->outlet->name,
            ]),
            'occurred_at' => $this->occurred_at?->toIso8601String(),
            'business_date' => $this->business_date?->toDateString(),
            'hour' => $this->hour,
            'payment_method' => $this->payment_method,
            'uses_loyalty_card' => (bool) $this->uses_loyalty_card,
            'net_sales' => (float) $this->net_sales,
            'tax' => (float) $this->tax,
            'total_amount' => (float) $this->total_amount,
            'total_items' => $this->total_items,
            'source' => $this->source,
            'note' => $this->note,
            'items' => $this->whenLoaded('items', fn () => $this->items->map(fn ($item) => [
                'id' => $item->id,
                'product_id' => $item->product_id,
                'product_name' => $item->product?->name,
                'quantity' => $item->quantity,
                'line_revenue' => (float) $item->line_revenue,
            ])->all()),
            'created_at' => $this->created_at?->toIso8601String(),
        ];
    }
}
