from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EcoCIConfig:
    base_url: str
    token: str
    carbon_intensity_kg_per_kwh: float
    runner_cpu_cores: int
    kwh_per_core_hour: float


def load_config() -> EcoCIConfig:
    base_url = os.getenv("GITLAB_BASE_URL", "https://gitlab.com")
    token = os.getenv("GITLAB_TOKEN", "").strip()
    carbon_intensity = float(os.getenv("CARBON_INTENSITY_KG_PER_KWH", "0.475"))
    runner_cores = int(os.getenv("DEFAULT_RUNNER_CPU_CORES", "2"))
    kwh_per_core_hour = float(os.getenv("KWH_PER_CORE_HOUR", "0.5"))

    if not token:
        raise RuntimeError("GITLAB_TOKEN is required")

    return EcoCIConfig(
        base_url=base_url,
        token=token,
        carbon_intensity_kg_per_kwh=carbon_intensity,
        runner_cpu_cores=runner_cores,
        kwh_per_core_hour=kwh_per_core_hour,
    )
