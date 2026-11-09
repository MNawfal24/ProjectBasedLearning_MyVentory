# Web — backend Laravel dan dashboard admin

Folder ini adalah inti sistem. Ia menyimpan data, menjaga aturan akses, dan
menyajikan dashboard. Aplikasi mobile juga memakai backend yang sama, hanya lewat
jalur `/api/v1`.

Stack: Laravel 13, PHP 8.4, Inertia.js, Vue 3, shadcn-vue, ECharts, PostgreSQL 16.

## Dua jalur dalam satu aplikasi

| Jalur | Untuk | Autentikasi | Hasil |
|---|---|---|---|
| `/` dan rute Inertia | Browser admin | Session cookie | Halaman Vue dirender lewat Inertia |
| `/api/v1/*` | Aplikasi mobile | Sanctum bearer token | JSON |

Keduanya memakai model dan service yang sama, jadi perhitungan stok tidak
diduplikasi.

## Halaman dashboard

| Rute | Isi |
|---|---|
| `/login`, `/logout` | Masuk dan keluar. Hanya akun `admin` yang diterima. |
| `/dashboard` | KPI periode dengan pembanding periode sebelumnya, tren harian, jam tersibuk, pola hari, metode pembayaran, produk terlaris, transaksi terakhir, stok menipis |
| `/transactions` | Daftar struk dengan pencarian, filter outlet/pembayaran/tanggal, dan form catat penjualan |
| `/stock` | Grafik batang mendatar komposisi status per outlet (aman/menipis/habis), tabel saldo per outlet x produk dengan filter outlet dan status di judul kolom, pergerakan stok, dan form ubah batas minimum |
| `/products` | Katalog produk yang dipakai form penjualan |
| `/users` | Akun staf mobile: buat akun dan reset kata sandi |

Semua rute di atas berada dalam grup `auth` + `role:admin`. Staf yang mencoba
membukanya mendapat `403`.

## API `/api/v1`

Endpoint baca memakai middleware `abilities:read`. Endpoint tulis menambah
`abilities:write` dan `role:admin`. Token staf hanya membawa `read`, sehingga
percobaan menulis dijawab `403` walaupun tombolnya ada di klien.

| Method | Endpoint | Izin |
|---|---|---|
| GET | `/health` | publik |
| POST | `/auth/login` | publik, throttle 10/menit |
| GET | `/auth/me`, POST `/auth/logout` | login |
| GET | `/outlets`, `/outlets/{id}` | read |
| GET | `/products`, `/products/{id}` | read |
| GET | `/stocks`, `/stocks/{id}` | read |
| GET | `/transactions`, `/transactions/{id}` | read |
| GET | `/dashboard/summary` | read |
| GET | `/predictions/sales-forecast` | read |
| GET | `/predictions/demand-forecast` | read |
| GET | `/predictions/stock` | read |
| POST/PATCH/DELETE | `/products`, `/products/{id}` | write + admin |
| POST | `/stocks/movements`, `/stocks/rebuild` | write + admin |
| PATCH | `/stocks/{id}` (batas minimum) | write + admin |
| POST/DELETE | `/transactions`, `/transactions/{id}` | write + admin |

Login menerima `client: mobile`. Bila `client` bernilai `mobile` dan akunnya admin,
server menolak dengan `403` karena dashboard web adalah satu-satunya pintu admin.
Tanpa `client`, keduanya boleh masuk dan izin mengikuti peran akun.

## Struktur kode

```
Web/
├── app/
│   ├── Http/
│   │   ├── Controllers/            dashboard: Dashboard, Transaction, Stock, Product
│   │   ├── Controllers/Api/        Auth, Dashboard, Outlet, Product, Stock, Transaction, Prediction
│   │   ├── Controllers/Web/        Auth, Landing, User
│   │   ├── Middleware/             EnsureRole, HandleInertiaRequests
│   │   ├── Requests/Api/           validasi body API
│   │   └── Resources/Api/          bentuk JSON
│   ├── Models/                     User, Outlet, Product, Stock, StockMovement, Transaction, TransactionItem
│   └── Services/                   DashboardStats, SalesRecorder, StockLedger, MlClient
├── routes/
│   ├── web.php                     rute Inertia
│   └── api.php                     rute JSON
├── resources/js/
│   ├── Pages/                      Dashboard, Transactions, Stock, Products, Users, Auth/Login
│   ├── Layouts/AppLayout.vue       navigasi, tema, tombol keluar
│   └── Components/                 komponen UI dan grafik
├── database/
│   ├── migrations/                 skema, termasuk users.role
│   └── seeders/                    impor transaksi, impor stok, akun admin
└── tests/Feature/                  tes rute, stok, transaksi, peran, API
```

## Service yang menentukan angka

- **StockLedger** satu-satunya tempat saldo stok berubah saat aplikasi melayani
  pengguna. Setiap perubahan menambah satu `stock_movement`, lalu saldo pada tabel
  `stocks` dihitung ulang dari jumlah seluruh pergerakan, sehingga keduanya tidak
  bisa berbeda. Satu-satunya pengecualian adalah `StockImportSeeder`, yang menulis
  pergerakan hasil impor secara massal lalu memverifikasi saldo setiap seri harus
  sama dengan `ClosingStock` hari terakhir.
- **SalesRecorder** mencatat penjualan: header struk, baris item, dan pergerakan
  stok keluar. Pajak 11% mengikuti rasio struk hasil impor.
- **DashboardStats** menghitung seluruh KPI dari tabel, tanpa angka contoh.
  Agregasi dilakukan di PHP agar hasilnya sama di PostgreSQL (produksi) dan
  SQLite saat pengujian.
- **MlClient** satu-satunya pemanggil FastAPI, melalui `ML_API_URL`. Bila layanan
  ML mati, endpoint prediksi menjawab `503` tanpa mengganggu endpoint lain.

## Tabel utama

| Tabel | Isi |
|---|---|
| `users` | Akun dengan `role` (`admin` atau `user`) |
| `outlets` | Tiga outlet kafe |
| `products` | Katalog, soft delete lewat `deleted_at` |
| `stocks` | Saldo dan batas minimum per outlet x produk |
| `stock_movements` | Riwayat `in`, `out`, `sale`, `adjustment` |
| `transactions` | Header struk |
| `transaction_items` | Baris produk pada struk |
| `personal_access_tokens` | Token Sanctum milik aplikasi mobile |

## Sumber data

Tidak ada angka contoh dan tidak ada turunan yang dikarang. Dua berkas mengisi
database, dan keduanya diimpor apa adanya.

| Seeder | Berkas | Yang ditulis |
|---|---|---|
| `TransactionImportSeeder` | `Transactions.csv` | outlet, produk, struk, baris item |
| `StockImportSeeder` | `Stock.csv` + `ItemMaster.csv` | `stock_movements`, saldo `stocks` |

- Tanggal, jam, nomor struk, metode bayar, `NetSales`, `Tax`, `TotalAmount` dan
  `TotalItem` disalin langsung. Tanggal tidak digeser.
- `sell_price` hanya diisi bila ada struk berisi satu item: di situ `NetSales`
  adalah harga item itu sendiri. Produk tanpa struk satu item dibiarkan `0` dan
  diisi lewat menu Produk.
- `category` tidak ada di sumber, jadi `null`. `sku` diambil dari `ItemMaster.csv`.
- `StockImportSeeder` menolak impor bila `OpeningStock + StockIn - StockOut`
  tidak sama dengan `ClosingStock`, bila `OpeningStock` sebuah hari tidak sama
  dengan `ClosingStock` hari sebelumnya, bila ada tanggal ganda, atau bila
  `ItemID`/nama produk tidak dikenal. Lebih baik gagal daripada menyimpan saldo
  yang saling bertentangan.
- `MinimumStock` hanya punya satu kolom di skema, jadi nilai hari terakhir setiap
  seri yang disimpan.
- Saldo stok adalah keadaan pada tanggal pergerakan terakhir, bukan hitungan hari
  ini. Halaman Stok dan panel "Unit di gudang" menampilkan tanggal itu.

## Konfigurasi

| Variabel | Default | Keterangan |
|---|---|---|
| `APP_URL` | `http://localhost:8080` | alamat publik; ubah saat memakai ngrok |
| `DB_*` | `myventory` | koneksi PostgreSQL |
| `SESSION_DRIVER` | `database` | sesi dashboard |
| `MYVENTORY_SEED` | `true` | impor CSV saat boot pertama |
| `MYVENTORY_SEED_CSV` | `database/data/Transactions.csv` | sumber impor transaksi |
| `MYVENTORY_STOCK_CSV` | `database/data/Stock.csv` | sumber impor stok |
| `MYVENTORY_ITEM_MASTER_CSV` | `database/data/ItemMaster.csv` | peta ItemID ke produk |
| `MYVENTORY_ADMIN_EMAIL` | `admin@myventory.com` | akun admin seeder |
| `MYVENTORY_ADMIN_PASSWORD` | `admin123` | kata sandi awal admin |
| `ML_API_URL` | `http://api:8000/api/v1` | alamat FastAPI |
| `ML_TIMEOUT` | `10` | detik sebelum prediksi dianggap gagal |

`bootstrap/app.php` mengaktifkan `trustProxies(at: '*')` supaya skema HTTPS dari
ngrok diteruskan dengan benar.

## Pengujian

```bash
docker compose --profile test run --rm test
```

Tes berjalan pada database `myventory_test` di PostgreSQL yang sama. Cakupannya:
hak akses peran, API baca/tulis, alur stok, transaksi manual, dan dashboard.
