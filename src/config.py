"""Application configuration objects."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    """Global app configuration."""

    output_dir: Path = Path("sample_outputs")
    bootstrap_sims: int = 500
    bootstrap_seed: int = 42
    ai_model: str = "gpt-4o-mini"
    percentiles: tuple[int, ...] = field(default_factory=lambda: (50, 75, 90, 95, 99))


DEFAULT_CONFIG = AppConfig()
