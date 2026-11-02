<?php

namespace App\Services;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\Transaction;
use App\Models\TransactionItem;
use Carbon\CarbonImmutable;
use Illuminate\Database\Eloquent\Builder;

/**
 * Aggregates the ledger into what the dashboard shows. Every figure is computed
 * from stored rows, never estimated, and grouped in PHP where the equivalent SQL
 * would not run on both sqlite (tests) and postgres (deployment).
 */
class DashboardStats
{
    public const PERIODS = [7, 30, 90, 365];

    public function build(int $days = 30, ?int $outletId = null): array
    {
        $days = in_array($days, self::PERIODS, true) ? $days : 30;
        $to = Transaction::query()->max('business_date');
        $to = $to ? CarbonImmutable::parse($to) : CarbonImmutable::today();
        $from = $to->subDays($days - 1);

        $current = $this->scope($from, $to, $outletId);
        $previousFrom = $from->subDays($days);
        $previousTo = $from->subDay();
        $previous = $this->scope($previousFrom, $previousTo, $outletId);

        $daily = $this->daily($current);

        return [
            'period' => [
                'days' => $days,
                'from' => $from->toDateString(),
                'to' => $to->toDateString(),
                'previous_from' => $previousFrom->toDateString(),
                'previous_to' => $previousTo->toDateString(),
            ],
            'kpis' => $this->kpis($current, $previous),
            // The newest day that actually carries receipts, so the panel is never a
            // structural zero when the export stops a few days short of today.
            'last_sale' => $this->lastSale($outletId),
            'daily' => $daily,
            'hours' => $this->byHour($current),
            'weekdays' => $this->byWeekday($daily),
            'payments' => $this->payments($current),
            'top_products' => $this->topProducts($current),
            'low_stock' => $this->lowStock($outletId),
            'inventory' => [
                'products' => Product::query()->where('is_active', true)->count(),
                'outlets' => Outlet::query()->count(),
                'units_on_hand' => (float) Stock::query()
                    ->when($outletId, fn (Builder $query) => $query->where('outlet_id', $outletId))
                    ->sum('quantity'),
            ],
        ];
    }

    private function lastSale(?int $outletId): array
    {
        $latest = Transaction::query()
            ->when($outletId, fn (Builder $query) => $query->where('outlet_id', $outletId))
            ->max('business_date');

        if (! $latest) {
            return ['date' => null, 'revenue' => 0.0, 'transactions' => 0];
        }

        $query = Transaction::query()
            ->where('business_date', $latest)
            ->when($outletId, fn (Builder $query) => $query->where('outlet_id', $outletId));

        return [
            'date' => CarbonImmutable::parse($latest)->toDateString(),
            'revenue' => round((float) (clone $query)->sum('net_sales'), 2),
            'transactions' => (clone $query)->count(),
        ];
    }

    private function scope(CarbonImmutable $from, CarbonImmutable $to, ?int $outletId): Builder
    {
        return Transaction::query()
            ->whereBetween('business_date', [$from->toDateString(), $to->toDateString()])
            ->when($outletId, fn (Builder $query) => $query->where('outlet_id', $outletId));
    }

    private function kpis(Builder $current, Builder $previous): array
    {
        $now = $this->totals($current);
        $before = $this->totals($previous);

        return [
            'revenue' => $this->kpi($now['revenue'], $before['revenue']),
            'transactions' => $this->kpi($now['transactions'], $before['transactions']),
            'average_basket' => $this->kpi($now['average_basket'], $before['average_basket']),
            'items_sold' => $this->kpi($now['items_sold'], $before['items_sold']),
        ];
    }

    private function totals(Builder $query): array
    {
        $row = (clone $query)
            ->selectRaw('COUNT(*) as transactions, COALESCE(SUM(net_sales), 0) as revenue, COALESCE(SUM(total_items), 0) as items_sold')
            ->first();

        $transactions = (int) $row->transactions;
        $revenue = (float) $row->revenue;

        return [
            'transactions' => $transactions,
            'revenue' => $revenue,
            'items_sold' => (int) $row->items_sold,
            'average_basket' => $transactions > 0 ? round($revenue / $transactions, 2) : 0.0,
        ];
    }

    private function kpi(float $value, float $previous): array
    {
        return [
            'value' => round($value, 2),
            'previous' => round($previous, 2),
            'change_pct' => $previous > 0 ? round((($value - $previous) / $previous) * 100, 1) : null,
        ];
    }

    /**
     * Every date in the period, including days with no receipt, so the trend line
     * has no gaps.
     */
    private function daily(Builder $query): array
    {
        $rows = (clone $query)
            ->selectRaw('business_date, COUNT(*) as transactions, COALESCE(SUM(net_sales), 0) as revenue')
            ->groupBy('business_date')
            ->orderBy('business_date')
            ->get()
            ->keyBy(fn ($row) => CarbonImmutable::parse($row->business_date)->toDateString());

        if ($rows->isEmpty()) {
            return [];
        }

        $cursor = CarbonImmutable::parse($rows->keys()->first());
        $last = CarbonImmutable::parse($rows->keys()->last());
        $series = [];
        while ($cursor->lessThanOrEqualTo($last)) {
            $key = $cursor->toDateString();
            $row = $rows->get($key);
            $series[] = [
                'date' => $key,
                'revenue' => round((float) ($row->revenue ?? 0), 2),
                'transactions' => (int) ($row->transactions ?? 0),
            ];
            $cursor = $cursor->addDay();
        }

        $window = 7;
        foreach ($series as $index => $point) {
            $slice = array_slice($series, max(0, $index - $window + 1), min($index + 1, $window));
            $series[$index]['moving_average'] = round(array_sum(array_column($slice, 'revenue')) / count($slice), 2);
        }

        return $series;
    }

    private function byHour(Builder $query): array
    {
        $rows = (clone $query)
            ->selectRaw('hour, COUNT(*) as transactions, COALESCE(SUM(net_sales), 0) as revenue')
            ->groupBy('hour')
            ->get()
            ->keyBy('hour');

        return collect(range(0, 23))->map(function (int $hour) use ($rows) {
            $row = $rows->get($hour);

            return [
                'hour' => $hour,
                'transactions' => (int) ($row->transactions ?? 0),
                'revenue' => round((float) ($row->revenue ?? 0), 2),
            ];
        })->all();
    }

    private function byWeekday(array $daily): array
    {
        $names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        $buckets = array_fill_keys($names, ['transactions' => 0, 'revenue' => 0.0]);

        foreach ($daily as $point) {
            $name = $names[CarbonImmutable::parse($point['date'])->dayOfWeekIso - 1];
            $buckets[$name]['transactions'] += $point['transactions'];
            $buckets[$name]['revenue'] += $point['revenue'];
        }

        return collect($buckets)->map(fn (array $bucket, string $name) => [
            'weekday' => $name,
            'transactions' => $bucket['transactions'],
            'revenue' => round($bucket['revenue'], 2),
        ])->values()->all();
    }

    private function payments(Builder $query): array
    {
        $rows = (clone $query)
            ->selectRaw('payment_method, COUNT(*) as transactions, COALESCE(SUM(net_sales), 0) as revenue')
            ->groupBy('payment_method')
            ->orderByDesc('transactions')
            ->get();

        $total = max(1, $rows->sum('transactions'));

        return $rows->map(fn ($row) => [
            'method' => $row->payment_method,
            'transactions' => (int) $row->transactions,
            'revenue' => round((float) $row->revenue, 2),
            'share' => round(((int) $row->transactions / $total) * 100, 1),
        ])->all();
    }

    private function topProducts(Builder $query): array
    {
        $ids = (clone $query)->select('id');

        return TransactionItem::query()
            ->whereIn('transaction_id', $ids)
            ->selectRaw('product_id, SUM(quantity) as quantity, COALESCE(SUM(line_revenue), 0) as revenue')
            ->groupBy('product_id')
            ->orderByDesc('quantity')
            ->limit(8)
            ->with('product:id,name,category')
            ->get()
            ->map(fn ($row) => [
                'name' => $row->product?->name ?? 'Unknown',
                'category' => $row->product?->category,
                'quantity' => (int) $row->quantity,
                'revenue' => round((float) $row->revenue, 2),
            ])->all();
    }

    private function lowStock(?int $outletId): array
    {
        return Stock::query()
            ->when($outletId, fn (Builder $query) => $query->where('outlet_id', $outletId))
            ->whereColumn('quantity', '<=', 'min_quantity')
            ->with(['outlet:id,code,name', 'product:id,name,unit'])
            ->orderBy('quantity')
            ->limit(8)
            ->get()
            ->map(fn (Stock $stock) => [
                'outlet' => $stock->outlet->code,
                'product' => $stock->product->name,
                'unit' => $stock->product->unit,
                'quantity' => (float) $stock->quantity,
                'min_quantity' => (float) $stock->min_quantity,
            ])->all();
    }
}
