# MyVentory Web

Dashboard Laravel 13 + Vue 3 (Inertia) untuk melacak transaksi dan stok.
Database PostgreSQL. Arah visual ada di `DESIGN.md`.

## Menjalankan

Cara yang dipakai sehari-hari adalah Docker Compose dari root repository:

```bash
cp .env.example .env
docker compose up -d --build     # http://localhost:8080
```

Untuk pengembangan dengan hot reload, jalankan PHP dan Vite terpisah. Butuh
ekstensi PHP `pdo_pgsql`:

```bash
composer install
npm install
php artisan migrate --seed       # impor ML/data/Transactions.csv
composer run dev                 # server + vite + queue + log
```

Tanpa `pdo_pgsql`, `php artisan migrate` gagal dengan "could not find driver".
Pakai container untuk pekerjaan database, atau pasang ekstensinya.

## Struktur

```
app/
├── Http/Controllers/
│   ├── DashboardController.php   # ringkasan periode
│   ├── TransactionController.php # daftar struk + form penjualan
│   ├── StockController.php       # saldo, pergerakan, batas minimum
│   └── ProductController.php     # katalog produk
├── Models/                       # Outlet, Product, Stock, StockMovement,
│                                 # Transaction, TransactionItem
└── Services/
    ├── DashboardStats.php        # seluruh agregasi dashboard
    ├── SalesRecorder.php         # satu penjualan = struk + item + stok
    └── StockLedger.php           # satu-satunya tempat saldo stok berubah
database/
├── migrations/                   # outlets, products, stocks, transactions,
│                                 # transaction_items, stock_movements
└── seeders/TransactionImportSeeder.php
resources/
├── css/app.css                   # token warna, komponen dasar
└── js/
    ├── Pages/                    # Dashboard, Transactions, Stock, Products
    ├── Components/               # Panel, StatStrip, chart, Modal, Pagination
    └── Layouts/AppLayout.vue     # navigasi, tema, toast
```

Aturan yang menjaga kode tetap kecil:

- Setiap penulisan stok lewat `StockLedger`, jadi saldo dan riwayat pergerakan
  tidak bisa berbeda.
- Setiap agregasi dashboard ada di `DashboardStats`, bukan di controller atau
  di Vue. Controller hanya memilih data dan mengirim props.
- Halaman Vue tidak menghitung angka bisnis; format tampilan ada di
  `resources/js/format.js`.
- Chart digambar sebagai SVG langsung (tiga bentuk saja), tanpa pustaka chart.

## Pengujian

```bash
docker compose --profile test run --rm test     # dari root repository
./vendor/bin/pint --test                        # gaya kode PHP
npm run build                                   # build aset
```
