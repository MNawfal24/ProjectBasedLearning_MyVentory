<?php

namespace Database\Seeders;

use App\Models\Outlet;
use App\Models\Product;
use App\Models\Stock;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use RuntimeException;

/**
 * Imports the real stock ledger (ML/data/Stock.csv) into stock_movements and its
 * closing balance into stocks. Nothing is simulated: every number comes from a
 * row of the file.
 *
 * Row contract: Date, Outlet, ItemID, OpeningStock, StockIn, StockOut,
 * ClosingStock, MinimumStock. The import refuses to run when the file breaks any
 * of these rules, instead of storing numbers that contradict each other:
 * - one row per outlet x item x date, dates strictly increasing;
 * - OpeningStock of a day equals ClosingStock of the previous day;
 * - OpeningStock + StockIn - StockOut equals ClosingStock;
 * - no negative quantity;
 * - every ItemID exists in ItemMaster.csv, every mapped product exists in
 *   products, every outlet exists in outlets.
 *
 * Movements written: OpeningStock of the first day as one `in`, every StockIn as
 * an `in`, every StockOut as an `out`. MinimumStock has a single column in the
 * schema, so the last day of each series wins.
 *
 * The file is indexed by series line numbers instead of being parsed into one big
 * array, so memory stays flat as the ledger grows.
 */
class StockImportSeeder extends Seeder
{
    private const CHUNK = 1000;

    private const HEADER = [
        'Date', 'Outlet', 'ItemID', 'OpeningStock', 'StockIn', 'StockOut', 'ClosingStock', 'MinimumStock',
    ];

    /** @var array<int, string> data lines of Stock.csv, header removed */
    private array $raw = [];

    public function run(): void
    {
        $path = base_path(config('myventory.stock_csv'));

        if (! is_file($path)) {
            $this->command?->warn("Stock.csv tidak ditemukan di {$path}, stok tidak diimpor.");

            return;
        }

        if (Stock::query()->exists()) {
            $this->command?->warn('Stok sudah ada, import stok dilewati.');

            return;
        }

        $master = $this->master();
        $lines = $this->lines($path);
        $outlets = Outlet::query()->get()->keyBy('code');
        $products = Product::query()->get()->keyBy('name');

        $movements = 0;
        $rows = 0;

        DB::transaction(function () use ($lines, $master, $outlets, $products, &$movements, &$rows) {
            foreach ($lines as $key => $numbers) {
                [$outletCode, $itemId] = explode('|', $key, 2);

                $outlet = $outlets->get($outletCode);
                if (! $outlet) {
                    throw new RuntimeException("Outlet '{$outletCode}' tidak ada. Jalankan import transaksi lebih dulu.");
                }

                $name = $master[$itemId] ?? null;
                if ($name === null) {
                    throw new RuntimeException("ItemID '{$itemId}' tidak ada di ItemMaster.csv.");
                }

                $product = $products->get($name);
                if (! $product) {
                    throw new RuntimeException("Produk '{$name}' ({$itemId}) tidak ada. Jalankan import transaksi lebih dulu.");
                }

                $points = $this->points($key, $numbers);
                $rows += count($points);
                $movements += $this->writeSeries($outlet->id, $product->id, $key, $points);
            }
        });

        $this->command?->info(sprintf(
            'Import stok selesai: %d baris, %d seri, %d pergerakan.',
            $rows,
            count($lines),
            $movements,
        ));
    }

    /**
     * @param  array<int, array{0: string, 1: float, 2: float, 3: float, 4: float, 5: float}>  $points
     */
    private function writeSeries(int $outletId, int $productId, string $key, array $points): int
    {
        $this->assertSeries($key, $points);

        $movements = [];
        $first = $points[0];

        if ($first[1] > 0) {
            $movements[] = $this->movement($outletId, $productId, 'in', $first[1], $first[0], 'opening');
        }

        foreach ($points as [$date, , $in, $out]) {
            if ($in > 0) {
                $movements[] = $this->movement($outletId, $productId, 'in', $in, $date, 'stock-in');
            }
            if ($out > 0) {
                $movements[] = $this->movement($outletId, $productId, 'out', -$out, $date, 'stock-out');
            }
        }

        foreach (array_chunk($movements, self::CHUNK) as $chunk) {
            DB::table('stock_movements')->insert($chunk);
        }

        $last = $points[array_key_last($points)];
        $balance = (float) DB::table('stock_movements')
            ->where('outlet_id', $outletId)
            ->where('product_id', $productId)
            ->sum('quantity');

        if (abs($balance - $last[4]) > 0.01) {
            throw new RuntimeException(sprintf(
                'Saldo %s tidak cocok: pergerakan %.2f, ClosingStock %.2f.',
                $key,
                $balance,
                $last[4],
            ));
        }

        Stock::create([
            'outlet_id' => $outletId,
            'product_id' => $productId,
            'quantity' => $last[4],
            'min_quantity' => $last[5],
        ]);

        return count($movements);
    }

    /**
     * @param  array<int, array{0: string, 1: float, 2: float, 3: float, 4: float, 5: float}>  $points
     */
    private function assertSeries(string $key, array $points): void
    {
        $previous = null;

        foreach ($points as [$date, $opening, $in, $out, $closing, $minimum]) {
            $label = "{$key} @ {$date}";

            if ($opening < 0 || $in < 0 || $out < 0 || $closing < 0) {
                throw new RuntimeException("Nilai negatif pada {$label}.");
            }

            if ($minimum < 0) {
                throw new RuntimeException("MinimumStock negatif pada {$label}.");
            }

            if (abs($opening + $in - $out - $closing) > 0.01) {
                throw new RuntimeException(sprintf(
                    'OpeningStock + StockIn - StockOut != ClosingStock pada %s (%.2f + %.2f - %.2f != %.2f).',
                    $label,
                    $opening,
                    $in,
                    $out,
                    $closing,
                ));
            }

            if ($previous !== null) {
                if ($date === $previous[0]) {
                    throw new RuntimeException("Tanggal ganda pada {$label}.");
                }
                if (abs($opening - $previous[4]) > 0.01) {
                    throw new RuntimeException(sprintf(
                        'OpeningStock %s (%.2f) tidak sama dengan ClosingStock hari sebelumnya (%.2f).',
                        $label,
                        $opening,
                        $previous[4],
                    ));
                }
            }

            $previous = [$date, $opening, $in, $out, $closing, $minimum];
        }
    }

    /**
     * Reads the file once and groups line numbers by "Outlot|ItemID", so the rows
     * can be parsed one series at a time.
     *
     * @return array<string, array<int, int>>
     */
    private function lines(string $path): array
    {
        $raw = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if ($raw === false) {
            throw new RuntimeException("Tidak dapat membaca: {$path}");
        }

        $header = array_map(
            fn ($column) => trim(str_replace("\u{FEFF}", '', $column)),
            str_getcsv((string) array_shift($raw)),
        );

        if ($header !== self::HEADER) {
            throw new RuntimeException(sprintf(
                'Header %s tidak sesuai. Diharapkan: %s.',
                basename($path),
                implode(',', self::HEADER),
            ));
        }

        $this->raw = $raw;
        $lines = [];

        foreach ($raw as $number => $line) {
            $row = str_getcsv($line);
            if (count($row) < 8) {
                throw new RuntimeException(sprintf('Baris %d tidak memuat 8 kolom.', $number + 2));
            }
            $lines["{$row[1]}|{$row[2]}"][] = $number;
        }

        return $lines;
    }

    /**
     * @param  array<int, int>  $numbers
     * @return array<int, array{0: string, 1: float, 2: float, 3: float, 4: float, 5: float}>
     */
    private function points(string $key, array $numbers): array
    {
        $points = [];

        foreach ($numbers as $number) {
            $row = str_getcsv($this->raw[$number]);
            $date = trim($row[0]);

            if (! preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) {
                throw new RuntimeException("Tanggal '{$date}' pada {$key} bukan format YYYY-MM-DD.");
            }

            $points[] = [
                $date,
                (float) $row[3],
                (float) $row[4],
                (float) $row[5],
                (float) $row[6],
                (float) $row[7],
            ];
        }

        usort($points, fn (array $a, array $b) => strcmp($a[0], $b[0]));

        return $points;
    }

    /**
     * @return array<string, string> ItemID => product name
     */
    private function master(): array
    {
        $path = base_path(config('myventory.item_master_csv'));

        if (! is_file($path)) {
            throw new RuntimeException("ItemMaster.csv tidak ditemukan di {$path}, stok tidak dapat dipetakan ke produk.");
        }

        $raw = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if ($raw === false) {
            throw new RuntimeException("Tidak dapat membaca: {$path}");
        }

        $header = array_map(
            fn ($column) => trim(str_replace("\u{FEFF}", '', $column)),
            str_getcsv((string) array_shift($raw)),
        );

        if ($header !== ['ItemID', 'ProductName']) {
            throw new RuntimeException(sprintf(
                'Header %s tidak sesuai. Diharapkan: ItemID,ProductName.',
                basename($path),
            ));
        }

        $master = [];
        foreach ($raw as $line) {
            $row = str_getcsv($line);
            $master[trim($row[0])] = trim($row[1]);
        }

        return $master;
    }

    private function movement(int $outletId, int $productId, string $type, float $quantity, string $date, string $reference): array
    {
        return [
            'outlet_id' => $outletId,
            'product_id' => $productId,
            'type' => $type,
            'quantity' => $quantity,
            'reference' => $reference,
            'note' => null,
            'occurred_at' => "{$date} 00:00:00",
            'created_at' => now(),
            'updated_at' => now(),
        ];
    }
}
