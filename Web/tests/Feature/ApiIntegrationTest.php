<?php

namespace Tests\Feature;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\StockMovement;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class ApiIntegrationTest extends TestCase
{
    use RefreshDatabase;

    private function token(): string
    {
        User::factory()->create([
            'email' => 'api@example.com',
            'password' => Hash::make('secret123'),
        ]);

        $response = $this->postJson('/api/v1/auth/login', [
            'email' => 'api@example.com',
            'password' => 'secret123',
            'device_name' => 'phpunit',
        ])->assertOk();

        return $response->json('token');
    }

    public function test_api_requires_authentication(): void
    {
        $this->getJson('/api/v1/products')->assertUnauthorized();
    }

    public function test_login_me_and_logout(): void
    {
        $token = $this->token();
        $headers = ['Authorization' => "Bearer {$token}"];

        $this->getJson('/api/v1/auth/me', $headers)
            ->assertOk()
            ->assertJsonPath('data.email', 'api@example.com');

        $this->postJson('/api/v1/auth/logout', [], $headers)->assertOk();

        // Token should be deleted after logout.
        $this->assertDatabaseMissing('personal_access_tokens', [
            'tokenable_type' => User::class,
            'name' => 'phpunit',
        ]);
    }

    public function test_product_crud_uses_the_stock_ledger(): void
    {
        $token = $this->token();
        $headers = ['Authorization' => "Bearer {$token}"];

        $outlet = Outlet::query()->create(['code' => 'SHOP001', 'name' => 'Main']);

        $created = $this->postJson('/api/v1/products', [
            'name' => 'Arabica',
            'unit' => 'Kg',
            'sell_price' => 50000,
            'buy_price' => 30000,
            'stock' => 12,
            'min_stock' => 3,
            'outlet_id' => $outlet->id,
        ], $headers)->assertCreated();

        $id = $created->json('data.id');
        $this->assertSame(12.0, (float) $created->json('data.stock'));

        $this->patchJson("/api/v1/products/{$id}", [
            'stock' => 20,
            'min_stock' => 5,
        ], $headers)->assertOk()->assertJsonPath('data.stock', 20);

        $this->postJson('/api/v1/stocks/movements', [
            'outlet_id' => $outlet->id,
            'product_id' => $id,
            'type' => 'in',
            'quantity' => 5,
        ], $headers)->assertCreated()->assertJsonPath('stock.quantity', 25);

        $this->assertEquals(25, StockMovement::query()
            ->where('product_id', $id)
            ->sum('quantity'));

        $this->deleteJson("/api/v1/products/{$id}", [], $headers)->assertOk();
        $this->assertSoftDeleted('products', ['id' => $id]);
        $this->assertSame(0, Product::query()->whereKey($id)->count());
    }

    public function test_product_info_update_without_stock_preserves_stock_balance(): void
    {
        $token = $this->token();
        $headers = ['Authorization' => "Bearer {$token}"];

        $outlet = Outlet::query()->create(['code' => 'SHOP001', 'name' => 'Main']);

        $created = $this->postJson('/api/v1/products', [
            'name' => 'Robusta Special',
            'unit' => 'Kg',
            'sell_price' => 45000,
            'buy_price' => 25000,
            'stock' => 15,
            'min_stock' => 5,
            'outlet_id' => $outlet->id,
        ], $headers)->assertCreated();

        $id = $created->json('data.id');

        // Edit product master info WITHOUT sending 'stock'
        $updated = $this->patchJson("/api/v1/products/{$id}", [
            'name' => 'Robusta Special Edition',
            'sell_price' => 48000,
        ], $headers)->assertOk();

        // Stock balance MUST remain 15, not reset to 0 or changed
        $this->assertSame(15.0, (float) $updated->json('data.stock'));
        $this->assertSame('Robusta Special Edition', $updated->json('data.name'));
        $this->assertSame(48000.0, (float) $updated->json('data.sell_price'));
    }

    public function test_stock_movement_without_outlet_id_falls_back_to_default_outlet(): void
    {
        $token = $this->token();
        $headers = ['Authorization' => "Bearer {$token}"];

        $outlet = Outlet::query()->create(['code' => 'SHOP001', 'name' => 'Main']);
        $product = Product::query()->create([
            'name' => 'Liberica',
            'unit' => 'Kg',
            'sell_price' => 60000,
        ]);

        // Post movement with outlet_id omitted
        $movement = $this->postJson('/api/v1/stocks/movements', [
            'product_id' => $product->id,
            'type' => 'in',
            'quantity' => 10,
        ], $headers)->assertCreated();

        $this->assertSame(10.0, (float) $movement->json('stock.quantity'));
        $this->assertSame($outlet->id, $movement->json('stock.outlet_id'));
    }

    public function test_stock_minimum_can_be_updated_directly(): void
    {
        $token = $this->token();
        $headers = ['Authorization' => "Bearer {$token}"];

        $outlet = Outlet::query()->create(['code' => 'SHOP001', 'name' => 'Main']);
        $product = Product::query()->create([
            'name' => 'Toraja',
            'unit' => 'Kg',
            'sell_price' => 70000,
        ]);

        $created = $this->getJson('/api/v1/products/'.$product->id, $headers)->assertOk();
        $stockId = $created->json('data.stock_id');
        $this->assertNotNull($stockId);

        $this->patchJson("/api/v1/stocks/{$stockId}", [
            'min_quantity' => 8,
        ], $headers)->assertOk()->assertJsonPath('data.min_quantity', 8);

        $this->getJson('/api/v1/products/'.$product->id, $headers)
            ->assertOk()
            ->assertJsonPath('data.min_stock', 8);
    }

    public function test_transaction_sale_and_void_restore_stock(): void
    {
        $token = $this->token();
        $headers = ['Authorization' => "Bearer {$token}"];

        $outlet = Outlet::query()->create(['code' => 'SHOP001', 'name' => 'Main']);
        $product = Product::query()->create([
            'name' => 'Arabica',
            'unit' => 'Kg',
            'sell_price' => 50000,
        ]);

        $this->postJson('/api/v1/stocks/movements', [
            'outlet_id' => $outlet->id,
            'product_id' => $product->id,
            'type' => 'in',
            'quantity' => 10,
        ], $headers)->assertCreated();

        $transaction = $this->postJson('/api/v1/transactions', [
            'outlet_id' => $outlet->id,
            'payment_method' => 'Cash',
            'items' => [['product_id' => $product->id, 'quantity' => 2]],
        ], $headers)->assertCreated();

        $this->assertSame(2.0, (float) $transaction->json('data.items.0.quantity'));
        $this->assertSame(100000.0, (float) $transaction->json('data.net_sales'));
        $this->assertSame(111000.0, (float) $transaction->json('data.total_amount'));

        $this->getJson('/api/v1/products/'.$product->id, $headers)
            ->assertOk()
            ->assertJsonPath('data.stock', 8);

        $this->deleteJson('/api/v1/transactions/'.$transaction->json('data.id'), [], $headers)
            ->assertOk();

        $this->getJson('/api/v1/products/'.$product->id, $headers)
            ->assertOk()
            ->assertJsonPath('data.stock', 10);
    }

    public function test_dashboard_summary_is_available(): void
    {
        $token = $this->token();

        $this->getJson('/api/v1/dashboard/summary?days=30', [
            'Authorization' => "Bearer {$token}",
        ])->assertOk()->assertJsonStructure([
            'stats' => ['period', 'kpis', 'daily', 'inventory'],
            'outlets',
        ]);
    }
}
