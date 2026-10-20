"""One canonical config source; wheels contain build-time copies as assets."""
from importlib.resources import files
from pathlib import Path


def default_config_path(name: str) -> Path:
    packaged = files("igem_drylab").joinpath("assets", name)
    if packaged.is_file():
        return Path(str(packaged))
    # Editable/source checkout: canonical files remain in the existing configs.
    return Path(__file__).resolve().parents[2] / "configs" / name
