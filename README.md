# MyVentory

**Sistem inventori pintar untuk kafe dan UMKM.** MyVentory menyatukan catatan
penjualan kasir, saldo stok per outlet, dan prediksi permintaan dari model machine
learning dalam satu tempat.

Pemilik kafe biasanya tahu berapa yang terjual kemarin, tapi tidak tahu berapa yang
harus dipesan besok. MyVentory mengambil data transaksi, menyusun saldo stok dari
data itu, lalu memakai model ML untuk memperkirakan permintaan, jam sibuk, dan
risiko kehabisan stok â€” sehingga keputusan restock tidak lagi menebak.

## Siapa memakai apa

| Aplikasi | Pengguna | Kemampuan |
|---|---|---|
| Dashboard web | Admin / pemilik | Melihat seluruh angka, mencatat penjualan, mengatur stok dan batas minimum, mengelola produk dan akun staf |
| Aplikasi mobile | Staf | Masuk, melihat stok, produk, ringkasan penjualan, dan prediksi permintaan |

Keduanya tidak saling memanggil. Keduanya memakai satu backend Laravel dan satu
database PostgreSQL, jadi angka di ponsel dan di browser selalu berasal dari baris
yang sama.

```
Flutter (staf, baca saja)  â”€â”€Bearer tokenâ”€â”€â”
                                           â”œâ”€â”€> Laravel /api/v1 â”€â”€> PostgreSQL
Dashboard web (admin)      â”€â”€sessionâ”€â”€â”€â”€â”€â”€â”€â”˜              â”‚
                                                          â””â”€â”€> FastAPI ML
                                                               (internal)
```

## Yang bisa dilihat

- KPI periode: penjualan bersih, jumlah transaksi, rata-rata per struk, item terjual
  â€” lengkap dengan pembanding periode sebelumnya.
- Tren penjualan harian, jam tersibuk, pola hari, dan metode pembayaran.
- Saldo stok per outlet x produk dengan status aman, menipis, atau habis.
- Prediksi permintaan per produk, kebutuhan stok, dan saran jumlah pesan ulang.
- Riwayat pergerakan stok: masuk, keluar, penjualan, dan penyesuaian stok opname.

Semua angka dihitung dari tabel, tidak ada nilai contoh di layar.

## Mencoba

Butuh Docker dan Docker Compose.

```bash
cp .env.example .env
docker compose up -d --build
```

Buka `http://localhost:8080`, masuk sebagai `admin@myventory.com` / `admin123`,
lalu buat akun staf dari menu **Akun** untuk dipakai di aplikasi mobile.

```bash
cd Mobile
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080/api/v1
```

Catatan: `ML/artifacts/` belum ada di repo, jadi lima model berstatus `unavailable`
dan endpoint prediksi menjawab `503`. Transaksi berasal dari ekspor kasir apa
adanya (2025-01-02 sampai 2025-09-30). Saldo stok diimpor dari `ML/data/Stock.csv`
yang dibentuk dari penjualan itu, jadi statusnya simulasi ledger — bukan hasil
stock opname. Fitur lain berjalan normal.

## Lisensi

Dirilis di bawah [MIT License](LICENSE).

## Kredit

Dibuat sebagai proyek *Project Based Learning* Semester 5, Politeknik Negeri Malang.

Terima kasih kepada para kontributor:

| Kontributor | GitHub |
|---|---|
| Vanesa Mardiana Putri | [@vanesamrd](https://github.com/vanesamrd) |
| M. Nawfal Mawla Azhar | [@MNawfal24](https://github.com/MNawfal24) |
| Arya Bayu Samodra | [@bavucadoz](https://github.com/bavucadoz) |
| Radit Firansah | [@Raditfiransah](https://github.com/Raditfiransah) |
| Raya Rabbani | [@RayaRabbani129](https://github.com/RayaRabbani129) |

Repositori: [MNawfal24/ProjectBasedLearning_MyVentory](https://github.com/MNawfal24/ProjectBasedLearning_MyVentory)

Data transaksi yang dipakai bersifat contoh untuk keperluan pembelajaran.

