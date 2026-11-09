<?php

namespace Tests\Feature;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ProductPageTest extends TestCase
{
    use RefreshDatabase;

    public function test_products_can_be_created_and_updated(): void
    {
        $this->post('/products', [
            'name' => 'Matcha Latte (Ice)',
            'sku' => 'P100',
            'category' => 'Coffee',
            'unit' => 'pcs',
            'sell_price' => 24000,
        ])->assertRedirect();

        $product = Product::query()->firstOrFail();
        $this->assertSame('Matcha Latte (Ice)', $product->name);

        $this->patch("/products/{$product->id}", [
            'name' => 'Matcha Latte (Ice)',
            'sku' => 'P100',
            'category' => 'Coffee',
            'unit' => 'pcs',
            'sell_price' => 26000,
            'is_active' => false,
        ])->assertRedirect();

        $this->assertSame('26000.00', Product::query()->firstOrFail()->sell_price);
        $this->assertFalse(Product::query()->firstOrFail()->is_active);
    }

    public function test_duplicate_product_name_is_rejected(): void
    {
        Product::create(['sku' => 'P1', 'name' => 'Lemons', 'unit' => 'pcs', 'sell_price' => 18000]);

        $this->post('/products', [
            'name' => 'Lemons',
            'unit' => 'pcs',
            'sell_price' => 18000,
        ])->assertSessionHasErrors('name');

        $this->assertSame(1, Product::query()->count());
    }

    public function test_stock_page_exposes_rows_and_summary(): void
    {
        $outlet = Outlet::create(['code' => 'SHOP001', 'name' => 'SHOP001']);
        $product = Product::create(['sku' => 'P1', 'name' => 'Lemons', 'unit' => 'pcs', 'sell_price' => 18000]);
        Stock::create(['outlet_id' => $outlet->id, 'product_id' => $product->id, 'quantity' => 2, 'min_quantity' => 5]);

        $this->get('/stock')
            ->assertOk()
            ->assertInertia(fn ($page) => $page
                ->component('Stock/Index')
                ->has('stocks.data', 1)
                ->where('summary.low', 1)
                ->where('summary.out', 0));
    }
}
