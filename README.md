# MyVentory

Smart inventory for a café: a dashboard that tracks transactions and stock, plus
the machine-learning service that forecasts from the same transaction data.

```
ML/data/Transactions.csv  (53.820 struk, SHOP001-SHOP003)
        |
        +--> ML/train/*.py   -> ML/artifacts/<model>/<versi>/   (5 model)
        |
        +--> Web/            -> dashboard Laravel + Vue + PostgreSQL
        |
        +--> API/            -> REST FastAPI untuk kelima model (belum disambungkan)
```

| Folder | Isi | Status |
|---|---|---|
| `Web/` | Dashboard Laravel 13 + Vue 3 (Inertia), PostgreSQL | Selesai |
| `API/` | REST API FastAPI untuk lima model ML | Berjalan sendiri, belum dipanggil dashboard |
| `ML/` | Skrip pelatihan dan artefak model | Selesai |
| `Mobile/` | Aplikasi Flutter (data contoh) | Belum tersambung |
| `docker/` | Dockerfile web, skrip entrypoint, verifikasi | Selesai |

## Menjalankan dashboard

Butuh Docker dan Docker Compose.

```bash
cp .env.example .env
docker compose up -d --build

# buka http://localhost:8080
```

Yang terjadi saat pertama kali dijalankan: PostgreSQL dibuat, migrasi jalan,
lalu `ML/data/Transactions.csv` diimpor (53.820 transaksi, 94 produk, 3 outlet).
Proses impor sekitar 11 detik dan dilewati pada boot berikutnya.

Untuk database kosong, set `MYVENTORY_SEED=false` sebelum `up`.

### Perintah lain

```bash
docker compose down            # hentikan
docker compose down -v         # hentikan dan hapus data (impor ulang saat up)

# uji PHP (22 tes, memakai database myventory_test di postgres yang sama)
docker compose --profile test run --rm test

# API ML, tidak dipanggil dashboard
docker compose --profile api up -d
```

### Variabel lingkungan

Semua punya nilai default di `docker-compose.yml`, jadi `.env` opsional.

| Variabel | Default | Keterangan |
|---|---|---|
| `WEB_PORT` | `8080` | port dashboard |
| `DB_DATABASE` | `myventory` | nama database |
| `DB_USERNAME` / `DB_PASSWORD` | `myventory` | kredensial database |
| `DB_PORT_FORWARD` | `5432` | port postgres di host |
| `APP_KEY` | kosong | dibuat otomatis dan disimpan di volume `web-storage` |
| `MYVENTORY_SEED` | `true` | impor CSV saat boot pertama |

## Dashboard

Empat halaman, semuanya membaca database yang sama:

- **Overview**: KPI periode (penjualan bersih, transaksi, rata-rata per struk,
  item terjual) dengan pembanding periode sebelumnya; tren penjualan harian
  beserta rata-rata bergerak 7 hari; jam tersibuk; pola hari; metode pembayaran;
  produk terlaris; transaksi terakhir; stok yang perlu perhatian.
- **Transactions**: daftar struk dengan pencarian nomor struk, filter outlet,
  pembayaran, dan rentang tanggal. Form "Catat penjualan" menambah struk manual
  dan mengurangi stok.
- **Stock**: saldo per outlet x produk, status aman/menipis/habis, pergerakan
  stok masuk, keluar, dan penyesuaian stok opname, serta batas minimum per baris.
- **Products**: katalog produk yang dipakai form penjualan dan stok.

Angka di dashboard selalu hasil hitungan dari tabel, tidak ada nilai contoh.
Detail arah visual ada di `Web/DESIGN.md`.

## Asal angka stok

Ekspor kasir tidak memuat jumlah stok, jadi saldo disusun ulang secara aritmetika:
satu pergerakan `in` sebesar rata-rata penjualan 14 hari dikali 14, lalu pergerakan
`sale` untuk penjualan minggu terakhir. Saldo pada tabel `stocks` adalah hasil
jumlah seluruh `stock_movements`, dan dihitung ulang setiap ada pergerakan baru.

Tanggal ekspor digeser maju dalam kelipatan minggu supaya data berakhir kemarin
(ekspor aslinya berakhir September 2025). Pola hari dalam minggu tetap utuh, dan
rentang asli dicetak pada log impor.

## Pengujian

```bash
docker compose --profile test run --rm test          # 22 tes PHP
cd API && python3 -m pytest                          # 67 tes API
cd Mobile && flutter test                            # 1 tes Flutter

# klik-tembus dashboard dengan browser sungguhan (butuh playwright)
python3 docker/verify/click_through.py http://localhost:8080
```

`docker/verify/click_through.py` menelusuri setiap kontrol (filter periode,
filter outlet, pencarian, form penjualan, form stok, form produk, tombol tema),
mencatat error konsol, dan menyimpan tangkapan layar desktop serta mobile ke
`docker/verify/shots/`.
