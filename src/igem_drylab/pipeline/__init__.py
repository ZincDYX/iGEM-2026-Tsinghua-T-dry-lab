"""Lightweight M1-M4 dry-lab pipeline interfaces."""

from .config import ProjectConfig, load_config


def __getattr__(name):
    if name in {"run_pipeline", "run_through_m4"}:
        from . import runner
        return getattr(runner, name)
    raise AttributeError(name)

__all__ = ["ProjectConfig", "load_config", "run_pipeline", "run_through_m4"]
