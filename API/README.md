# MyVentory Smart Inventory API

REST API FastAPI yang melayani tiga model machine learning Smart Inventory:
sales forecasting, demand forecasting, dan product segmentation. Setiap model
punya skema validasi, preprocessing, inference, dan versi sendiri, serta dapat
gagal dimuat tanpa menghentikan aplikasi.

Tidak ada database, Prometheus, Grafana, Redis, atau layanan eksternal lain.
Metrik teknis disimpan in-memory di dalam proses API.

## Menjalankan dengan Docker

```bash
# build image (dari root repository; konteks build harus root agar API/artifacts ikut)
docker build -f API/Dockerfile -t myventory-api .

# jalankan container
docker run -d --name myventory-api -p 8000:8000 myventory-api

# cek kesehatan API
curl http://localhost:8000/api/v1/health
```

Swagger UI ada di `http://localhost:8000/docs` (ReDoc: `/redoc`, OpenAPI:
`/openapi.json`). Image berbasis `python:3.12-slim`, berjalan sebagai user
non-root `myventory` (uid 10001), dan memuat `API/app`, `API/tests`, serta
`API/artifacts`. Konfigurasi diberikan lewat environment variable:

| Variabel | Default | Keterangan |
|---|---|---|
| `MYVENTORY_ARTIFACTS_ROOT` | `/app/API/artifacts` | lokasi direktori artefak model |
| `MYVENTORY_LOG_LEVEL` | `INFO` | level logging aplikasi |
| `MYVENTORY_LATENCY_SAMPLE_SIZE` | `2000` | jumlah sampel latency per bucket |

## Menjalankan tanpa Docker

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r API/requirements.txt
cd API && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoint

Semua endpoint berada di bawah prefix `/api/v1`.

### Prediksi

| Method | Path | Body (contoh) |
|---|---|---|
| POST | `/sales-forecast` | `{"outlet": "SHOP001", "horizon_days": 7}` (`outlet: null` = agregat semua outlet) |
| POST | `/demand-forecast` | `{"product": "Friendly Coffee (Ice)", "horizon_days": 7}` |
| POST | `/segmentation` | `{"products": ["Chocolate (Gedhe)", "Friendly Coffee (Ice)"]}` |

Setiap response memuat envelope yang sama:

```json
{
  "request_id": "...",
  "model_id": "sales_forecast",
  "model_version": "1.0.0",
  "task": "regression",
  "generated_at": "2026-10-11T19:42:14Z",
  "...": "field hasil spesifik model"
}
```

`sales_forecast` mengembalikan deret prediksi, ringkasan, dan 7 hari aktual
terakhir. `demand_forecast` mengembalikan qty per hari plus saran reorder.
`segmentation` mengembalikan klaster, label, jarak ke centroid, distribusi, dan
top 5 produk per segmen.

### Sistem, model, dan metrik

| Method | Path | Keterangan |
|---|---|---|
| GET | `/health` | proses API hidup (tidak bergantung artefak) |
| GET | `/ready` | model yang siap; `503` bila tidak ada model siap |
| GET | `/models` | daftar ketiga model + status, versi, dan metrik kualitas |
| GET | `/models/{model_id}` | identitas, versi, fitur, catatan pelatihan, berkas artefak |
| GET | `/metrics/` | ringkasan teknis + rincian per model dan per endpoint |
| GET | `/metrics/models` | metrik teknis per model, dipisah dari metrik kualitas |
| GET | `/metrics/models/{model_id}` | metrik teknis satu model + rincian endpoint |
| POST | `/metrics/reset` | mengosongkan penghitung metrik in-memory |
| POST | `/models/{model_id}/evaluate` | evaluasi memakai data aktual berlabel dari request |

### Evaluasi

| model_id | bentuk body | metrik |
|---|---|---|
| `sales_forecast` | `{"actuals": [{date, outlet, net_sales}]}` | MAE, RMSE, WAPE + baseline lag-7 |
| `demand_forecast` | `{"actuals": [{date, outlet, product, qty}]}` | `422 evaluation_not_supported` |
| `product_segmentation` | `{"products": [...]}` | Silhouette, Davies-Bouldin, label agreement |

Metrik hanya dihitung bila datanya valid. Bila tidak ada baris yang bisa
dievaluasi, endpoint mengembalikan `422` dengan alasan - bukan angka fiktif.
`note` pada response menjelaskan bahwa artefak dilatih pada seluruh data
historis, sehingga tanggal di dalam rentang historis bersifat in-sample; angka
out-of-sample tersedia di `GET /api/v1/models/{model_id}`.

## Metrik

- **Teknis (in-memory).** Jumlah request, sukses/gagal, error rate, latency
  rata-rata/p50/p95, jumlah inference per model, dan versi model. Data hilang
  saat proses restart dan tidak menyimpan isi request/header/data pengguna.
- **Kualitas (dari pelatihan).** MAE/RMSE/WAPE untuk regresi dan Silhouette/
  Davies-Bouldin untuk clustering, berasal dari holdout saat pelatihan.

## Status HTTP dan format error

| Status | Kapan |
|---|---|
| 200 | request berhasil |
| 404 | `model_id` tidak dikenal |
| 422 | body tidak valid (`validation_error`), input tidak dapat dipakai (`invalid_input`), atau evaluasi tidak didukung |
| 503 | artefak belum tersedia atau gagal dimuat (`model_not_ready`) |
| 500 | kesalahan internal (`internal_error`) |

Semua error memakai bentuk yang sama dan setiap response membawa header
`X-Request-Id`:

```json
{
  "request_id": "69808424210447c0a8e590333a6f5239",
  "error": {
    "code": "model_not_ready",
    "message": "model 'sales_forecast' belum siap menerima request",
    "details": {"reason": "artefak belum tersedia"}
  }
}
```

## Pengujian

```bash
cd API && python3 -m pytest
MYVENTORY_DOCKER_TEST=1 pytest -m docker -v   # build image + uji container
```

Cakupan suite: kesehatan/kesiapan, validasi request dan format response ketiga
endpoint, model yang belum tersedia atau gagal dimuat, konsistensi metrik,
inference memakai artefak nyata di `API/artifacts`, dan evaluasi memakai data
aktual dari `ML/data/Transactions.csv`.

## Struktur kode

```
API/
|-- app/
|   |-- main.py             # factory aplikasi, middleware request-id, error handler
|   |-- config.py           # settings dari environment (prefix MYVENTORY_)
|   |-- errors.py           # ApiError + subclass, helper request id
|   |-- metrics.py          # penyimpanan metrik in-memory
|   |-- schemas.py          # seluruh kontrak request/response
|   |-- model_registry.py   # pemuatan & status ketiga model
|   |-- routes.py           # seluruh endpoint
|   `-- models/
|       |-- base.py             # kontrak ArtifactModel (load artefak, info)
|       |-- common.py           # helper fitur dan metrik regresi
|       |-- sales_forecast.py
|       |-- demand_forecast.py
|       `-- segmentation.py
|-- artifacts/              # bundle runtime: sales_forecast, demand_forecast_product, product_segmentation
|-- tests/
|-- pytest.ini
|-- requirements.txt
`-- Dockerfile
```

## Menambah atau memperbarui model

1. Latih ulang model lewat notebook di `ML/notebook/`, lalu ekspor bundle ke
   `API/artifacts/<model_id>/<versi>/` dengan `model.pkl` dan `metadata.json`.
2. Bila model baru: tambahkan subclass `ArtifactModel` di `app/models/`,
   kontrak request/response di `app/schemas.py`, daftarkan di
   `app/model_registry.py`, lalu tambahkan route di `app/routes.py`.
3. Jalankan `cd API && pytest`.

Model dengan artefak rusak atau belum tersedia dilaporkan `unavailable` pada
`/api/v1/ready` dan `/api/v1/models`; request ke model tersebut dijawab `503`
tanpa mengganggu model lain.
