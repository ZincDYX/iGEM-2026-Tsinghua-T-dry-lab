from __future__ import annotations

import json
from pathlib import Path

import typer

from igem_drylab.literature import answer_question, build_prompt, load_schema
from igem_drylab.literature.qa_server import serve as serve_literature_qa
from igem_drylab.agent import AgentRuntime, AgentTask, OpenAICompatiblePlanningBackend, HybridLLMPlanningBackend
from igem_drylab.agent.env import load_local_env
from igem_drylab.literature.database import build_database_from_manifest
from igem_drylab.literature.icl import load_icl_examples
from igem_drylab.literature.sources import LiteratureSearchQuery, search_literature, write_search_manifest
from igem_drylab.mcp import create_default_registry
from igem_drylab.multichain import assess_interface, solve_binding_equilibrium
from igem_drylab.pipeline import load_config, run_pipeline
from igem_drylab.project_state import ProjectState
from igem_drylab.parameters import validate_parameters
from igem_drylab.parameters import ParameterRegistry
from igem_drylab.parameters import ParameterRecord
from igem_drylab.parameters.requirements import requirements_for_stage
from igem_drylab.wetlab.parameter_update import approve_and_persist_parameter, validate_candidate_for_approval

app = typer.Typer(help="iGEM 2026 Tsinghua-T dry-lab utilities.")
pipeline_app = typer.Typer(help="Run M1-M4 pipeline skeleton.")
literature_app = typer.Typer(help="Use schema-first literature extraction helpers.")
multichain_app = typer.Typer(help="Build and inspect multichain module designs.")
tools_app = typer.Typer(help="Inspect and call MCP-style local tools.")
agent_app = typer.Typer(help="Plan and run conservative dry-lab agent workflows.")
parameters_app = typer.Typer(help="Inspect reviewed scientific parameters and provenance.")
project_app = typer.Typer(help="Inspect the registry-backed project state.")
software_app = typer.Typer(help="Run the local software dashboard.")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(literature_app, name="literature")
app.add_typer(multichain_app, name="multichain")
app.add_typer(tools_app, name="tools")
app.add_typer(agent_app, name="agent")
app.add_typer(parameters_app, name="parameters")
app.add_typer(project_app, name="project")
app.add_typer(software_app, name="software")


@pipeline_app.command("analyze-m4")
def analyze_m4(prediction_file: Path, analysis_file: Path, output_file: Path):
    from igem_drylab.design_analysis import M4AnalysisConfig, analyze_prediction
    raw = json.loads(prediction_file.read_text(encoding="utf-8"))
    result = analyze_prediction(raw.get("prediction_contract", raw),
                                M4AnalysisConfig.model_validate_json(analysis_file.read_text(encoding="utf-8")))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")


@pipeline_app.command("freeze-prediction")
def freeze_research_prediction(prediction_file: Path, parameter_file: Path, plan_file: Path, output_file: Path):
    from igem_drylab.research_validation import freeze_prediction
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    sources = {name:Path(path) for name,path in plan.pop("calibration_datasets").items()}
    snapshot = freeze_prediction(prediction_file,parameter_file,sources,**plan)
    output_file.parent.mkdir(parents=True,exist_ok=True)
    if output_file.exists():
        raise ValueError("freeze_output_exists_create_a_new_freeze")
    output_file.write_text(json.dumps(snapshot,indent=2,allow_nan=False),encoding="utf-8")


@pipeline_app.command("validate-holdout")
def validate_research_holdout(freeze_file: Path, dataset_id: str, dataset_file: Path, output_file: Path):
    from igem_drylab.research_validation import validate_holdout
    result = validate_holdout(json.loads(freeze_file.read_text(encoding="utf-8")),dataset_id,dataset_file)
    output_file.parent.mkdir(parents=True,exist_ok=True)
    if output_file.exists():
        raise ValueError("holdout_output_exists_preserve_prior_validation")
    output_file.write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")


@pipeline_app.command("scan-designs")
def scan_designs(plan_file: Path, output_dir: Path):
    from igem_drylab.design_analysis import FiniteDesignPlan, scan_scaffold_designs
    plan = FiniteDesignPlan.model_validate_json(plan_file.read_text(encoding="utf-8"))
    result = scan_scaffold_designs(plan, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "design_decision.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")


@software_app.command("serve")
def serve_software_dashboard(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8780, "--port", min=1, max=65535),
    data_dir: Path = typer.Option(Path("outputs/platform"), "--data-dir"),
    development: bool = typer.Option(False, "--dev-anonymous", help="Explicit loopback-only software development mode."),
    token_env: str = typer.Option("FUSIONLAB_API_TOKEN", "--api-token-env"),
) -> None:
    """Serve the local Dashboard API; start the React dev server separately."""
    from igem_drylab.software.dashboard import serve as serve_dashboard

    serve_dashboard(host=host, port=port, data_dir=data_dir, development=development, token_env=token_env)


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


@literature_app.command("qa")
def literature_qa_command(
    question: str,
    evidence: Path = typer.Option(..., "--evidence", "-e"),
    top_k: int = typer.Option(5, "--top-k", min=1),
    mode: str = typer.Option("retrieve_only", "--mode", help="retrieve_only or synthesize"),
    semantic_enabled: bool = typer.Option(False, "--semantic", help="Use the optional embedding backend configured in the environment."),
) -> None:
    """Search a local evidence file and print provenance-bearing results."""
    load_local_env()
    typer.echo(json.dumps(answer_question(question, evidence, top_k=top_k, mode=mode, semantic_enabled=semantic_enabled), ensure_ascii=False, indent=2))


@literature_app.command("serve-qa")
def serve_literature_qa_command(
    evidence: Path = typer.Option(..., "--evidence", "-e"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port", min=1, max=65535),
) -> None:
    """Serve the local QA page; use a non-local host only behind your own access control."""
    load_local_env()
    serve_literature_qa(evidence, host=host, port=port)


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
    typer.echo(json.dumps({"query": query, "providers": provider, "results": len(results), "output_manifest": str(output_manifest) if output_manifest else None}, ensure_ascii=False, indent=2))


@parameters_app.command("list")
def list_parameters(config: Path) -> None:
    """List registry records; literature evidence is not automatically reviewed."""
    typer.echo(json.dumps([item.model_dump(mode="json") for item in load_config(config).parameters], ensure_ascii=False, indent=2))


@parameters_app.command("validate")
def validate_parameter_records(
    config: Path,
    required: list[str] = typer.Option([], "--required", help="Required parameter name; repeat option."),
) -> None:
    project = load_config(config)
    _selected, missing = validate_parameters(project.parameters, required_names=set(required), allow_assumptions=project.execution.allow_assumptions)
    typer.echo(json.dumps({"ok": not missing, "missing": missing}, ensure_ascii=False, indent=2))
    if missing:
        raise typer.Exit(code=1)


@parameters_app.command("provenance")
def parameter_provenance(config: Path, parameter_id: str) -> None:
    for item in load_config(config).parameters:
        if item.parameter_id == parameter_id:
            typer.echo(item.model_dump_json(indent=2)); return
    raise typer.BadParameter(f"Unknown parameter_id: {parameter_id}")


@parameters_app.command("query")
def query_parameters(
    config: Path,
    parameter_type: str | None = typer.Option(None, "--type"),
    enzyme: str | None = typer.Option(None, "--enzyme"),
    substrate: str | None = typer.Option(None, "--substrate"),
) -> None:
    registry = ParameterRegistry(load_config(config).parameters)
    typer.echo(json.dumps([item.model_dump(mode="json") for item in registry.query(parameter_type=parameter_type, enzyme_id=enzyme, substrate_id=substrate)], ensure_ascii=False, indent=2))


@parameters_app.command("conflicts")
def parameter_conflicts(config: Path) -> None:
    project = load_config(config)
    catalog = {
        requirement.name: requirement
        for stage in ("m3", "m4")
        for requirement in requirements_for_stage(project, stage)
    }
    registry = ParameterRegistry(project.parameters)
    typer.echo(json.dumps([item.model_dump(mode="json") for item in registry.list_conflicts(requirements=catalog)], ensure_ascii=False, indent=2))


@parameters_app.command("validate-candidate")
def validate_parameter_candidate(
    config: Path,
    candidate_file: Path,
    stage: str = typer.Option(..., "--stage"),
    requirement_name: str = typer.Option(..., "--requirement-name"),
    reviewer: str = typer.Option(..., "--reviewer"),
) -> None:
    """Validate a candidate at the same approval boundary used by persistence."""
    project = load_config(config)
    candidate = ParameterRecord.model_validate_json(candidate_file.read_text(encoding="utf-8"))
    requirement = next((item for item in requirements_for_stage(project, stage) if item.name == requirement_name), None)
    if requirement is None:
        raise typer.BadParameter("Unknown declared requirement")
    validate_candidate_for_approval(project, candidate, requirement, reviewer)
    typer.echo(json.dumps({"ok": True, "approval_required": True}, ensure_ascii=False))


@parameters_app.command("approve")
def approve_parameter_candidate(
    config: Path,
    candidate_file: Path,
    stage: str = typer.Option(..., "--stage"),
    requirement_name: str = typer.Option(..., "--requirement-name"),
    reviewer: str = typer.Option(..., "--reviewer"),
) -> None:
    """Persist one reviewed candidate; this is deliberately an explicit human action."""
    candidate = ParameterRecord.model_validate_json(candidate_file.read_text(encoding="utf-8"))
    approved = approve_and_persist_parameter(config, candidate, reviewer=reviewer, target_stage=stage, target_requirement_name=requirement_name)
    typer.echo(approved.model_dump_json(indent=2))


@project_app.command("state")
def project_state(config: Path) -> None:
    project = load_config(config)
    state = ProjectState.from_project(project)
    typer.echo(state.model_dump_json(indent=2))


@project_app.command("missing-inputs")
def project_missing_inputs(config: Path, stage: str = typer.Option("m4", "--stage")) -> None:
    project = load_config(config)
    state = ProjectState.from_project(project)
    from igem_drylab.pipeline.config import canonical_m4_condition_id
    condition_id = canonical_m4_condition_id(project.stages.m4_reaction)
    typer.echo(json.dumps({"stage": stage, "missing": state.missing_inputs(stage, allow_assumptions=project.execution.allow_assumptions, condition_id=condition_id, enable_degradation=project.stages.m4_reaction.enable_degradation, require_provenance=project.execution.mode == "real" and project.execution.require_provenance)}, ensure_ascii=False, indent=2))


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


def _load_agent_task(task_file: Path) -> AgentTask:
    payload = json.loads(task_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise typer.BadParameter("Agent task file must contain a JSON object")
    return AgentTask.model_validate(payload)


def _agent_runtime(
    memory_path: Path,
    *,
    planner: str,
    api_base: str | None,
    model: str | None,
    api_key_env: str,
) -> AgentRuntime:
    if planner == "rule-based":
        return AgentRuntime(memory_path=memory_path)
    if planner not in {"llm", "hybrid"}:
        raise typer.BadParameter("Planner must be 'rule-based', 'llm', or 'hybrid'")
    import os

    load_local_env()
    prefix = "QWEN" if api_key_env.startswith("QWEN_") else "DEEPSEEK"
    resolved_base = api_base or os.getenv(f"{prefix}_API_BASE") or "https://api.deepseek.com/chat/completions"
    resolved_model = model or os.getenv(f"{prefix}_MODEL") or ("qwen3-235b-a22b-instruct-2507" if prefix == "QWEN" else "deepseek-chat")
    backend_class = HybridLLMPlanningBackend if planner == "hybrid" else OpenAICompatiblePlanningBackend
    backend = backend_class.from_environment(
        api_base=resolved_base,
        model=resolved_model,
        api_key_env=api_key_env,
    )
    return AgentRuntime(memory_path=memory_path, planning_backend=backend)


@agent_app.command("dry-run")
def agent_dry_run(
    task_file: Path,
    memory_path: Path = typer.Option(Path("outputs/agent_memory/events.jsonl"), "--memory-path"),
    planner: str = typer.Option("rule-based", "--planner", help="rule-based (default), llm, or hybrid"),
    api_base: str | None = typer.Option(None, "--api-base", help="OpenAI-compatible /chat/completions URL"),
    model: str | None = typer.Option(None, "--model", help="Model name for --planner llm"),
    api_key_env: str = typer.Option("DEEPSEEK_API_KEY", "--api-key-env"),
) -> None:
    runtime = _agent_runtime(memory_path, planner=planner, api_base=api_base, model=model, api_key_env=api_key_env)
    trace = runtime.dry_run(_load_agent_task(task_file))
    typer.echo(trace.model_dump_json(indent=2))


@agent_app.command("run")
def agent_run(
    task_file: Path,
    memory_path: Path = typer.Option(Path("outputs/agent_memory/events.jsonl"), "--memory-path"),
    planner: str = typer.Option("rule-based", "--planner", help="rule-based (default), llm, or hybrid"),
    api_base: str | None = typer.Option(None, "--api-base", help="OpenAI-compatible /chat/completions URL"),
    model: str | None = typer.Option(None, "--model", help="Model name for --planner llm"),
    api_key_env: str = typer.Option("DEEPSEEK_API_KEY", "--api-key-env"),
) -> None:
    runtime = _agent_runtime(memory_path, planner=planner, api_base=api_base, model=model, api_key_env=api_key_env)
    trace = runtime.run_once(_load_agent_task(task_file))
    typer.echo(trace.model_dump_json(indent=2))
    if trace.final_status in {"blocked", "failed"}:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
