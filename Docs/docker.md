# docker — cara seluruh sistem dijalankan

Folder ini berisi semua yang dibutuhkan untuk menyalakan MyVentory dengan Docker
Compose, plus skrip verifikasi antarmuka.

## Empat service

Didefinisikan di `docker-compose.yml` di root repo.

| Service | Image | Port | Kapan jalan |
|---|---|---|---|
| `db` | `postgres:16-alpine` | 5432 | selalu |
| `web` | `docker/web/Dockerfile` (target `runtime`) | 8080 | selalu |
| `api` | `API/Dockerfile` | hanya internal | profil `api` |
| `test` | `docker/web/Dockerfile` (target `testing`) | - | profil `test`, sekali jalan |

`db` punya healthcheck dan `start_period` 30 detik karena pemulihan setelah crash
pada volume besar bisa memakan beberapa detik. `web` menunggu `db` sehat sebelum
start, jadi tidak ada migrasi yang gagal karena database belum siap.

## Isi folder

```
docker/
├── db/init-test-database.sql   membuat database myventory_test sekali, saat volume kosong
├── web/
│   ├── Dockerfile              tiga stage: assets, runtime, testing
│   ├── entrypoint.sh           tunggu DB, migrasi, seed, cache config/route
│   └── apache.conf            document root ke public/, rewrite aktif
└── verify/
    └── click_through.py        uji klik-tembus dashboard dengan Playwright
```

## Alur start container web

`docker/web/entrypoint.sh` menjalankan urutan berikut:

1. Membuat ulang struktur `storage/` karena volume bernama mulai kosong.
2. Menyiapkan `APP_KEY`. Bila tidak diberikan lewat environment, kunci dibuat
   sekali dan disimpan di `storage/app/app.key`, sehingga restart tidak membatalkan
   sesi dan cookie.
3. Menunggu PostgreSQL menerima koneksi.
4. `php artisan migrate --force`.
5. `php artisan db:seed --force` bila `MYVENTORY_SEED=true`.
6. `config:cache` dan `route:cache`, lalu menyerahkan proses ke Apache.

Seeder mengimpor `ML/data/Transactions.csv` bila tabel transaksi masih kosong,
jadi boot kedua tidak mengimpor ulang.

## Stage Dockerfile web

| Stage | Isi | Dipakai |
|---|---|---|
| `assets` | Node 22, `npm ci`, `npm run build` | hasilnya disalin ke stage lain |
| `base` | PHP 8.4 + Apache, ekstensi `pdo_pgsql`, `opcache` | dasar dua stage berikut |
| `runtime` | `composer install --no-dev`, kode aplikasi, aset hasil build | service `web` |
| `testing` | sama tetapi dengan dependensi dev | service `test` |

Stage `assets` dipisah agar mengubah kode PHP tidak membangun ulang aset Vue.
Karena Docker memilih stage terakhir bila `target` tidak disebut, compose menulis
`target: runtime` secara eksplisit.

## Volume dan jaringan

| Nama | Isi |
|---|---|
| `db-data` | data PostgreSQL; `down -v` menghapusnya |
| `web-storage` | `storage/` Laravel, termasuk `app.key` |

`api` hanya dapat dijangkau `web` lewat nama layanan `api:8000` di jaringan
internal Compose. Port tidak dipublikasikan supaya layanan tanpa autentikasi itu
tidak terbuka dari luar. Pada `docker-compose.yml` saat ini `api` masih memakai
`ports`, jadi bila tidak sedang dipakai untuk debugging sebaiknya dihapus atau
diganti `expose`.

## Konfigurasi

Semua variabel punya nilai default di compose, jadi `.env` opsional.

| Variabel | Default | Keterangan |
|---|---|---|
| `WEB_PORT` | `8080` | port dashboard di host |
| `API_PORT` | `8000` | port FastAPI di host |
| `DB_DATABASE` | `myventory` | nama database |
| `DB_USERNAME`, `DB_PASSWORD` | `myventory` | kredensial |
| `DB_PORT_FORWARD` | `5432` | port PostgreSQL di host |
| `APP_URL` | `http://localhost:8080` | ubah saat memakai ngrok |
| `APP_KEY` | kosong | dibuat otomatis bila kosong |
| `MYVENTORY_SEED` | `true` | impor CSV saat boot pertama |

`web` menerima `ML_API_URL` dan `ML_TIMEOUT` untuk memanggil FastAPI.

## Perintah

```bash
docker compose up -d --build          # nyalakan semua
docker compose down                   # hentikan
docker compose down -v                # hentikan dan hapus data

docker compose --profile test run --rm test     # tes PHP
docker compose --profile api up -d              # nyalakan layanan ML
```

## Verifikasi antarmuka

`docker/verify/click_through.py` membuka dashboard dengan browser sungguhan,
menelusuri filter periode, filter outlet, pencarian, form penjualan, form stok,
form produk, dan tombol tema, lalu mencatat error konsol serta menyimpan tangkapan
layar ke `docker/verify/shots/`.

```bash
python3 docker/verify/click_through.py http://localhost:8080
```

Skrip ini butuh Playwright di host, bukan di dalam image.
