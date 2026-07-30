from __future__ import annotations

from pathlib import Path

import typer

from igem_drylab.literature import build_prompt, load_schema
from igem_drylab.literature.icl import load_icl_examples
from igem_drylab.pipeline import load_config, run_pipeline

app = typer.Typer(help="iGEM 2026 Tsinghua-T dry-lab utilities.")
pipeline_app = typer.Typer(help="Run M1-M4 pipeline skeleton.")
literature_app = typer.Typer(help="Use schema-first literature extraction helpers.")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(literature_app, name="literature")


@pipeline_app.command("validate")
def validate_pipeline(config: Path) -> None:
    load_config(config)
    typer.echo(f"Config is valid: {config}")


@pipeline_app.command("run")
def run_pipeline_command(
    config: Path,
    output_dir: Path | None = typer.Option(None, "--output-dir", "-o"),
) -> None:
    project_config = load_config(config)
    if output_dir is not None:
        project_config.run.output_dir = output_dir
    manifest = run_pipeline(project_config)
    typer.echo(f"Pipeline completed: {manifest.run_dir}")


@literature_app.command("build-prompt")
def build_literature_prompt(
    text_file: Path,
    schema: Path,
    icl_bank: Path | None = typer.Option(None, "--icl-bank"),
    top_k: int = typer.Option(3, "--top-k", min=0),
    out: Path | None = typer.Option(None, "--out", "-o"),
) -> None:
    extraction_schema = load_schema(schema)
    examples = load_icl_examples(icl_bank)
    prompt = build_prompt(
        text=text_file.read_text(encoding="utf-8"),
        schema=extraction_schema,
        examples=examples,
        icl_top_k=top_k,
    )
    if out is None:
        typer.echo(prompt)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        typer.echo(f"Wrote prompt: {out}")


if __name__ == "__main__":
    app()
