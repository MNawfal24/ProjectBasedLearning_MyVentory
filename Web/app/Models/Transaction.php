<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

#[Fillable([
    'outlet_id',
    'receipt_number',
    'occurred_at',
    'business_date',
    'hour',
    'payment_method',
    'uses_loyalty_card',
    'net_sales',
    'tax',
    'total_amount',
    'total_items',
    'source',
    'note',
])]
class Transaction extends Model
{
    protected function casts(): array
    {
        return [
            'occurred_at' => 'datetime',
            'business_date' => 'date',
            'uses_loyalty_card' => 'boolean',
            'net_sales' => 'decimal:2',
            'tax' => 'decimal:2',
            'total_amount' => 'decimal:2',
        ];
    }

    public function outlet(): BelongsTo
    {
        return $this->belongsTo(Outlet::class);
    }

    public function items(): HasMany
    {
        return $this->hasMany(TransactionItem::class);
    }
}
