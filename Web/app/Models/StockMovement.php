<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

#[Fillable(['outlet_id', 'product_id', 'type', 'quantity', 'reference', 'note', 'occurred_at'])]
class StockMovement extends Model
{
    public const TYPES = ['in', 'out', 'adjustment', 'sale'];

    protected function casts(): array
    {
        return [
            'quantity' => 'decimal:2',
            'occurred_at' => 'datetime',
        ];
    }

    public function outlet(): BelongsTo
    {
        return $this->belongsTo(Outlet::class);
    }

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}
