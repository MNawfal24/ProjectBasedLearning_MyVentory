<?php

namespace App\Services;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Transaction;
use Carbon\CarbonImmutable;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

/**
 * Creates a sale from the dashboard form: receipt header, item lines and the
 * stock movements that follow from them. Tax is 11% of net sales, which is the
 * ratio the imported receipts use.
 */
class SalesRecorder
{
    public const TAX_RATE = 0.11;

    public function __construct(private readonly StockLedger $ledger) {}

    /**
     * @param  array<int, array{product_id: int, quantity: int}>  $lines
     */
    public function record(
        Outlet $outlet,
        array $lines,
        ?CarbonImmutable $occurredAt = null,
        string $paymentMethod = 'Cash',
        bool $usesLoyaltyCard = false,
        string $source = 'manual',
        ?string $note = null,
    ): Transaction {
        $occurredAt ??= CarbonImmutable::now();
        $products = Product::query()->findMany(array_column($lines, 'product_id'))->keyBy('id');

        $rows = [];
        $netSales = 0.0;
        $totalItems = 0;

        foreach ($lines as $line) {
            $product = $products->get($line['product_id']);
            if (! $product) {
                throw ValidationException::withMessages(['items' => 'Produk pada baris penjualan tidak ditemukan.']);
            }
            $quantity = (int) $line['quantity'];
            $lineRevenue = round((float) $product->sell_price * $quantity, 2);
            $netSales += $lineRevenue;
            $totalItems += $quantity;
            $rows[] = ['product' => $product, 'quantity' => $quantity, 'line_revenue' => $lineRevenue];
        }

        $tax = round($netSales * self::TAX_RATE, 2);

        return DB::transaction(function () use ($outlet, $rows, $occurredAt, $netSales, $tax, $totalItems, $paymentMethod, $usesLoyaltyCard, $source, $note) {
            $transaction = Transaction::create([
                'outlet_id' => $outlet->id,
                'occurred_at' => $occurredAt,
                'business_date' => $occurredAt->toDateString(),
                'hour' => (int) $occurredAt->format('G'),
                'payment_method' => $paymentMethod,
                'uses_loyalty_card' => $usesLoyaltyCard,
                'net_sales' => round($netSales, 2),
                'tax' => $tax,
                'total_amount' => round($netSales + $tax, 2),
                'total_items' => $totalItems,
                'source' => $source,
                'note' => $note,
            ]);

            foreach ($rows as $row) {
                $transaction->items()->create([
                    'product_id' => $row['product']->id,
                    'quantity' => $row['quantity'],
                    'line_revenue' => $row['line_revenue'],
                ]);

                if ($source === 'manual') {
                    $this->ledger->record($outlet, $row['product'], 'sale', $row['quantity'], "receipt:{$transaction->id}", null, $occurredAt);
                }
            }

            return $transaction;
        });
    }
}
