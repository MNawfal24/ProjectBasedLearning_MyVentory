# Mobile — aplikasi Flutter untuk staf

Aplikasi ini untuk staf kafe: masuk, lihat stok dan produk, lihat ringkasan
penjualan, dan lihat prediksi permintaan. Isinya **tampilan saja**. Semua perubahan
data dilakukan dari dashboard web.

Stack: Flutter 3, Dart 3, Dio untuk HTTP, flutter_secure_storage untuk menyimpan
token, google_fonts untuk tipografi.

## Cara kerja

1. `main.dart` menginisialisasi `InjectionContainer` lalu membaca token tersimpan
   melalui `authController.initialize()`.
2. `AuthGate` di `app.dart` memilih halaman: landing/login bila belum masuk,
   `AppShell` bila sudah.
3. Setiap permintaan HTTP lewat `ApiClient`, yang menempelkan header
   `Authorization: Bearer <token>` dari secure storage.
4. Respons `401` menghapus token dan mengembalikan pengguna ke halaman login.

Login mengirim `client: mobile`. Server menolak akun admin dari jalur ini, jadi
staf memakai akun yang dibuat admin dari menu **Akun**.

## Halaman

| Halaman | Berkas | Isi |
|---|---|---|
| Landing | `pages/auth/landing_page.dart` | Pengantar dan tombol masuk |
| Login | `pages/auth/login_page.dart` | Email dan kata sandi staf |
| Dashboard | `pages/dashboard/dashboard_page.dart` | Penjualan, jumlah produk, stok menipis, total unit |
| Products | `pages/products/products_page.dart` | Daftar produk dengan pencarian dan filter |
| Detail produk | `features/product/presentation/pages/product_detail_page.dart` | Saldo, batas minimum, harga |
| Prediction | `pages/predictions/prediction_page.dart` | Prediksi permintaan per produk dan grafik 7 hari |
| Stock-out | `pages/predictions/stockout_page.dart` | Perbandingan stok dengan prediksi dan saran restock |
| Profile | `pages/profile/profile_page.dart` | Akun yang sedang masuk dan tombol keluar |

Registrasi mandiri sudah dihapus. Halaman `register_page.dart` tidak ada lagi.

## Struktur kode

```
Mobile/lib/
├── main.dart                  titik masuk
├── app.dart                   AuthGate dan AppShell (bottom navigation)
├── injection_container.dart   perakitan dependensi
├── core/
│   ├── config/api_config.dart base URL
│   ├── network/api_client.dart Dio + token + penanganan 401
│   ├── storage/token_storage.dart
│   ├── controllers/auth_controller.dart
│   ├── models/api_exception.dart
│   └── app_state.dart         instance authController global
├── features/
│   ├── auth/                  datasource, repository
│   ├── product/               entity, repository, usecase, halaman
│   └── prediction/            datasource proxy ML, usecase
├── pages/                     dashboard, products, predictions, profile, auth
├── widgets/                   tema, kartu, navigasi bawah
└── data/mock_data.dart        InventoryStore (nama lama, isinya API)
```

`data/mock_data.dart` menyimpan nama berkas yang menyesatkan: `InventoryStore` di
dalamnya tidak lagi berisi data contoh, melainkan memuat produk, ringkasan
dashboard, outlet, dan prediksi dari API.

## Data yang ditampilkan

| Kebutuhan | Endpoint |
|---|---|
| Profil | `GET /api/v1/auth/me` |
| Daftar outlet | `GET /api/v1/outlets` |
| Produk + stok + batas minimum | `GET /api/v1/products` |
| Detail produk | `GET /api/v1/products/{id}` |
| Stok menipis | `GET /api/v1/products` lalu disaring di klien |
| Ringkasan dashboard | `GET /api/v1/dashboard/summary` |
| Prediksi permintaan | `GET /api/v1/predictions/demand-forecast` |
| Prediksi stok | `GET /api/v1/predictions/stock` |

Prediksi diambil sekali per produk saat halaman prediksi dibuka, lalu disimpan di
`InventoryStore`. Bila layanan ML belum siap, nilai prediksi menjadi `0` dan
halaman lain tetap berjalan.

## Base URL

Default `http://10.0.2.2:8080/api/v1`, yaitu alamat host dari dalam emulator
Android pada port Laravel. Ubah saat build:

```bash
# emulator
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080/api/v1

# perangkat fisik, IP LAN komputer
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8080/api/v1

# demo lewat internet
flutter run --dart-define=API_BASE_URL=https://<domain>.ngrok-free.app/api/v1
```

Port `8000` adalah FastAPI dan tidak dipakai aplikasi ini. Android manifest sudah
memuat `usesCleartextTraffic="true"`, jadi HTTP lokal diizinkan. Header
`ngrok-skip-browser-warning` dipasang agar halaman peringatan ngrok tidak muncul.

## Pengujian

```bash
cd Mobile && flutter test
```

- `test/widget_test.dart` memeriksa alur login sampai logout.
- `test/prediction_page_test.dart` memakai `InventoryStore` tiruan untuk menguji
  kondisi memuat, kosong, dan berisi.
