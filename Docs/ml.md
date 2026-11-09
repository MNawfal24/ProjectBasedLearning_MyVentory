# ML — data, notebook, dan skrip dataset

Folder ini menyimpan bahan pelatihan model: data transaksi asli, notebook eksplorasi,
dan skrip yang membentuk dataset turunan. Tidak ada kode yang berjalan saat aplikasi
melayani pengguna.

## Isi

```
ML/
├── data/
│   └── Transactions.csv        ekspor kasir 53.820 struk
├── notebook/
│   ├── 00_Preprocessing.ipynb
│   ├── stock_forecasting_comparison.ipynb
│   └── stockout_risk_forecast.ipynb
└── script/
    ├── generate_stock_data.py  membentuk Stock.csv dari transaksi
    └── build_stock_dataset.py  membentuk dataset risiko kehabisan stok
```

## Data transaksi

`Transactions.csv` adalah satu-satunya data asli di repo. Isinya struk dari tiga
outlet (SHOP001–SHOP003) dengan kolom tanggal, jam, nomor struk, item, jumlah,
harga, metode pembayaran, dan status kartu loyalitas.

Data ini dipakai di tiga tempat:

1. **Web** — diimpor ke PostgreSQL oleh `TransactionImportSeeder` saat boot pertama,
   sehingga dashboard punya angka nyata.
2. **ML** — menjadi dasar semua fitur model setelah notebook preprocessing.
3. **Verifikasi** — `docker/verify/click_through.py` memakai angka yang berasal
   dari impor ini.

Ekspor aslinya berakhir September 2025. Saat impor, tanggal digeser maju dalam
kelipatan minggu supaya data berakhir kemarin; pola hari dalam minggu tetap utuh.

## Kenapa ada skrip tambahan

Ekspor kasir tidak memuat jumlah stok. Karena itu saldo harus disusun, dan dua
skrip di folder `script/` melakukannya:

- **`generate_stock_data.py`** membuat ledger stok harian sintetis dengan kebijakan
  (s, S): titik pesan ulang dari rata-rata permintaan, jumlah pesan sampai
  `s + rata-rata × (L+1) + 1,96 × simpangan × akar(L+1)`, dengan lead time per
  outlet (SHOP001 = 3 hari, SHOP002 dan SHOP003 = 2 hari). Keluarannya `Stock.csv`
  dan `ItemMaster.csv`.
- **`build_stock_dataset.py`** memperbaiki dua kelemahan ledger itu: pesanan yang
  masih dalam perjalanan direkonstruksi menjadi `on_order_qty`, dan titik pesan
  ulang dihitung ulang dari permintaan terkini (`reorder_point_dyn`) alih-alih
  kolom `MinimumStock` yang statis. Label bersifat maju: "apakah outlet x item
  akan habis dalam lead time atau H hari". Keluarannya
  `stock_forecast_dataset.csv` beserta metadata.

Label risiko kehabisan stok adalah proxy berbasis kecepatan penjualan, bukan hasil
pencatatan stok nyata. API menyebutkan hal ini lewat field `proxy_label`.

## Alur ke aplikasi

```
ML/data/Transactions.csv
      │
      ├──> impor ke PostgreSQL ──────────> dashboard web
      │
      └──> notebook + script ──> artefak ──> API FastAPI ──> Laravel ──> mobile
```

## Kondisi saat ini

- `ML/artifacts/` **tidak ada** di repo, dan folder pelatihan juga tidak ada.
  Akibatnya FastAPI melaporkan kelima model `unavailable` dan endpoint prediksi
  menjawab `503`; bagian lain aplikasi tetap berjalan.
- `ML/README.md` masih kosong.

Untuk mengaktifkan prediksi, artefak harus dihasilkan dengan kontrak direktori
`ML/artifacts/<model_id>/<versi>/` berisi `model.joblib` dan `metadata.json`
(lengkap dengan versi, daftar fitur, dan metrik kualitas hasil holdout). Setelah
artefak ada, `docker compose --profile api up -d` akan memuatnya otomatis.

## Menjalankan skrip

```bash
python3 ML/script/generate_stock_data.py    # butuh ML/data/Transactions.csv
python3 ML/script/build_stock_dataset.py    # butuh Stock.csv dan ItemMaster.csv
```

Keduanya menulis ke `ML/data/`, tidak menyentuh data asli.
