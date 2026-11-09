# MyVentory

MyVentory adalah sistem inventori pintar untuk kafe/UMKM. Ia menyatukan tiga hal
yang biasanya terpisah: catatan penjualan kasir, saldo stok per outlet, dan
prediksi permintaan dari model machine learning.

Masalah yang dijawab: pemilik kafe tahu berapa yang terjual kemarin, tapi tidak
tahu berapa yang harus dipesan besok. MyVentory mengambil data transaksi, menyusun
saldo stok dari data itu, lalu memakai model ML untuk memperkirakan permintaan,
jam sibuk, dan risiko kehabisan stok.

Data contoh di repo ini berasal dari ekspor kasir 53.820 struk untuk tiga outlet
(SHOP001–SHOP003) dan 94 produk.

## Ada dua aplikasi, satu backend

| Aplikasi | Untuk siapa | Bisa apa |
|---|---|---|
| Dashboard web | Admin / pemilik | Melihat seluruh angka, mencatat penjualan, mengatur stok dan batas minimum, mengelola produk dan akun |
| Aplikasi mobile | Staf | Masuk, melihat stok, produk, ringkasan penjualan, dan prediksi permintaan |

Keduanya tidak saling memanggil. Keduanya bicara ke satu backend Laravel yang
memakai satu database PostgreSQL, sehingga angka di ponsel dan di browser selalu
berasal dari baris yang sama.

```
Flutter (staf, baca saja)  ──Bearer token──┐
                                           ├──> Laravel /api/v1 ──> PostgreSQL
Dashboard web (admin)      ──session───────┘              │
                                                          └──> FastAPI ML
                                                               (internal)
```

## Lima folder

| Folder | Isi | Baca |
|---|---|---|
| `Web/` | Backend Laravel + dashboard Vue. Sumber kebenaran data dan aturan akses. | [web.md](web.md) |
| `API/` | Layanan FastAPI untuk lima model ML. Tanpa database, tanpa autentikasi, hanya dipanggil Laravel. | [api.md](api.md) |
| `ML/` | Data transaksi, notebook, dan skrip pembentukan dataset. | [ml.md](ml.md) |
| `Mobile/` | Aplikasi Flutter untuk staf. Tampilan saja. | [mobile.md](mobile.md) |
| `docker/` | Dockerfile, entrypoint, konfigurasi Apache, dan skrip verifikasi klik-tembus. | [docker.md](docker.md) |

## Menjalankan

Butuh Docker dan Docker Compose.

```bash
cp .env.example .env
docker compose up -d --build
```

Buka `http://localhost:8080`. Saat pertama kali jalan, PostgreSQL dibuat, migrasi
dijalankan, lalu `ML/data/Transactions.csv` diimpor (sekitar 11 detik). Impor
dilewati pada boot berikutnya.

Masuk sebagai admin dengan `admin@myventory.com` / `admin123`, lalu buat akun staf
dari menu **Akun** untuk dipakai di aplikasi mobile.

Untuk menjalankan aplikasi mobile:

```bash
cd Mobile
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080/api/v1
```

`10.0.2.2` adalah alamat host dari dalam emulator Android. Perangkat fisik memakai
IP LAN komputer, misalnya `http://192.168.1.10:8080/api/v1`.

## Pembagian hak akses

Aturan ini dijaga di server, bukan hanya disembunyikan di tampilan.

| | Admin (web) | Staf (mobile) |
|---|---|---|
| Baca dashboard, produk, stok, transaksi | ya | ya |
| Catat penjualan, ubah stok, ubah batas minimum | ya | tidak |
| Tambah/ubah/hapus produk | ya | tidak |
| Buat akun dan reset kata sandi | ya | tidak |
| Prediksi ML | ya | ya |

Registrasi publik sudah tidak ada. Akun staf hanya dibuat admin, dan token mobile
hanya membawa izin baca sehingga permintaan tulis dijawab `403`.

## Perintah lain

```bash
docker compose down                # hentikan
docker compose down -v             # hentikan dan hapus data

docker compose --profile test run --rm test              # tes PHP
docker compose --profile api up -d                       # layanan ML
```

## Status yang perlu diketahui

- `ML/artifacts/` tidak ada di repo. Tanpa artefak, lima model ML berstatus
  `unavailable` dan endpoint prediksi menjawab `503`. Fitur lain tetap berjalan.
- `Web/resources/js/Pages/Auth/Register.vue` dan `Pages/Landing/Index.vue` masih
  tersimpan tetapi tidak lagi punya route.
- `ML/README.md` masih kosong.

Detail tiap bagian ada di dokumen folder masing-masing.
