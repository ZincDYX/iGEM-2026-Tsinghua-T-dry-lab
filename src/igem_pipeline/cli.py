from pathlib import Path
from typing import Optional

import typer

from .config import load_config
from .pipeline import run_pipeline

app = typer.Typer(help="Run the iGEM M1-M4 dry-lab pipeline.")


@app.command()
def run(
    config: Path = typer.Argument(..., help="Path to a YAML pipeline config."),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Override run.output_dir from the config.",
    ),
) -> None:
    """Run M1 -> M2 -> M3 -> M4 and write intermediate results."""

    project_config = load_config(config)
    if output_dir is not None:
        project_config.run.output_dir = output_dir
    manifest = run_pipeline(project_config)
    typer.echo(f"Pipeline completed: {manifest.run_dir}")


@app.command()
def validate(
    config: Path = typer.Argument(..., help="Path to a YAML pipeline config."),
) -> None:
    """Validate a pipeline config without running stages."""

    load_config(config)
    typer.echo(f"Config is valid: {config}")
