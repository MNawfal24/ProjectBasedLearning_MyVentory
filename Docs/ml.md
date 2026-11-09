# ML — data, notebook, dan skrip dataset

Folder ini menyimpan bahan pelatihan model: data transaksi asli, notebook eksplorasi,
dan skrip yang membentuk dataset turunan. Tidak ada kode yang berjalan saat aplikasi
melayani pengguna.

## Isi

```
ML/
├── data/
│   ├── Transactions.csv        ekspor kasir 53.820 struk
│   ├── Stock.csv               ledger stok harian per outlet x item
│   └── ItemMaster.csv          ItemID -> nama produk
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

Data ini dipakai di empat tempat:

1. **Web** — diimpor ke PostgreSQL oleh `TransactionImportSeeder` saat boot pertama,
   sehingga dashboard punya angka nyata.
2. **Web** — `Stock.csv` diimpor oleh `StockImportSeeder` menjadi saldo stok.
3. **ML** — menjadi dasar semua fitur model setelah notebook preprocessing.
4. **Verifikasi** — `docker/verify/click_through.py` memakai angka yang berasal
   dari impor ini.

Tanggal tidak digeser saat impor: dashboard menampilkan rentang yang benar-benar
ada di berkas.

## Data stok

`Stock.csv` adalah ledger harian dengan kolom `Date, Outlet, ItemID,
OpeningStock, StockIn, StockOut, ClosingStock, MinimumStock`, dan
`ItemMaster.csv` memetakan `ItemID` ke nama produk.

Berkasnya dibentuk oleh `script/generate_stock_data.py` dari penjualan asli:
satu baris per outlet x item x hari, jumlah terjual menjadi `StockOut`, dan
kebijakan pengisian ulang (s, S) menentukan `StockIn` serta `ClosingStock`.
Artinya **saldo stok adalah hasil simulasi dari transaksi asli**, bukan hasil
stock opname. Kalau nanti ada pencatatan stok fisik, ganti `Stock.csv` dengan
ekspor itu — `StockImportSeeder` tidak peduli dari mana berkasnya berasal,
selama kolom dan aturannya sama.

Aturannya harus konsisten, karena `build_stock_dataset.py` dan
`StockImportSeeder` sama-sama mengandalkannya:

- grain unik `Date x Outlet x ItemID`, dan setiap seri memuat tanggal lengkap
  tanpa hari yang hilang (baris tanpa penjualan tetap ada dengan `StockOut = 0`);
- `OpeningStock + StockIn - StockOut = ClosingStock`, `ClosingStock >= 0`;
- `OpeningStock` sebuah hari sama dengan `ClosingStock` hari sebelumnya;
- `ProductName` di `ItemMaster.csv` sama persis dengan string item di
  `Transactions.csv`.

## Kenapa ada skrip tambahan

Ekspor kasir tidak memuat jumlah stok, jadi dua skrip di folder `script/`
menyiapkannya:

- **`generate_stock_data.py`** membentuk `Stock.csv` dan `ItemMaster.csv` dari
  transaksi: kebijakan (s, S) dengan titik pesan ulang
  `max(1, ceil(rata-rata harian × 3))` dan lead time per outlet (SHOP001 = 3
  hari, SHOP002 dan SHOP003 = 2 hari). Keluarannya simulasi, bukan pencatatan.
- **`build_stock_dataset.py`** menyusun dataset pemodelan. Fitur stok dibaca apa
  adanya (`ClosingStock`, `MinimumStock`, `gap_to_min`, `cover_days`), fitur
  permintaan adalah `StockOut` yang di-lag, dan fitur trafik outlet berasal dari
  transaksi. Tidak ada lead time, pesanan dalam perjalanan, atau reorder point
  yang direkonstruksi. Label bersifat maju: "apakah outlet x item akan habis
  dalam H hari", dengan `H` 2, 3, dan 7.

Dataset itu tidak membuat label risiko kehabisan stok dari kecepatan penjualan
sebagai pengganti pencatatan stok: labelnya memakai `ClosingStock` yang tercatat.
`demand_true`, `is_censored` dan `lost_units` tetap ada untuk mengukur berapa
permintaan yang tidak terlayani ledger.

## Alur ke aplikasi

```
ML/data/Transactions.csv
      │
      ├──> impor ke PostgreSQL ──────────> dashboard web
      │
      └──> notebook ──> artefak ──> API FastAPI ──> Laravel ──> mobile

ML/data/Stock.csv + ItemMaster.csv
      │
      ├──> impor ke PostgreSQL ──────────> halaman stok + dashboard
      │
      └──> build_stock_dataset.py ──> dataset latih ──> artefak
```

## Kondisi saat ini

- `Stock.csv` dan `ItemMaster.csv` sudah ada di repo, dibentuk oleh
  `generate_stock_data.py`. Isinya simulasi ledger dari penjualan asli, jadi
  saldo stok di dashboard adalah keadaan simulasi pada tanggal terakhir berkas
  (2025-09-30), bukan stok fisik hari ini.
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
python3 ML/script/build_stock_dataset.py    # butuh Stock.csv, ItemMaster.csv
```

Keduanya menulis ke `ML/data/`, tidak menyentuh data asli.
