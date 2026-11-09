<?php

namespace Database\Seeders;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Transaction;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use RuntimeException;

/**
 * Imports the café's real transaction export (ML/data/Transactions.csv) exactly
 * as recorded: no date shifting, no derived prices, no stock reconstruction.
 *
 * Everything stored is read from the file:
 * - outlet code, receipt number, date, time, payment method, loyalty flag,
 *   net sales, tax and total amount;
 * - item lines from the comma separated item names, one unit per name;
 * - sell_price only when a receipt contains exactly one item, because then the
 *   line revenue is the item's own price. Receipts with several items only give
 *   a receipt total, which says nothing about the individual prices.
 *
 * Stock is never written here. It comes from Stock.csv through StockImportSeeder.
 */
class TransactionImportSeeder extends Seeder
{
    private const CHUNK = 500;

    private const HEADER = [
        'Outlet', 'Date', 'Time', 'NetSales', 'Tax', 'TotalAmount',
        'ReceiptNumber', 'Items', 'TotalItem', 'PaymentMethod', 'UseLoyaltyCard',
    ];

    public function run(): void
    {
        $path = base_path(config('myventory.seed_csv'));

        if (! is_file($path)) {
            throw new RuntimeException("Dataset tidak ditemukan: {$path}");
        }

        if (Transaction::query()->exists()) {
            $this->command?->warn('Transaksi sudah ada, import dilewati.');

            return;
        }

        $summary = $this->scan($path);
        $products = $this->createProducts($summary['products']);
        $outlets = $this->createOutlets($summary['outlets']);

        $this->importReceipts($path, $products, $outlets);

        $this->command?->info(sprintf(
            'Import selesai: %d transaksi, %d produk, %d outlet, rentang %s sampai %s.',
            Transaction::query()->count(),
            count($products),
            count($outlets),
            $summary['first_day'],
            $summary['last_day'],
        ));
    }

    /**
     * Reads the file once to collect product names, exact prices from single-item
     * receipts, outlet codes and the date range.
     */
    private function scan(string $path): array
    {
        $handle = $this->open($path);

        $products = [];
        $outlets = [];
        $firstDay = null;
        $lastDay = null;

        while (($row = fgetcsv($handle)) !== false) {
            [$outlet, $date, , $netSales, , , , $items] = $row;
            $outlets[$outlet] = true;
            $firstDay = $firstDay === null ? $date : min($firstDay, $date);
            $lastDay = $lastDay === null ? $date : max($lastDay, $date);

            $names = $this->names($items);
            $single = count($names) === 1;

            foreach ($names as $name) {
                $products[$name] ??= ['price' => null, 'priced_at' => null, 'positions' => 0];
                $products[$name]['positions']++;
            }

            if ($single && (float) $netSales > 0) {
                // A one-item receipt has no allocation ambiguity: NetSales is that
                // item's own pre-tax price. Zero-value receipts (comps, promos) are
                // not a price, so they never overwrite a real one.
                $name = $names[0];
                $stamp = "{$date} 00:00:00";
                if ($products[$name]['priced_at'] === null || $stamp > $products[$name]['priced_at']) {
                    $products[$name]['price'] = round((float) $netSales, 2);
                    $products[$name]['priced_at'] = $stamp;
                }
            }
        }

        fclose($handle);

        return [
            'products' => $products,
            'outlets' => array_keys($outlets),
            'first_day' => $firstDay,
            'last_day' => $lastDay,
        ];
    }

    private function createProducts(array $stats): array
    {
        ksort($stats);
        $skus = $this->skus();
        $products = [];

        foreach ($stats as $name => $stat) {
            $products[$name] = Product::create([
                'sku' => $skus[$name] ?? null,
                'name' => $name,
                'category' => null,
                'unit' => 'pcs',
                'sell_price' => $stat['price'] ?? 0,
            ]);
        }

        return $products;
    }

    /**
     * ItemID -> product name from ItemMaster.csv, when the file exists. The export
     * itself has no product identifiers, so without the master file SKU stays empty.
     *
     * @return array<string, string>
     */
    private function skus(): array
    {
        $path = base_path(config('myventory.item_master_csv'));

        if (! is_file($path)) {
            return [];
        }

        $handle = $this->open($path, ['ItemID', 'ProductName']);
        $skus = [];

        while (($row = fgetcsv($handle)) !== false) {
            [$id, $name] = $row;
            $skus[trim($name)] = trim($id);
        }

        fclose($handle);

        return $skus;
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

    private function importReceipts(string $path, array $products, array $outlets): void
    {
        $handle = $this->open($path);
        $batch = [];

        while (($row = fgetcsv($handle)) !== false) {
            $batch[] = $row;
            if (count($batch) === self::CHUNK) {
                $this->insertBatch($batch, $products, $outlets);
                $batch = [];
            }
        }

        if ($batch !== []) {
            $this->insertBatch($batch, $products, $outlets);
        }

        fclose($handle);
    }

    private function insertBatch(array $rows, array $products, array $outlets): void
    {
        $transactions = [];
        $linesByReceipt = [];

        foreach ($rows as $row) {
            [$outletCode, $date, $time, $netSales, $tax, $total, $receipt, $items, $totalItem, $payment, $loyalty] = $row;
            $names = $this->names($items);

            $transactions[] = [
                'outlet_id' => $outlets[$outletCode]->id,
                'receipt_number' => $receipt,
                'occurred_at' => "{$date} {$time}",
                'business_date' => $date,
                'hour' => (int) substr($time, 0, 2),
                'payment_method' => $payment,
                'uses_loyalty_card' => (bool) (int) $loyalty,
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
    }

    private function open(string $path, ?array $expected = null)
    {
        $handle = fopen($path, 'r');
        if ($handle === false) {
            throw new RuntimeException("Tidak dapat membaca: {$path}");
        }

        $header = array_map(
            fn ($column) => trim(str_replace("\u{FEFF}", '', (string) $column)),
            fgetcsv($handle) ?: [],
        );

        $expected ??= self::HEADER;

        if ($header !== $expected) {
            fclose($handle);
            throw new RuntimeException(sprintf(
                'Header %s tidak sesuai. Diharapkan: %s.',
                basename($path),
                implode(',', $expected),
            ));
        }

        return $handle;
    }

    /**
     * @return array<int, string>
     */
    private function names(string $items): array
    {
        return array_values(array_filter(array_map('trim', explode(',', $items)), fn ($name) => $name !== ''));
    }
}
