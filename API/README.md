# MyVentory Smart Inventory API

REST API FastAPI yang melayani lima model machine learning Smart Inventory
(sales forecasting, demand forecasting, segmentation, peak-hour prediction,
stock prediction). Satu aplikasi, lima modul model yang terpisah secara logis:
setiap model punya skema validasi, preprocessing, inference, konfigurasi, dan
versi sendiri, dan dapat gagal dimuat tanpa menghentikan aplikasi.

Tidak ada database, Prometheus, Grafana, Redis, atau layanan eksternal lain.
Metrik teknis disimpan in-memory di dalam proses API.

## Menjalankan dengan Docker

```bash
# build image (dari root repository; konteks build harus root agar ML/artifacts ikut)
docker build -f API/Dockerfile -t myventory-api .

# jalankan container
docker run -d --name myventory-api -p 8000:8000 myventory-api

# cek kesehatan API
curl http://localhost:8000/api/v1/health

# buka Swagger UI
#   http://localhost:8000/docs      (ReDoc: /redoc, OpenAPI: /openapi.json)

# lihat log
docker logs -f myventory-api

# hentikan dan hapus container
docker stop myventory-api && docker rm myventory-api
```

Image berbasis `python:3.12-slim`, berjalan sebagai user non-root `myventory`
(uid 10001), memuat `API/app`, `API/tests`, dan `ML/artifacts`. Tidak ada
secret yang ditanam di image; konfigurasi diberikan lewat environment variable:

| Variabel | Default | Keterangan |
|---|---|---|
| `MYVENTORY_ARTIFACTS_ROOT` | `/app/ML/artifacts` | lokasi direktori artefak model |
| `MYVENTORY_LOG_LEVEL` | `INFO` | level logging aplikasi |
| `MYVENTORY_LATENCY_SAMPLE_SIZE` | `2000` | jumlah sampel latency yang disimpan per bucket |

Container punya `HEALTHCHECK` yang memanggil `/api/v1/health`.

## Menjalankan tanpa Docker

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r API/requirements.txt
cd API && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoint

Semua endpoint berada di bawah prefix `/api/v1`.

### Prediksi (satu endpoint per model)

| Method | Path | Body (contoh) |
|---|---|---|
| POST | `/sales-forecast` | `{"outlet": "SHOP001", "horizon_days": 7}` |
| POST | `/demand-forecast` | `{"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 7}` |
| POST | `/segmentation` | `{"transactions": [{"total_item": 1, "total_amount": 23000, "hour": 8, "day_of_week": 3, "use_loyalty_card": false}]}` |
| POST | `/peak-hour` | `{"outlet": "SHOP001", "date": "2025-10-01"}` (`date` opsional) |
| POST | `/stock-prediction` | `{"outlet": "SHOP001", "product": "Friendly Coffee (Ice)", "horizon_days": 7, "available_stock": 5}` |

Setiap response memuat envelope yang sama:

```json
{
  "request_id": "…",
  "model_id": "sales_forecast",
  "model_version": "1.0.0",
  "task": "regression",
  "generated_at": "2026-10-11T19:42:14Z",
  "...": "field hasil spesifik model"
}
```

Isi hasil disesuaikan karakteristik tiap model: `sales_forecast` mengembalikan
deret prediksi + ringkasan + 7 hari aktual terakhir; `demand_forecast`
menambahkan pendapatan dan saran jumlah pemesanan ulang; `segmentation`
mengembalikan klaster, label, jarak ke centroid, dan distribusi klaster;
`peak-hour` mengembalikan 16 jam operasional (07:00–22:00) beserta jam tersibuk
dan penanda jam sibuk; `stock_prediction` mengembalikan kebutuhan stok
kumulatif, saran reorder, probabilitas risiko, dan penjelasan label proxy.

### Sistem, model, dan metrik

| Method | Path | Keterangan |
|---|---|---|
| GET | `/health` | proses API hidup (tidak bergantung artefak) |
| GET | `/ready` | model yang siap menerima request; `503` bila tidak ada model siap |
| GET | `/models` | daftar kelima model + status, versi, dan metrik kualitas |
| GET | `/models/{model_id}` | identitas, versi, fitur, catatan pelatihan, berkas artefak |
| GET | `/metrics/` | ringkasan teknis + rincian per model dan per endpoint |
| GET | `/metrics/models` | metrik teknis per model, dipisah dari metrik kualitas |
| GET | `/metrics/models/{model_id}` | metrik teknis satu model + rincian endpoint |
| POST | `/metrics/reset` | mengosongkan penghitung metrik in-memory |
| POST | `/models/{model_id}/evaluate` | evaluasi memakai data aktual berlabel dari request |

### Evaluasi

`POST /api/v1/models/{model_id}/evaluate` menerima data aktual berlabel dan
menghitung metrik kualitas memakai model yang sedang dilayani:

| model_id | bentuk `actuals` | metrik |
|---|---|---|
| `sales_forecast` | `{date, outlet, net_sales}` | MAE, RMSE, WAPE + baseline lag-7 |
| `demand_forecast` | `{date, outlet, product, qty}` | MAE, RMSE, WAPE + baseline lag-7 |
| `segmentation` | transaksi + `cluster` opsional | Silhouette, Davies–Bouldin, agreement label |
| `peak_hour` | `{date, outlet, hour, tx_count}` + `peak_label` | MAE, RMSE, precision/recall/F1 |
| `stock_prediction` | `{date, outlet, product, required_stock}` | MAE, RMSE, WAPE, precision/recall/F1 risiko |

Metrik hanya dihitung bila datanya valid. Bila tidak ada baris yang bisa
dievaluasi (tanggal di luar rentang fitur, outlet/produk tidak dikenal, hanya
satu kelas), endpoint mengembalikan `422` dengan alasan - bukan angka fiktif.
Setiap response evaluasi memuat field `note` yang menjelaskan bahwa artefak
yang dilayani dilatih ulang pada seluruh data historis, sehingga tanggal di
dalam rentang historis bersifat in-sample; angka out-of-sample tersedia di
`GET /api/v1/models/{model_id}` (holdout 28 hari terakhir).

## Metrik

Dua kelompok metrik dipisahkan dengan sengaja:

- **Teknis (in-memory, sementara).** Jumlah request, request sukses/gagal,
  error rate, latency rata-rata/p50/p95, jumlah inference per model, dan versi
  model yang dipakai. Dapat dibedakan per model dan per endpoint. Data hilang
  saat proses di-restart dan tidak pernah menyimpan isi request, header, atau
  data pengguna - hanya counter, status code, latency, dan versi model.
  Permintaan yang gagal validasi tetap tercatat sebagai request, sedangkan
  `inferences` hanya menghitung prediksi yang benar-benar dihasilkan.
- **Kualitas (dari pelatihan).** MAE/RMSE/WAPE untuk model regresi, Silhouette
  dan Davies–Bouldin untuk clustering, precision/recall/F1 untuk klasifikasi.
  Angka ini berasal dari holdout 28 hari terakhir saat pelatihan dan tidak
  pernah dihitung dari trafik API.

## Status HTTP dan format error

| Status | Kapan |
|---|---|
| 200 | request berhasil |
| 404 | `model_id` tidak dikenal |
| 422 | body tidak valid (`validation_error`) atau input tidak dapat dipakai model (`invalid_input`) |
| 503 | artefak model belum tersedia atau gagal dimuat (`model_not_ready`) |
| 500 | kesalahan internal (`internal_error`) |

Semua error memakai bentuk yang sama, dan setiap response membawa header
`X-Request-Id` (nilai dari request bila dikirim, atau dibuat baru):

```json
{
  "request_id": "69808424210447c0a8e590333a6f5239",
  "error": {
    "code": "model_not_ready",
    "message": "model 'stock_prediction' belum siap menerima request",
    "details": {"reason": "artefak belum tersedia"}
  }
}
```

## Pengujian

```bash
cd API && python3 -m pytest            # suite utama (67 tes)
MYVENTORY_DOCKER_TEST=1 pytest -m docker -v   # build image + uji container
```

Cakupan suite: kesehatan/kesiapan, validasi request dan format response kelima
endpoint, penanganan input tidak valid, model yang belum tersedia atau gagal
dimuat (mock/isolated), konsistensi pencatatan metrik, inference memakai
artefak nyata di `ML/artifacts`, dan evaluasi memakai data aktual dari
`ML/data/Transactions.csv`.

## Struktur kode

```
API/
├── app/
│   ├── main.py             # factory aplikasi, middleware request-id, error handler
│   ├── config.py           # settings dari environment (prefix MYVENTORY_)
│   ├── errors.py           # ApiError + subclass, helper request id
│   ├── metrics.py          # penyimpanan metrik in-memory
│   ├── schemas.py          # seluruh kontrak request/response
│   ├── model_registry.py   # pemuatan & status kelima model
│   ├── routes.py           # seluruh endpoint (system, prediksi, evaluasi, metrik)
│   └── models/
│       ├── base.py             # kontrak ArtifactModel (load artefak, info)
│       ├── common.py           # HistoryIndex, pembentuk fitur, metrik regresi
│       ├── sales_forecast.py   # konstanta + preprocessing + inference + evaluasi
│       ├── demand_forecast.py
│       ├── segmentation.py
│       ├── peak_hour.py
│       └── stock_prediction.py
├── tests/
│   ├── conftest.py             # fixture client, artefak kosong/rusak
│   ├── test_system.py          # health, ready, daftar model, OpenAPI
│   ├── test_predictions.py     # validasi request & kontrak response 5 endpoint
│   ├── test_inference.py       # inference memakai artefak nyata
│   ├── test_evaluation.py      # evaluasi memakai data aktual berlabel
│   ├── test_metrics.py         # konsistensi metrik teknis
│   ├── test_availability.py    # model hilang / artefak rusak
│   └── test_docker.py          # build image + startup container
├── pytest.ini
├── requirements.txt
└── Dockerfile                  # dibangun dengan konteks root: docker build -f API/Dockerfile .
```

Setiap modul model memuat konstanta fiturnya sendiri dan berdiri sendiri:
mengubah satu model tidak menyentuh model lain. `app/models/base.py` dan
`app/models/common.py` berisi kontrak artefak dan helper bersama yang dipakai
lebih dari satu model.

## Menambah atau memperbarui model

1. Latih ulang model dengan `python3 ML/train/train_<model>.py`
   (lihat `ML/README.md`), atau tambahkan trainer baru yang mengikuti kontrak
   artefak: `<model_id>/<versi>/{model.joblib, metadata.json, *.json}`.
2. Bila model baru: tambahkan `app/models/<model_id>.py` berisi konstanta fitur
   dan subclass `ArtifactModel` (muat artefak, `predict`, `evaluate`), tambahkan
   kontrak request/response di `app/schemas.py`, lalu daftarkan kelasnya di
   `app/model_registry.py` dan tambahkan route-nya di `app/routes.py`.
3. Jalankan `cd API && pytest`.

Model dengan artefak rusak atau belum tersedia dilaporkan `unavailable` beserta
alasannya pada `/api/v1/ready` dan `/api/v1/models`; request ke model tersebut
dijawab `503` tanpa mengganggu model lain.
