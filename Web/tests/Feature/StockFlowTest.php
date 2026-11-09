<?php

namespace Tests\Feature;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\StockMovement;
use App\Models\Transaction;
use App\Models\User;
use App\Services\SalesRecorder;
use App\Services\StockLedger;
use Carbon\CarbonImmutable;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class StockFlowTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        $this->actingAs(User::factory()->admin()->create());
    }

    private function outlet(): Outlet
    {
        return Outlet::create(['code' => 'SHOP001', 'name' => 'SHOP001']);
    }

    private function product(float $price = 20000): Product
    {
        return Product::create([
            'sku' => 'P001',
            'name' => 'Friendly Coffee (Ice)',
            'unit' => 'pcs',
            'sell_price' => $price,
        ]);
    }

    public function test_stock_in_movement_raises_the_balance(): void
    {
        $outlet = $this->outlet();
        $product = $this->product();

        app(StockLedger::class)->record($outlet, $product, 'in', 40);

        $stock = Stock::query()->firstOrFail();
        $this->assertSame('40.00', $stock->quantity);
    }

    public function test_stock_out_movement_lowers_the_balance(): void
    {
        $outlet = $this->outlet();
        $product = $this->product();
        $ledger = app(StockLedger::class);

        $ledger->record($outlet, $product, 'in', 10);
        $ledger->record($outlet, $product, 'out', 4);

        $this->assertSame('6.00', Stock::query()->firstOrFail()->quantity);
    }

    public function test_adjustment_stores_the_signed_difference_not_the_input(): void
    {
        $outlet = $this->outlet();
        $product = $this->product();
        $ledger = app(StockLedger::class);
        $ledger->record($outlet, $product, 'in', 10);

        $this->patch(route('stock.update', Stock::query()->firstOrFail()), ['min_quantity' => 5])->assertRedirect();

        $this->post(route('stock.store'), [
            'outlet_id' => $outlet->id,
            'product_id' => $product->id,
            'type' => 'adjustment',
            'quantity' => 7,
        ])->assertRedirect();

        $this->assertSame('7.00', Stock::query()->firstOrFail()->quantity);
        $this->assertSame('-3.00', (string) StockMovement::query()->where('type', 'adjustment')->value('quantity'));
    }

    public function test_minimum_quantity_is_editable_and_marks_the_row_low(): void
    {
        $outlet = $this->outlet();
        $product = $this->product();
        app(StockLedger::class)->record($outlet, $product, 'in', 3);
        $stock = Stock::query()->firstOrFail();

        $this->patch(route('stock.update', $stock), ['min_quantity' => 5])->assertRedirect();

        $stock->refresh();
        $this->assertSame('5.00', $stock->min_quantity);
        $this->assertTrue($stock->isLow());
    }

    public function test_manual_sale_creates_receipt_lines_and_moves_stock(): void
    {
        $outlet = $this->outlet();
        $product = $this->product(25000);
        app(StockLedger::class)->record($outlet, $product, 'in', 20);

        $this->post(route('transactions.store'), [
            'outlet_id' => $outlet->id,
            'payment_method' => 'Cash',
            'occurred_at' => '2025-10-01T09:30:00',
            'items' => [['product_id' => $product->id, 'quantity' => 2]],
        ])->assertRedirect(route('transactions.index'));

        $transaction = Transaction::query()->with('items')->firstOrFail();
        $this->assertSame('50000.00', $transaction->net_sales);
        $this->assertSame('5500.00', $transaction->tax);
        $this->assertSame('55500.00', $transaction->total_amount);
        $this->assertSame('2025-10-01', $transaction->business_date->toDateString());
        $this->assertSame(9, $transaction->hour);
        $this->assertCount(1, $transaction->items);
        $this->assertSame('18.00', Stock::query()->firstOrFail()->quantity);
    }

    public function test_manual_sale_rejects_an_unknown_product(): void
    {
        $outlet = $this->outlet();

        $this->post(route('transactions.store'), [
            'outlet_id' => $outlet->id,
            'payment_method' => 'Cash',
            'items' => [['product_id' => 999, 'quantity' => 1]],
        ])->assertSessionHasErrors('items.0.product_id');

        $this->assertSame(0, Transaction::query()->count());
    }

    public function test_imported_receipts_do_not_touch_stock(): void
    {
        $outlet = $this->outlet();
        $product = $this->product();

        app(SalesRecorder::class)->record(
            outlet: $outlet,
            lines: [['product_id' => $product->id, 'quantity' => 1]],
            occurredAt: CarbonImmutable::parse('2025-09-30 10:00:00'),
            source: 'import',
        );

        $this->assertSame(0, Stock::query()->count());
    }
}
