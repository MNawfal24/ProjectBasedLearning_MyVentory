# MyVentory Smart Inventory API - runtime image
# Build dari root repository (konteks build harus root agar ML/artifacts ikut):
#   docker build -f API/Dockerfile -t myventory-api .
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MYVENTORY_ARTIFACTS_ROOT=/app/ML/artifacts

WORKDIR /app

# Dependencies first so application edits do not invalidate the pip layer.
COPY API/requirements.txt /app/API/requirements.txt
RUN pip install --no-cache-dir -r /app/API/requirements.txt

# Application code, the API tests, and the model artefacts needed at runtime.
COPY API/app /app/API/app
COPY API/tests /app/API/tests
COPY API/pytest.ini /app/API/pytest.ini
COPY ML/artifacts /app/ML/artifacts

# Non-root runtime user (uid/gid fixed so bind mounts stay predictable).
RUN useradd --create-home --uid 10001 myventory && chown -R myventory:myventory /app
USER myventory

WORKDIR /app/API
EXPOSE 8000

# Runtime configuration (no secrets are baked into the image):
#   MYVENTORY_LOG_LEVEL          default INFO
#   MYVENTORY_ARTIFACTS_ROOT     default /app/ML/artifacts
#   MYVENTORY_LATENCY_SAMPLE_SIZE default 2000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
