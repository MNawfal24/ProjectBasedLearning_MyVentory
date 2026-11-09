"""Runtime configuration (env driven, prefix ``MYVENTORY_``)."""

from __future__ import annotations

import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYVENTORY_", env_file=".env", extra="ignore")

    api_title: str = "MyVentory Smart Inventory API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # Directory holding ML/artifacts/<model_id>/<version>/
    artifacts_root: pathlib.Path = REPO_ROOT / "ML" / "artifacts"

    # Number of latency samples kept per (model, endpoint) bucket for percentiles.
    latency_sample_size: int = 2000

    log_level: str = "INFO"


settings = Settings()
