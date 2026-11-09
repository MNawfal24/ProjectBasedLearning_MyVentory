<?php

namespace Tests\Feature;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Transaction;
use App\Models\TransactionItem;
use App\Services\DashboardStats;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class DashboardStatsTest extends TestCase
{
    use RefreshDatabase;

    private Outlet $outlet;

    private Product $product;

    protected function setUp(): void
    {
        parent::setUp();

        $this->outlet = Outlet::create(['code' => 'SHOP001', 'name' => 'SHOP001']);
        $this->product = Product::create([
            'sku' => 'P001',
            'name' => 'Friendly Coffee (Ice)',
            'unit' => 'pcs',
            'sell_price' => 20000,
        ]);
    }

    private function receipt(string $date, float $net, int $hour = 10, string $payment = 'Cash'): Transaction
    {
        $transaction = Transaction::create([
            'outlet_id' => $this->outlet->id,
            'occurred_at' => "{$date} {$hour}:00:00",
            'business_date' => $date,
            'hour' => $hour,
            'payment_method' => $payment,
            'net_sales' => $net,
            'tax' => round($net * 0.11, 2),
            'total_amount' => round($net * 1.11, 2),
            'total_items' => 1,
        ]);

        TransactionItem::create([
            'transaction_id' => $transaction->id,
            'product_id' => $this->product->id,
            'quantity' => 1,
            'line_revenue' => $net,
        ]);

        return $transaction;
    }

    public function test_kpis_compare_the_period_with_the_one_before_it(): void
    {
        // Two receipts inside the last 7 days, one in the 7 days before that.
        $this->receipt('2025-09-29', 100000.0);
        $this->receipt('2025-09-30', 200000.0);
        $this->receipt('2025-09-23', 100000.0);

        $stats = app(DashboardStats::class)->build(7);

        $this->assertSame('2025-09-24', $stats['period']['from']);
        $this->assertSame('2025-09-30', $stats['period']['to']);
        $this->assertSame(300000.0, $stats['kpis']['revenue']['value']);
        $this->assertSame(100000.0, $stats['kpis']['revenue']['previous']);
        $this->assertSame(200.0, $stats['kpis']['revenue']['change_pct']);
        $this->assertSame(2.0, (float) $stats['kpis']['transactions']['value']);
        $this->assertSame(150000.0, $stats['kpis']['average_basket']['value']);
    }

    public function test_daily_series_has_a_row_for_days_without_sales(): void
    {
        $this->receipt('2025-09-28', 50000.0);
        $this->receipt('2025-09-30', 50000.0);

        $daily = app(DashboardStats::class)->build(7)['daily'];

        $this->assertCount(3, $daily);
        $this->assertSame(['2025-09-28', '2025-09-29', '2025-09-30'], array_column($daily, 'date'));
        $this->assertSame(0.0, $daily[1]['revenue']);
        // The average includes the empty day, so the window is 50000, 0, 50000.
        $this->assertEqualsWithDelta(33333.33, $daily[2]['moving_average'], 0.01);
    }

    public function test_moving_average_smooths_across_the_window(): void
    {
        $this->receipt('2025-09-28', 10000.0);
        $this->receipt('2025-09-29', 20000.0);
        $this->receipt('2025-09-30', 30000.0);

        $daily = app(DashboardStats::class)->build(7)['daily'];

        $this->assertSame(10000.0, $daily[0]['moving_average']);
        $this->assertSame(15000.0, $daily[1]['moving_average']);
        $this->assertSame(20000.0, $daily[2]['moving_average']);
    }

    public function test_hour_breakdown_covers_all_twenty_four_hours(): void
    {
        $this->receipt('2025-09-30', 10000.0, hour: 8);
        $this->receipt('2025-09-30', 10000.0, hour: 8);
        $this->receipt('2025-09-30', 10000.0, hour: 19);

        $hours = app(DashboardStats::class)->build(7)['hours'];

        $this->assertCount(24, $hours);
        $this->assertSame(2, $hours[8]['transactions']);
        $this->assertSame(1, $hours[19]['transactions']);
        $this->assertSame(0, $hours[3]['transactions']);
    }

    public function test_payment_share_sums_to_one_hundred(): void
    {
        $this->receipt('2025-09-30', 10000.0, payment: 'Cash');
        $this->receipt('2025-09-30', 10000.0, payment: 'Cash');
        $this->receipt('2025-09-30', 10000.0, payment: 'BCA');

        $payments = app(DashboardStats::class)->build(7)['payments'];

        $this->assertSame('Cash', $payments[0]['method']);
        $this->assertEqualsWithDelta(100.0, array_sum(array_column($payments, 'share')), 0.2);
    }

    public function test_outlet_filter_narrows_every_figure(): void
    {
        $other = Outlet::create(['code' => 'SHOP002', 'name' => 'SHOP002']);
        $this->receipt('2025-09-30', 10000.0);

        $transaction = $this->receipt('2025-09-30', 90000.0);
        $transaction->update(['outlet_id' => $other->id]);

        $stats = app(DashboardStats::class)->build(7, $other->id);

        $this->assertSame(90000.0, $stats['kpis']['revenue']['value']);
        $this->assertSame(1.0, (float) $stats['kpis']['transactions']['value']);
    }

    public function test_empty_database_reports_zeroes_instead_of_failing(): void
    {
        $stats = app(DashboardStats::class)->build(30);

        $this->assertSame([], $stats['daily']);
        $this->assertSame(0.0, $stats['kpis']['revenue']['value']);
        $this->assertNull($stats['kpis']['revenue']['change_pct']);
        $this->assertCount(24, $stats['hours']);
    }

    public function test_dashboard_page_renders_with_its_props(): void
    {
        $this->receipt('2025-09-30', 10000.0);

        $response = $this->get('/');

        $response->assertOk();
        $response->assertInertia(fn ($page) => $page
            ->component('Dashboard')
            ->has('stats.kpis.revenue')
            ->has('stats.daily')
            ->has('stats.hours', 24)
            ->where('stats.inventory.products', 1)
            ->has('outlets'));
    }

    public function test_unknown_period_falls_back_to_thirty_days(): void
    {
        $this->receipt('2025-09-30', 10000.0);

        $this->get('/?days=45')
            ->assertOk()
            ->assertInertia(fn ($page) => $page
                ->where('filters.days', 30)
                ->where('stats.period.days', 30));
    }
}
