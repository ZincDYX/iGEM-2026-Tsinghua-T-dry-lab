from __future__ import annotations

import json
from pathlib import Path

import typer

from igem_drylab.literature import build_prompt, load_schema
from igem_drylab.literature.database import build_database_from_manifest
from igem_drylab.literature.icl import load_icl_examples
from igem_drylab.literature.sources import LiteratureSearchQuery, search_literature, write_search_manifest
from igem_drylab.mcp import create_default_registry
from igem_drylab.multichain import assess_interface, solve_binding_equilibrium
from igem_drylab.pipeline import load_config, run_pipeline

app = typer.Typer(help="iGEM 2026 Tsinghua-T dry-lab utilities.")
pipeline_app = typer.Typer(help="Run M1-M4 pipeline skeleton.")
literature_app = typer.Typer(help="Use schema-first literature extraction helpers.")
multichain_app = typer.Typer(help="Build and inspect multichain module designs.")
tools_app = typer.Typer(help="Inspect and call MCP-style local tools.")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(literature_app, name="literature")
app.add_typer(multichain_app, name="multichain")
app.add_typer(tools_app, name="tools")


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


@literature_app.command("build-database")
def build_literature_database(
    manifest: Path,
    schema: Path,
    output_dir: Path = typer.Option(..., "--output-dir", "-o"),
    max_per_paper: int = typer.Option(8, "--max-per-paper", min=1),
    max_contexts_per_paper: int = typer.Option(160, "--max-contexts-per-paper", min=20),
) -> None:
    summary = build_database_from_manifest(
        manifest=manifest,
        schema=load_schema(schema),
        output_dir=output_dir,
        max_per_paper=max_per_paper,
        max_contexts_per_paper=max_contexts_per_paper,
    )
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))


@literature_app.command("search")
def search_literature_command(
    query: str,
    provider: list[str] = typer.Option(["openalex"], "--provider", "-p"),
    output_manifest: Path | None = typer.Option(None, "--output-manifest", "-o"),
    max_results: int = typer.Option(25, "--max-results", min=1),
    from_year: int | None = typer.Option(None, "--from-year"),
    to_year: int | None = typer.Option(None, "--to-year"),
    mailto: str | None = typer.Option(None, "--mailto"),
    api_key_env: str | None = typer.Option(None, "--api-key-env"),
) -> None:
    results = search_literature(
        providers=provider,
        query=LiteratureSearchQuery(
            query=query,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            mailto=mailto,
            api_key_env=api_key_env,
        ),
    )
    if output_manifest is not None:
        write_search_manifest(output_manifest, results)
    typer.echo(
        json.dumps(
            {
                "query": query,
                "providers": provider,
                "results": len(results),
                "output_manifest": str(output_manifest) if output_manifest else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@multichain_app.command("binding-equilibrium")
def binding_equilibrium_command(
    receptor: str,
    ligand: str,
    receptor_total: float,
    ligand_total: float,
    kd: float,
    receptor_valency: int = typer.Option(1, "--receptor-valency", min=1),
    ligand_valency: int = typer.Option(1, "--ligand-valency", min=1),
) -> None:
    result = solve_binding_equilibrium(
        receptor=receptor,
        ligand=ligand,
        receptor_total=receptor_total,
        ligand_total=ligand_total,
        kd=kd,
        receptor_valency=receptor_valency,
        ligand_valency=ligand_valency,
    )
    typer.echo(result.model_dump_json(indent=2))


@multichain_app.command("assess-interface")
def assess_interface_command(
    pdb_file: Path,
    chain_a: str,
    chain_b: str,
    contact_cutoff_angstrom: float = typer.Option(5.0, "--contact-cutoff"),
    clash_cutoff_angstrom: float = typer.Option(2.0, "--clash-cutoff"),
) -> None:
    result = assess_interface(
        pdb_file=pdb_file,
        chain_a=chain_a,
        chain_b=chain_b,
        contact_cutoff_angstrom=contact_cutoff_angstrom,
        clash_cutoff_angstrom=clash_cutoff_angstrom,
    )
    typer.echo(result.model_dump_json(indent=2))


@tools_app.command("list")
def list_tools() -> None:
    registry = create_default_registry()
    typer.echo(json.dumps({"tools": registry.list_tools()}, ensure_ascii=False, indent=2))


@tools_app.command("call")
def call_tool(
    name: str,
    arguments_json: str | None = typer.Option(None, "--arguments-json"),
    arguments_file: Path | None = typer.Option(None, "--arguments-file"),
) -> None:
    if arguments_json and arguments_file:
        raise typer.BadParameter("Use either --arguments-json or --arguments-file, not both")
    if arguments_file is not None:
        raw_arguments = arguments_file.read_text(encoding="utf-8")
    else:
        raw_arguments = arguments_json or "{}"
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Tool arguments must be valid JSON: {exc}") from exc
    if not isinstance(arguments, dict):
        raise typer.BadParameter("Tool arguments must be a JSON object")
    result = create_default_registry().call(name, arguments)
    typer.echo(json.dumps(result.as_protocol_dict(), ensure_ascii=False, indent=2))
    if result.is_error:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
