<?php

namespace Tests\Feature;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Transaction;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class TransactionPageTest extends TestCase
{
    use RefreshDatabase;

    private function seedReceipts(): void
    {
        $outlet = Outlet::create(['code' => 'SHOP001', 'name' => 'SHOP001']);
        $product = Product::create([
            'sku' => 'P001',
            'name' => 'Friendly Coffee (Ice)',
            'unit' => 'pcs',
            'sell_price' => 20000,
        ]);

        foreach ([['2025-09-28', 'Cash'], ['2025-09-29', 'BCA'], ['2025-09-30', 'Cash']] as $index => [$date, $payment]) {
            $transaction = Transaction::create([
                'outlet_id' => $outlet->id,
                'receipt_number' => "SHOP001-{$index}",
                'occurred_at' => "{$date} 10:00:00",
                'business_date' => $date,
                'hour' => 10,
                'payment_method' => $payment,
                'net_sales' => 20000,
                'tax' => 2200,
                'total_amount' => 22200,
                'total_items' => 1,
            ]);
            $transaction->items()->create([
                'product_id' => $product->id,
                'quantity' => 1,
                'line_revenue' => 20000,
            ]);
        }
    }

    public function test_index_lists_receipts_newest_first(): void
    {
        $this->seedReceipts();

        $response = $this->get('/transactions');

        $response->assertOk();
        $response->assertInertia(fn ($page) => $page
            ->component('Transactions/Index')
            ->has('transactions.data', 3)
            ->where('transactions.data.0.receipt_number', 'SHOP001-2')
            ->has('products')
            ->has('outlets'));
    }

    public function test_search_and_filters_narrow_the_table(): void
    {
        $this->seedReceipts();

        $this->get('/transactions?payment=BCA')
            ->assertInertia(fn ($page) => $page->has('transactions.data', 1)->where('transactions.data.0.payment_method', 'BCA'));

        $this->get('/transactions?search=SHOP001-0')
            ->assertInertia(fn ($page) => $page->has('transactions.data', 1));

        $this->get('/transactions?from=2025-09-29&to=2025-09-29')
            ->assertInertia(fn ($page) => $page->has('transactions.data', 1));
    }

    public function test_invalid_date_filter_is_rejected_instead_of_failing(): void
    {
        $this->seedReceipts();

        $this->from('/transactions')
            ->get('/transactions?from=abc')
            ->assertRedirect('/transactions')
            ->assertSessionHasErrors('from');

        $this->from('/transactions')
            ->get('/transactions?to=2025-13-01')
            ->assertRedirect('/transactions')
            ->assertSessionHasErrors('to');
    }

    public function test_receipt_times_are_sent_as_iso_8601(): void
    {
        $this->seedReceipts();

        $this->get('/transactions')
            ->assertInertia(fn ($page) => $page
                ->where('transactions.data.0.occurred_at', fn ($value) => is_string($value) && str_contains($value, 'T')));
    }

    public function test_store_validation_rejects_missing_items(): void
    {
        $outlet = Outlet::create(['code' => 'SHOP001', 'name' => 'SHOP001']);

        $this->post('/transactions', [
            'outlet_id' => $outlet->id,
            'payment_method' => 'Cash',
            'items' => [],
        ])->assertSessionHasErrors('items');
    }

    public function test_unknown_route_returns_404(): void
    {
        $this->get('/tidak-ada')->assertNotFound();
    }
}
