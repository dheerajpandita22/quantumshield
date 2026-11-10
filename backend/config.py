"""
QuantumShield Backend — Central Configuration
Loads settings from environment variables with safe defaults.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "QuantumShield API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Database
    database_url: str = "postgresql://quantumshield:changeme@localhost:5432/quantumshield"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Quantum Engine
    quantum_backend: str = "aer_simulator"
    quantum_shots: int = 1024
    quantum_max_qubits: int = 32

    # Security
    secret_key: str = "CHANGE_ME_IN_PRODUCTION_SECRET_KEY_FOR_LOCAL_DEV_ONLY"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
