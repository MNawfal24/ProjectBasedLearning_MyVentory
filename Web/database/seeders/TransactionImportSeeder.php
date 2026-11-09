<?php

namespace Database\Seeders;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use App\Models\Transaction;
use Carbon\CarbonImmutable;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use RuntimeException;

/**
 * Imports the café's real transaction export (ML/data/Transactions.csv).
 *
 * The export has no product master, no prices per line and no stock counts, so:
 * - product names come from the receipt item strings, and sell_price is the mean
 *   revenue per unit line across the export (receipt NetSales split evenly over
 *   its item lines);
 * - stock is reconstructed: an opening 'in' movement 14 days before the last
 *   imported day, then 'sale' movements for the final week of receipts, so the
 *   balance is arithmetic over real sales rather than a guessed number.
 *
 * Dates are moved forward by whole weeks so the export ends yesterday: the export
 * stops in September 2025, and a dashboard whose period ended a year ago would be
 * empty. Whole weeks keep every weekday pattern intact, and the original range is
 * printed at the end of the import.
 */
class TransactionImportSeeder extends Seeder
{
    private const OPENING_DAYS = 14;

    private const REPLAY_DAYS = 7;

    private const CHUNK = 500;

    /** @var array<int, array{outlet: Outlet, product: Product, quantity: int, occurred_at: string}> */
    private array $replaySales = [];

    private int $shiftDays = 0;

    public function run(): void
    {
        $path = $this->csvPath();
        if (! is_file($path)) {
            throw new RuntimeException("Dataset tidak ditemukan: {$path}");
        }
        if (Transaction::query()->exists()) {
            $this->command?->warn('Transaksi sudah ada, import dilewati.');

            return;
        }

        $summary = $this->scan($path);
        $this->shiftDays = $this->shiftFor($summary['last_day']);
        $products = $this->createProducts($summary['products']);
        $outlets = $this->createOutlets($summary['outlets']);

        $this->importReceipts($path, $products, $outlets, $summary['last_day']);
        $this->reconstructStock($summary['recent_qty'], $products, $outlets, $summary['last_day']);

        $this->command?->info(sprintf(
            'Import selesai: %d transaksi, %d produk, %d outlet. Rentang asli %s sampai %s, digeser %d hari.',
            Transaction::query()->count(),
            count($products),
            count($outlets),
            $summary['first_day'],
            $summary['last_day'],
            $this->shiftDays,
        ));
    }

    /**
     * Whole weeks between the export's last day and yesterday, so the seeded data
     * ends where a dashboard expects it and weekday patterns stay aligned.
     */
    private function shiftFor(string $lastDay): int
    {
        $gap = CarbonImmutable::parse($lastDay)->diffInDays(CarbonImmutable::yesterday(), false);

        return max(0, intdiv($gap, 7)) * 7;
    }

    private function shiftDate(string $date): string
    {
        return CarbonImmutable::parse($date)->addDays($this->shiftDays)->toDateString();
    }

    private function shiftDateTime(string $dateTime): string
    {
        return CarbonImmutable::parse($dateTime)->addDays($this->shiftDays)->toDateTimeString();
    }

    private function csvPath(): string
    {
        return base_path(config('myventory.seed_csv'));
    }

    /**
     * First pass: product quantities, outlets, and the per-day quantity needed to
     * size opening stock. Only the last OPENING_DAYS of data is kept per series.
     */
    private function scan(string $path): array
    {
        $handle = fopen($path, 'r');
        fgetcsv($handle);

        $products = [];
        $outlets = [];
        $recentQty = [];
        $lastDay = null;
        $firstDay = null;

        while (($row = fgetcsv($handle)) !== false) {
            [$outlet, $date, $time, $netSales, , , $receipt, $items] = $row;
            $lastDay = max($lastDay ?? $date, $date);
            $firstDay = min($firstDay ?? $date, $date);
            $outlets[$outlet] = true;

            $names = array_map('trim', explode(',', $items));
            $lines = count($names);
            $revenuePerLine = (float) $netSales / $lines;

            foreach ($names as $name) {
                $products[$name] ??= ['quantity' => 0, 'revenue' => 0.0];
                $products[$name]['quantity']++;
                $products[$name]['revenue'] += $revenuePerLine;
            }

            unset($time, $receipt);
        }

        fclose($handle);

        $handle = fopen($path, 'r');
        fgetcsv($handle);
        $cutoff = CarbonImmutable::parse($lastDay)->subDays(self::OPENING_DAYS - 1)->toDateString();

        while (($row = fgetcsv($handle)) !== false) {
            [$outlet, $date, , , , , , $items] = $row;
            if ($date < $cutoff) {
                continue;
            }
            foreach (array_map('trim', explode(',', $items)) as $name) {
                $key = "{$outlet}|{$name}|{$date}";
                $recentQty[$key] = ($recentQty[$key] ?? 0) + 1;
            }
        }

        fclose($handle);

        return [
            'products' => $products,
            'outlets' => array_keys($outlets),
            'recent_qty' => $recentQty,
            'first_day' => $firstDay,
            'last_day' => $lastDay,
        ];
    }

    private function createProducts(array $stats): array
    {
        ksort($stats);
        $products = [];
        $index = 1;

        foreach ($stats as $name => $stat) {
            $product = Product::create([
                'sku' => 'P'.str_pad((string) $index, 3, '0', STR_PAD_LEFT),
                'name' => $name,
                'category' => $this->categoryOf($name),
                'unit' => 'pcs',
                'sell_price' => round($stat['revenue'] / max(1, $stat['quantity']), 2),
            ]);
            $products[$name] = $product;
            $index++;
        }

        return $products;
    }

    /**
     * The export has no category column, so the category is read from the item name.
     * It is a sorting aid for the product list, not a stored attribute of the source.
     */
    private function categoryOf(string $name): string
    {
        $lower = strtolower($name);
        $food = ['cake', 'bread', 'waffle', 'croffle', 'donat', 'pisang', 'nutella', 'klepon', 'pie'];
        $tea = ['tea', 'chamomile', 'jasmine', 'nostaltea'];
        $nonCoffee = ['air mineral', 'jus', 'susu', 'apple', 'berry', 'liquid', 'lemon', 'sitrus', 'summer', 'sunset', 'moody', 'biru', 'gula', 'sugar', 'moca', 'mocha'];

        foreach ($food as $keyword) {
            if (str_contains($lower, $keyword)) {
                return 'Makanan';
            }
        }
        foreach ($tea as $keyword) {
            if (str_contains($lower, $keyword)) {
                return 'Teh';
            }
        }
        foreach ($nonCoffee as $keyword) {
            if (str_contains($lower, $keyword)) {
                return 'Non-kopi';
            }
        }

        return 'Kopi';
    }

    /**
     * @return array<string, Outlet>
     */
    private function createOutlets(array $codes): array
    {
        sort($codes);
        $outlets = [];
        foreach ($codes as $code) {
            $outlets[$code] = Outlet::create(['code' => $code, 'name' => $code]);
        }

        return $outlets;
    }

    private function importReceipts(string $path, array $products, array $outlets, string $lastDay): void
    {
        $handle = fopen($path, 'r');
        fgetcsv($handle);

        $replayFrom = $this->shiftDate(
            CarbonImmutable::parse($lastDay)->subDays(self::REPLAY_DAYS - 1)->toDateString(),
        );
        $batch = [];
        $replayReceipts = [];

        while (($row = fgetcsv($handle)) !== false) {
            $batch[] = $row;
            if (count($batch) === self::CHUNK) {
                $replayReceipts = array_merge($replayReceipts, $this->insertBatch($batch, $products, $outlets, $replayFrom));
                $batch = [];
            }
        }
        if ($batch !== []) {
            $replayReceipts = array_merge($replayReceipts, $this->insertBatch($batch, $products, $outlets, $replayFrom));
        }

        fclose($handle);

        $this->replaySales = $replayReceipts;
    }

    /**
     * Inserts a chunk of receipts plus their item lines, and returns the sale
     * movements to replay for receipts inside the stock replay window.
     */
    private function insertBatch(array $rows, array $products, array $outlets, string $replayFrom): array
    {
        $transactions = [];
        $linesByReceipt = [];

        foreach ($rows as $row) {
            [$outletCode, $date, $time, $netSales, $tax, $total, $receipt, $items, $totalItem, $payment, $loyalty] = $row;
            $names = array_map('trim', explode(',', $items));
            $occurredAt = $this->shiftDateTime("{$date} {$time}");
            $businessDate = $this->shiftDate($date);

            $transactions[] = [
                'outlet_id' => $outlets[$outletCode]->id,
                'receipt_number' => $receipt,
                'occurred_at' => $occurredAt,
                'business_date' => $businessDate,
                'hour' => (int) substr($time, 0, 2),
                'payment_method' => $payment,
                'uses_loyalty_card' => (bool) $loyalty,
                'net_sales' => $netSales,
                'tax' => $tax,
                'total_amount' => $total,
                'total_items' => (int) $totalItem,
                'source' => 'import',
                'created_at' => now(),
                'updated_at' => now(),
            ];

            $linesByReceipt[$receipt] = [
                'names' => $names,
                'revenue' => round((float) $netSales / count($names), 2),
                'outlet' => $outlets[$outletCode],
                'occurred_at' => $occurredAt,
            ];
        }

        DB::table('transactions')->insert($transactions);

        $ids = DB::table('transactions')
            ->whereIn('receipt_number', array_keys($linesByReceipt))
            ->pluck('id', 'receipt_number');

        $items = [];
        foreach ($linesByReceipt as $receipt => $line) {
            foreach ($line['names'] as $name) {
                $items[] = [
                    'transaction_id' => $ids[$receipt],
                    'product_id' => $products[$name]->id,
                    'quantity' => 1,
                    'line_revenue' => $line['revenue'],
                    'created_at' => now(),
                    'updated_at' => now(),
                ];
            }
        }
        DB::table('transaction_items')->insert($items);

        $replay = [];
        foreach ($linesByReceipt as $receipt => $line) {
            if ($line['occurred_at'] < $replayFrom) {
                continue;
            }
            foreach ($line['names'] as $name) {
                $replay[] = [
                    'outlet' => $line['outlet'],
                    'product' => $products[$name],
                    'quantity' => 1,
                    'occurred_at' => $line['occurred_at'],
                ];
            }
        }

        return $replay;
    }

    private function reconstructStock(array $recentQty, array $products, array $outlets, string $lastDay): void
    {
        $perSeries = [];
        foreach ($recentQty as $key => $quantity) {
            [$outletCode, $name, $date] = explode('|', $key, 3);
            $perSeries["{$outletCode}|{$name}"][$date] = $quantity;
        }

        $openingAt = CarbonImmutable::parse($lastDay)->addDays($this->shiftDays)->subDays(self::OPENING_DAYS)->toDateTimeString();

        foreach ($perSeries as $key => $byDate) {
            [$outletCode, $name] = explode('|', $key, 2);
            $dailyAverage = array_sum($byDate) / self::OPENING_DAYS;
            $outlet = $outlets[$outletCode];
            $product = $products[$name];

            Stock::create([
                'outlet_id' => $outlet->id,
                'product_id' => $product->id,
                'quantity' => 0,
                'min_quantity' => max(1, (int) ceil($dailyAverage * 3)),
            ]);

            DB::table('stock_movements')->insert([
                'outlet_id' => $outlet->id,
                'product_id' => $product->id,
                'type' => 'in',
                'quantity' => round($dailyAverage * self::OPENING_DAYS, 2),
                'reference' => 'opening-balance',
                'note' => 'Saldo awal dari kecepatan penjualan 14 hari terakhir.',
                'occurred_at' => $openingAt,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }

        $movements = [];
        foreach ($this->replaySales as $sale) {
            $movements[] = [
                'outlet_id' => $sale['outlet']->id,
                'product_id' => $sale['product']->id,
                'type' => 'sale',
                'quantity' => -$sale['quantity'],
                'reference' => 'import-replay',
                'occurred_at' => $sale['occurred_at'],
                'created_at' => now(),
                'updated_at' => now(),
            ];
        }
        foreach (array_chunk($movements, 1000) as $chunk) {
            DB::table('stock_movements')->insert($chunk);
        }

        $balances = DB::table('stock_movements')
            ->selectRaw('outlet_id, product_id, SUM(quantity) as balance')
            ->groupBy('outlet_id', 'product_id')
            ->get();

        foreach ($balances as $balance) {
            DB::table('stocks')
                ->where('outlet_id', $balance->outlet_id)
                ->where('product_id', $balance->product_id)
                ->update(['quantity' => $balance->balance]);
        }
    }
}
