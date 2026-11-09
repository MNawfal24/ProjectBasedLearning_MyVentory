# API — layanan prediksi FastAPI

Folder ini berisi satu aplikasi FastAPI yang melayani lima model machine learning.
Perannya sempit dan sengaja dibuat begitu: menerima angka, menjalankan model,
mengembalikan hasil. Tidak ada database, tidak ada login, tidak ada data pengguna.

Stack: Python 3.12, FastAPI, scikit-learn, pandas, joblib.

## Kenapa tanpa database dan tanpa autentikasi

Layanan ini tidak menyimpan apa pun. Semua data yang dibutuhkan model datang dari
artefak hasil pelatihan, dan konteks outlet/produk dikirim pada request. Karena
tidak menyimpan data dan tidak punya akun, layanan ini tidak perlu autentikasi
sendiri. Konsekuensinya: **jangan diekspos ke internet**. Yang memanggil hanya
Laravel lewat jaringan Docker internal `http://api:8000`.

Aplikasi mobile tidak pernah memanggil FastAPI langsung. Laravel yang meneruskan
permintaan lewat `/api/v1/predictions/*` sehingga token staf tetap satu pintu.

## Lima model

| `model_id` | Endpoint | Menjawab |
|---|---|---|
| `sales_forecast` | `POST /sales-forecast` | Total penjualan harian per outlet beberapa hari ke depan, plus ringkasan dan 7 hari aktual terakhir |
| `demand_forecast` | `POST /demand-forecast` | Jumlah unit terjual per outlet x produk, pendapatan perkiraan, dan saran jumlah pesan ulang |
| `segmentation` | `POST /segmentation` | Klaster transaksi, label, dan jarak ke centroid |
| `peak_hour` | `POST /peak-hour` | Volume struk tiap jam operasional 07:00–22:00 dan jam tersibuk |
| `stock_prediction` | `POST /stock-prediction` | Kebutuhan stok kumulatif, saran reorder, probabilitas risiko kehabisan |

Setiap model dimuat terpisah dari `ML/artifacts/<model_id>/<versi>/`. Satu artefak
rusak hanya membuat model itu berstatus `unavailable`, bukan menghentikan aplikasi.

## Endpoint sistem dan metrik

| Method | Endpoint | Isi |
|---|---|---|
| GET | `/health` | proses hidup, tidak bergantung artefak |
| GET | `/ready` | model mana yang siap; `503` bila tidak ada |
| GET | `/models` | daftar model, status, versi, metrik kualitas |
| GET | `/models/{model_id}` | detail satu model |
| GET | `/metrics/` | ringkasan teknis in-memory |
| GET | `/metrics/models` | metrik teknis per model |
| POST | `/models/{model_id}/evaluate` | metrik kualitas dari data aktual yang dikirim |
| POST | `/metrics/reset` | kosongkan penghitung |

Metrik teknis disimpan di memori proses dan hilang saat restart. Isinya hanya
jumlah request, status code, latency, jumlah inference, dan versi model — tidak
pernah isi request atau data pengguna.

## Bentuk respons

Semua prediksi memakai envelope yang sama:

```json
{
  "request_id": "…",
  "model_id": "demand_forecast",
  "model_version": "1.0.0",
  "task": "regression",
  "generated_at": "2026-11-09T10:00:00Z",
  "outlet": "SHOP001",
  "product": "Friendly Coffee (Ice)",
  "predictions": [],
  "summary": {}
}
```

Kesalahan memakai satu bentuk, dan setiap respons membawa header `X-Request-Id`:

```json
{
  "request_id": "…",
  "error": {
    "code": "model_not_ready",
    "message": "model 'stock_prediction' belum siap menerima request",
    "details": {"reason": "artefak belum tersedia"}
  }
}
```

| Status | Kapan |
|---|---|
| 200 | berhasil |
| 404 | `model_id` tidak dikenal |
| 422 | body tidak valid atau input tidak dapat dipakai model |
| 503 | artefak belum ada atau gagal dimuat |
| 500 | kesalahan internal |

## Struktur kode

```
API/
├── app/
│   ├── main.py             factory aplikasi, request-id, error handler
│   ├── config.py           setting dari environment (prefix MYVENTORY_)
│   ├── errors.py           ApiError dan subclass
│   ├── metrics.py          penyimpanan metrik in-memory
│   ├── schemas.py          kontrak request/response
│   ├── model_registry.py   pemuatan dan status lima model
│   ├── routes.py           seluruh endpoint
│   └── models/
│       ├── base.py         kontrak ArtifactModel
│       ├── common.py       helper bersama
│       └── <model_id>.py   satu modul per model
├── tests/                  tujuh berkas tes
├── Dockerfile
└── requirements.txt
```

## Menjalankan

```bash
# lewat compose (disarankan; artefak di-mount read-only)
docker compose --profile api up -d

# tanpa Docker
python3 -m venv .venv && . .venv/bin/activate
pip install -r API/requirements.txt
cd API && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Swagger tersedia di `http://localhost:8000/docs`.

| Variabel | Default | Keterangan |
|---|---|---|
| `MYVENTORY_ARTIFACTS_ROOT` | `/app/ML/artifacts` | lokasi artefak |
| `MYVENTORY_LOG_LEVEL` | `INFO` | level log |
| `MYVENTORY_LATENCY_SAMPLE_SIZE` | `2000` | sampel latency per bucket |

## Kondisi saat ini

`ML/artifacts/` tidak ada di repo. Tanpa artefak, `/ready` mengembalikan `503`,
`/models` menandai kelima model `unavailable`, dan Laravel meneruskan hasilnya
sebagai `503` pada endpoint prediksi. Untuk mengaktifkan prediksi, artefak harus
dihasilkan lebih dulu — lihat [ml.md](ml.md).
