from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from igem_drylab.literature import build_prompt, extract_records_from_text, load_schema
from igem_drylab.literature.elsevier import extract_text_from_xml, fetch_article_xml, search_scopus
from igem_drylab.literature.icl import load_icl_examples
from igem_drylab.literature.llm import ChatClient
from igem_drylab.literature.database import build_database_from_manifest
from igem_drylab.literature.sources import LiteratureSearchQuery, search_literature, write_search_manifest
from igem_drylab.multichain import assess_interface, build_multichain_input, expand_fth1_arms, solve_binding_equilibrium
from igem_drylab.multichain.models import ProteinChain
from igem_drylab.parsers.freesasa import compute_pocket_sasa_retention
from igem_drylab.parsers.calvados import parse_calvados_output
from igem_drylab.parsers.structure_prediction import parse_structure_prediction_output
from igem_drylab.scoring.m2_structure import M2StructureMetrics, score_m2_structure
from igem_drylab.scoring.m4_reaction import (
    DockingPenalty,
    compute_docking_penalty,
    score_m4_ode,
    score_m4_piecewise_ode,
)
from igem_drylab.kinetics import CascadeParameters, CompetitiveCascadeParameters, InductionGate
from igem_drylab.pipeline.adapters import create_tool_adapter
from igem_drylab.pipeline import load_config, run_pipeline

from .types import JsonObject, McpTool, McpToolResult, ToolHandler


def _schema(
    properties: JsonObject,
    required: list[str] | None = None,
    *,
    additional_properties: bool = False,
) -> JsonObject:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": additional_properties,
    }


def _require_str(arguments: JsonObject, key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Argument '{key}' must be a non-empty string")
    return value


def _optional_int(arguments: JsonObject, key: str, default: int, *, minimum: int | None = None) -> int:
    value = arguments.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"Argument '{key}' must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"Argument '{key}' must be >= {minimum}")
    return value


def _optional_path(arguments: JsonObject, key: str) -> Path | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"Argument '{key}' must be a non-empty string path")
    return Path(value)


def _read_text_file(arguments: JsonObject, path_key: str, inline_key: str) -> str:
    inline = arguments.get(inline_key)
    path = arguments.get(path_key)
    if isinstance(inline, str) and inline:
        return inline
    if isinstance(path, str) and path:
        return Path(path).read_text(encoding="utf-8")
    raise ValueError(f"Provide either '{inline_key}' or '{path_key}'")


def _secret_from_env(arguments: JsonObject, env_key: str, default_env_name: str) -> str:
    env_name = arguments.get(env_key, default_env_name)
    if not isinstance(env_name, str) or not env_name:
        raise ValueError(f"Argument '{env_key}' must be a non-empty environment variable name")
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"Environment variable '{env_name}' is not set")
    return value


def pipeline_validate(arguments: JsonObject) -> McpToolResult:
    config_path = Path(_require_str(arguments, "config_path"))
    config = load_config(config_path)
    return McpToolResult.ok(
        {
            "ok": True,
            "config_path": str(config_path),
            "run_id": config.run.id,
            "enzymes": [enzyme.id for enzyme in config.inputs.enzymes],
            "scaffolds": [scaffold.id for scaffold in config.inputs.scaffolds],
            "linkers": [linker.id for linker in config.inputs.linkers],
        }
    )


def pipeline_run(arguments: JsonObject) -> McpToolResult:
    config_path = Path(_require_str(arguments, "config_path"))
    output_dir = _optional_path(arguments, "output_dir")
    config = load_config(config_path)
    if output_dir is not None:
        config.run.output_dir = output_dir
    manifest = run_pipeline(config)
    return McpToolResult.ok(
        {
            "ok": True,
            "run_id": manifest.run_id,
            "run_dir": str(manifest.run_dir),
            "stages": [
                {
                    "stage": stage.stage,
                    "json_file": str(stage.json_file),
                    "csv_file": str(stage.csv_file),
                    "record_count": stage.record_count,
                }
                for stage in manifest.stages
            ],
        }
    )


def compute_check_tool(arguments: JsonObject) -> McpToolResult:
    config = load_config(Path(_require_str(arguments, "config_path")))
    tool_name = _require_str(arguments, "tool_name")
    adapter = create_tool_adapter(tool_name, config.tools.get(tool_name))
    description = adapter.describe()
    return McpToolResult.ok(
        {
            "ok": True,
            "tool_name": tool_name,
            "enabled": adapter.config.enabled,
            "mode": adapter.config.mode,
            "command": adapter.config.command,
            "repo_path": str(adapter.config.repo_path) if adapter.config.repo_path is not None else None,
            "available": adapter.is_available(),
            "description": description.model_dump(mode="json"),
        }
    )


def compute_run_tool(arguments: JsonObject) -> McpToolResult:
    config = load_config(Path(_require_str(arguments, "config_path")))
    tool_name = _require_str(arguments, "tool_name")
    output_dir = Path(_require_str(arguments, "output_dir"))
    context = arguments.get("context", {})
    if not isinstance(context, dict):
        raise ValueError("Argument 'context' must be an object")
    dry_run = bool(arguments.get("dry_run", False))
    timeout_seconds = _optional_int(arguments, "timeout_seconds", 3600, minimum=1)
    adapter = create_tool_adapter(tool_name, config.tools.get(tool_name))
    result = adapter.run(output_dir=output_dir, dry_run=dry_run, timeout_seconds=timeout_seconds, **context)
    result = _persist_standard_output(tool_name, result)
    return McpToolResult.ok({"ok": result.status not in {"failed", "missing_executable"}, "run": result.model_dump(mode="json")})


def _persist_standard_output(tool_name: str, result: Any) -> Any:
    """Materialize machine-readable stdout for downstream local tools.

    AutoDock Vina prints its pose table to stdout and FreeSASA can print JSON to
    stdout. Persisting those streams makes the next stage reproducible without
    parsing an agent trace. Empty mock output is intentionally not written.
    """
    filenames = {"autodock_vina": "vina_stdout.txt", "freesasa": "freesasa.json"}
    filename = filenames.get(tool_name)
    if filename is None or result.output_dir is None or not result.stdout.strip():
        return result
    output_file = result.output_dir / filename
    output_file.write_text(result.stdout, encoding="utf-8")
    return result.model_copy(update={"outputs": {**result.outputs, "standard_output": output_file}})


def multichain_build_input(arguments: JsonObject) -> McpToolResult:
    raw_chains = arguments.get("chains")
    if not isinstance(raw_chains, list):
        raise ValueError("Argument 'chains' must be a list")
    chains = [ProteinChain.model_validate(item) for item in raw_chains]
    result = build_multichain_input(
        complex_id=_require_str(arguments, "complex_id"),
        chains=chains,
        output_dir=Path(_require_str(arguments, "output_dir")),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def multichain_binding_equilibrium(arguments: JsonObject) -> McpToolResult:
    receptor_valency = _optional_int(arguments, "receptor_valency", 1, minimum=1)
    ligand_valency = _optional_int(arguments, "ligand_valency", 1, minimum=1)
    result = solve_binding_equilibrium(
        receptor=_require_str(arguments, "receptor"),
        ligand=_require_str(arguments, "ligand"),
        receptor_total=float(arguments.get("receptor_total", 0.0)),
        ligand_total=float(arguments.get("ligand_total", 0.0)),
        kd=float(arguments.get("kd", 0.0)),
        receptor_valency=receptor_valency,
        ligand_valency=ligand_valency,
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def multichain_assess_interface(arguments: JsonObject) -> McpToolResult:
    result = assess_interface(
        pdb_file=Path(_require_str(arguments, "pdb_file")),
        chain_a=_require_str(arguments, "chain_a"),
        chain_b=_require_str(arguments, "chain_b"),
        contact_cutoff_angstrom=float(arguments.get("contact_cutoff_angstrom", 5.0)),
        clash_cutoff_angstrom=float(arguments.get("clash_cutoff_angstrom", 2.0)),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def multichain_expand_fth1_arms(arguments: JsonObject) -> McpToolResult:
    probe_residue_ids = arguments.get("probe_residue_ids")
    if probe_residue_ids is not None and (
        not isinstance(probe_residue_ids, list) or not all(isinstance(value, int) for value in probe_residue_ids)
    ):
        raise ValueError("Argument 'probe_residue_ids' must be a list of integers")
    result = expand_fth1_arms(
        template_pdb=Path(_require_str(arguments, "template_pdb")),
        local_arm_pdb=Path(_require_str(arguments, "local_arm_pdb")),
        reference_core_chain=_require_str(arguments, "reference_core_chain"),
        core_anchor_residue=int(arguments.get("core_anchor_residue")),
        core_anchor_atom=_require_str(arguments, "core_anchor_atom"),
        core_orientation_atom=_require_str(arguments, "core_orientation_atom"),
        arm_anchor_chain=_require_str(arguments, "arm_anchor_chain"),
        arm_anchor_residue=int(arguments.get("arm_anchor_residue")),
        arm_anchor_atom=_require_str(arguments, "arm_anchor_atom"),
        arm_orientation_atom=_require_str(arguments, "arm_orientation_atom"),
        probe_chain=arguments.get("probe_chain") if isinstance(arguments.get("probe_chain"), str) else None,
        probe_residue_ids=probe_residue_ids,
        clash_cutoff_angstrom=float(arguments.get("clash_cutoff_angstrom", 2.0)),
        exposure_cutoff_angstrom=float(arguments.get("exposure_cutoff_angstrom", 5.0)),
        expected_subunits=_optional_int(arguments, "expected_subunits", 24, minimum=1),
        output_pdb=_optional_path(arguments, "output_pdb"),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def scoring_pocket_sasa(arguments: JsonObject) -> McpToolResult:
    residues = arguments.get("residues")
    if not isinstance(residues, list) or not all(isinstance(item, int) for item in residues):
        raise ValueError("Argument 'residues' must be a list of integers")
    result = compute_pocket_sasa_retention(
        model_pdb=_optional_path(arguments, "model_pdb"),
        reference_pdb=_optional_path(arguments, "reference_pdb"),
        model_json=_optional_path(arguments, "model_json"),
        reference_json=_optional_path(arguments, "reference_json"),
        chain=_require_str(arguments, "chain"),
        residues=residues,
        threshold_loss_fraction=float(arguments.get("threshold_loss_fraction", 0.15)),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def scoring_m2_structure(arguments: JsonObject) -> McpToolResult:
    result = score_m2_structure(M2StructureMetrics.model_validate(arguments))
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def parser_structure_prediction(arguments: JsonObject) -> McpToolResult:
    result = parse_structure_prediction_output(
        Path(_require_str(arguments, "path")),
        candidate_id=arguments.get("candidate_id") if isinstance(arguments.get("candidate_id"), str) else None,
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def parser_calvados(arguments: JsonObject) -> McpToolResult:
    result = parse_calvados_output(Path(_require_str(arguments, "path")))
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def scoring_docking_penalty(arguments: JsonObject) -> McpToolResult:
    result = compute_docking_penalty(
        candidate_id=_require_str(arguments, "candidate_id"),
        reference_vina_output=Path(_require_str(arguments, "reference_vina_output")),
        fusion_vina_output=Path(_require_str(arguments, "fusion_vina_output")),
        allowed_loss_kcal_mol=float(arguments.get("allowed_loss_kcal_mol", 1.0)),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def scoring_m4_ode(arguments: JsonObject) -> McpToolResult:
    params_payload = arguments.get("params", {})
    if not isinstance(params_payload, dict):
        raise ValueError("Argument 'params' must be an object")
    penalty_payload = arguments.get("docking_penalty")
    result = score_m4_ode(
        candidate_id=_require_str(arguments, "candidate_id"),
        params=CascadeParameters(**params_payload),
        docking_penalty=None if penalty_payload is None else DockingPenalty.model_validate(penalty_payload),
        t_end=float(arguments.get("t_end", 24.0)),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def scoring_m4_piecewise_ode(arguments: JsonObject) -> McpToolResult:
    params_payload = arguments.get("params", {})
    if not isinstance(params_payload, dict):
        raise ValueError("Argument 'params' must be an object")
    oc_gate_payload = arguments.get("oc_gate", {})
    dmt_gate_payload = arguments.get("dmt_gate", {})
    if not isinstance(oc_gate_payload, dict) or not isinstance(dmt_gate_payload, dict):
        raise ValueError("Arguments 'oc_gate' and 'dmt_gate' must be objects")
    initial_payload = arguments.get("initial", [10.0, 0.0, 0.0, 0.0])
    if not isinstance(initial_payload, list) or len(initial_payload) != 4:
        raise ValueError("Argument 'initial' must be a four-number list")
    penalty_payload = arguments.get("docking_penalty")
    result = score_m4_piecewise_ode(
        candidate_id=_require_str(arguments, "candidate_id"),
        params=CompetitiveCascadeParameters(**params_payload),
        oc_gate=InductionGate(**oc_gate_payload),
        dmt_gate=InductionGate(**dmt_gate_payload),
        docking_penalty=None if penalty_payload is None else DockingPenalty.model_validate(penalty_payload),
        initial=tuple(float(value) for value in initial_payload),  # type: ignore[arg-type]
        t_end=float(arguments.get("t_end", 24.0)),
    )
    return McpToolResult.ok({"ok": True, "result": result.model_dump(mode="json")})


def literature_build_prompt(arguments: JsonObject) -> McpToolResult:
    text = _read_text_file(arguments, "text_file", "text")
    schema = load_schema(Path(_require_str(arguments, "schema_path")))
    examples = load_icl_examples(_optional_path(arguments, "icl_bank"))
    top_k = _optional_int(arguments, "top_k", 3, minimum=0)
    prompt = build_prompt(text=text, schema=schema, examples=examples, icl_top_k=top_k)
    out_path = _optional_path(arguments, "output_path")
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt, encoding="utf-8")
    return McpToolResult.ok(
        {
            "ok": True,
            "prompt": prompt if out_path is None else None,
            "output_path": str(out_path) if out_path is not None else None,
            "example_count": len(examples),
            "top_k": top_k,
        }
    )


def literature_build_database(arguments: JsonObject) -> McpToolResult:
    manifest = Path(_require_str(arguments, "manifest_path"))
    schema = load_schema(Path(_require_str(arguments, "schema_path")))
    output_dir = Path(_require_str(arguments, "output_dir"))
    max_per_paper = _optional_int(arguments, "max_per_paper", 8, minimum=1)
    max_contexts_per_paper = _optional_int(arguments, "max_contexts_per_paper", 160, minimum=20)
    summary = build_database_from_manifest(
        manifest=manifest,
        schema=schema,
        output_dir=output_dir,
        max_per_paper=max_per_paper,
        max_contexts_per_paper=max_contexts_per_paper,
    )
    return McpToolResult.ok({"ok": True, "summary": summary})


def literature_search(arguments: JsonObject) -> McpToolResult:
    provider_value = arguments.get("providers", ["openalex"])
    if not isinstance(provider_value, list) or not all(isinstance(item, str) for item in provider_value):
        raise ValueError("Argument 'providers' must be a list of strings")
    max_results = _optional_int(arguments, "max_results", 25, minimum=1)
    from_year = arguments.get("from_year")
    to_year = arguments.get("to_year")
    if from_year is not None and not isinstance(from_year, int):
        raise ValueError("Argument 'from_year' must be an integer when provided")
    if to_year is not None and not isinstance(to_year, int):
        raise ValueError("Argument 'to_year' must be an integer when provided")
    mailto = arguments.get("mailto")
    if mailto is not None and not isinstance(mailto, str):
        raise ValueError("Argument 'mailto' must be a string when provided")
    api_key_env = arguments.get("api_key_env")
    if api_key_env is not None and not isinstance(api_key_env, str):
        raise ValueError("Argument 'api_key_env' must be a string when provided")
    results = search_literature(
        providers=provider_value,
        query=LiteratureSearchQuery(
            query=_require_str(arguments, "query"),
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            mailto=mailto,
            api_key_env=api_key_env,
        ),
    )
    output_manifest = _optional_path(arguments, "output_manifest")
    if output_manifest is not None:
        write_search_manifest(output_manifest, results)
    return McpToolResult.ok(
        {
            "ok": True,
            "result_count": len(results),
            "output_manifest": str(output_manifest) if output_manifest else None,
            "results": [result.__dict__ | {"raw": None} for result in results],
        }
    )


def literature_extract_records(arguments: JsonObject) -> McpToolResult:
    text = _read_text_file(arguments, "text_file", "text")
    schema = load_schema(Path(_require_str(arguments, "schema_path")))
    examples = load_icl_examples(_optional_path(arguments, "icl_bank"))
    top_k = _optional_int(arguments, "top_k", 3, minimum=0)
    client = ChatClient(
        api_key=_secret_from_env(arguments, "api_key_env", "DEEPSEEK_API_KEY"),
        api_base=_require_str(arguments, "api_base"),
        model=_require_str(arguments, "model"),
        temperature=float(arguments.get("temperature", 0.2)),
        timeout_seconds=_optional_int(arguments, "timeout_seconds", 180, minimum=1),
        retries=_optional_int(arguments, "retries", 3, minimum=1),
    )
    records = extract_records_from_text(text=text, schema=schema, examples=examples, client=client, icl_top_k=top_k)
    output_path = _optional_path(arguments, "output_path")
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    return McpToolResult.ok(
        {
            "ok": True,
            "records": records,
            "record_count": len(records),
            "output_path": str(output_path) if output_path is not None else None,
        }
    )


def elsevier_search(arguments: JsonObject) -> McpToolResult:
    query = _require_str(arguments, "query")
    count = _optional_int(arguments, "count", 10, minimum=1)
    api_key = _secret_from_env(arguments, "api_key_env", "ELSEVIER_API_KEY")
    entries = search_scopus(api_key=api_key, query=query, count=count)
    return McpToolResult.ok({"ok": True, "query": query, "count": len(entries), "entries": entries})


def elsevier_fetch_article_text(arguments: JsonObject) -> McpToolResult:
    api_key = _secret_from_env(arguments, "api_key_env", "ELSEVIER_API_KEY")
    pii = arguments.get("pii")
    doi = arguments.get("doi")
    if pii is not None and not isinstance(pii, str):
        raise ValueError("Argument 'pii' must be a string when provided")
    if doi is not None and not isinstance(doi, str):
        raise ValueError("Argument 'doi' must be a string when provided")
    xml = fetch_article_xml(api_key=api_key, pii=pii, doi=doi)
    if xml is None:
        raise ValueError("Provide either 'pii' or 'doi'")
    text = extract_text_from_xml(xml)
    return McpToolResult.ok({"ok": True, "text": text, "character_count": len(text)})


PIPELINE_VALIDATE_TOOL = McpTool(
    name="igem.pipeline.validate",
    title="Validate M1-M4 pipeline config",
    description="Validate a YAML config and return the normalized run inputs.",
    input_schema=_schema({"config_path": {"type": "string", "description": "Path to project YAML config."}}, ["config_path"]),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "run_id": {"type": "string"}},
        additional_properties=True,
    ),
)

PIPELINE_RUN_TOOL = McpTool(
    name="igem.pipeline.run",
    title="Run M1-M4 pipeline",
    description="Run the local M1-M4 dry-lab pipeline and write JSON/CSV outputs.",
    input_schema=_schema(
        {
            "config_path": {"type": "string"},
            "output_dir": {"type": "string", "description": "Optional output directory override."},
        },
        ["config_path"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "run_dir": {"type": "string"}, "stages": {"type": "array"}},
        additional_properties=True,
    ),
)

COMPUTE_CHECK_TOOL = McpTool(
    name="igem.compute.check_tool",
    title="Check configured compute tool",
    description="Inspect command template, mode, and executable availability for a scientific compute tool.",
    input_schema=_schema(
        {
            "config_path": {"type": "string"},
            "tool_name": {
                "type": "string",
                "description": "Tool key from YAML, e.g. abcfold, calvados, freesasa, autodock_vina.",
            },
        },
        ["config_path", "tool_name"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "tool_name": {"type": "string"}, "available": {"type": "boolean"}},
        additional_properties=True,
    ),
)

COMPUTE_RUN_TOOL = McpTool(
    name="igem.compute.run_tool",
    title="Run configured compute tool",
    description="Render and optionally execute a scientific command-line tool from the YAML config.",
    input_schema=_schema(
        {
            "config_path": {"type": "string"},
            "tool_name": {"type": "string"},
            "output_dir": {"type": "string"},
            "context": {
                "type": "object",
                "description": "Template values used by the command, e.g. input_file, config_file, pdb_file.",
            },
            "dry_run": {"type": "boolean"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
        },
        ["config_path", "tool_name", "output_dir"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "run": {"type": "object"}}, additional_properties=True),
)

MULTICHAIN_BUILD_INPUT_TOOL = McpTool(
    name="igem.multichain.build_input",
    title="Build multichain structure input",
    description="Create a multichain FASTA and manifest for complex prediction tools such as ABCFold.",
    input_schema=_schema(
        {
            "complex_id": {"type": "string"},
            "output_dir": {"type": "string"},
            "chains": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "chain_id": {"type": "string"},
                        "name": {"type": "string"},
                        "sequence": {"type": "string"},
                        "copies": {"type": "integer", "minimum": 1},
                        "role": {"type": "string"},
                    },
                    "required": ["chain_id", "name", "sequence"],
                    "additionalProperties": False,
                },
            },
        },
        ["complex_id", "output_dir", "chains"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

MULTICHAIN_BINDING_EQUILIBRIUM_TOOL = McpTool(
    name="igem.multichain.binding_equilibrium",
    title="Solve multicomponent binding equilibrium",
    description="Solve finite-site A+B binding for two expressed modules with configurable valency and Kd.",
    input_schema=_schema(
        {
            "receptor": {"type": "string"},
            "ligand": {"type": "string"},
            "receptor_total": {"type": "number"},
            "ligand_total": {"type": "number"},
            "kd": {"type": "number"},
            "receptor_valency": {"type": "integer", "minimum": 1},
            "ligand_valency": {"type": "integer", "minimum": 1},
        },
        ["receptor", "ligand", "receptor_total", "ligand_total", "kd"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

MULTICHAIN_ASSESS_INTERFACE_TOOL = McpTool(
    name="igem.multichain.assess_interface",
    title="Assess chain-chain interface",
    description="Calculate contact, clash, and minimum-distance metrics between two chains in a PDB file.",
    input_schema=_schema(
        {
            "pdb_file": {"type": "string"},
            "chain_a": {"type": "string"},
            "chain_b": {"type": "string"},
            "contact_cutoff_angstrom": {"type": "number"},
            "clash_cutoff_angstrom": {"type": "number"},
        },
        ["pdb_file", "chain_a", "chain_b"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

MULTICHAIN_EXPAND_FTH1_ARMS_TOOL = McpTool(
    name="igem.multichain.expand_fth1_arms",
    title="Expand a local fusion arm around an FTH1 24-mer template",
    description=(
        "Map one local appendage structure to every FTH1 subunit using template geometry, then report "
        "core/arm clashes and a geometric exposure proxy. This is not an LLPS or SASA calculation."
    ),
    input_schema=_schema(
        {
            "template_pdb": {"type": "string"}, "local_arm_pdb": {"type": "string"},
            "reference_core_chain": {"type": "string"}, "core_anchor_residue": {"type": "integer"},
            "core_anchor_atom": {"type": "string"}, "core_orientation_atom": {"type": "string"},
            "arm_anchor_chain": {"type": "string"}, "arm_anchor_residue": {"type": "integer"},
            "arm_anchor_atom": {"type": "string"}, "arm_orientation_atom": {"type": "string"},
            "probe_chain": {"type": "string"}, "probe_residue_ids": {"type": "array", "items": {"type": "integer"}},
            "clash_cutoff_angstrom": {"type": "number"}, "exposure_cutoff_angstrom": {"type": "number"},
            "expected_subunits": {"type": "integer", "minimum": 1}, "output_pdb": {"type": "string"},
        },
        ["template_pdb", "local_arm_pdb", "reference_core_chain", "core_anchor_residue", "core_anchor_atom",
         "core_orientation_atom", "arm_anchor_chain", "arm_anchor_residue", "arm_anchor_atom", "arm_orientation_atom"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

SCORING_POCKET_SASA_TOOL = McpTool(
    name="igem.scoring.pocket_sasa",
    title="Calculate pocket SASA retention",
    description="Compare model and reference pocket SASA from FreeSASA JSON or PDB inputs.",
    input_schema=_schema(
        {
            "model_json": {"type": "string"},
            "reference_json": {"type": "string"},
            "model_pdb": {"type": "string"},
            "reference_pdb": {"type": "string"},
            "chain": {"type": "string"},
            "residues": {"type": "array", "items": {"type": "integer"}},
            "threshold_loss_fraction": {"type": "number"},
        },
        ["chain", "residues"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

SCORING_M2_STRUCTURE_TOOL = McpTool(
    name="igem.scoring.m2_structure",
    title="Score M2 structure compatibility",
    description="Apply transparent rule-based structural screening from SASA/RMSD/PAE/confidence/clash metrics.",
    input_schema=_schema(
        {
            "candidate_id": {"type": "string"},
            "sasa_retention": {"type": "number"},
            "pocket_rmsd_angstrom": {"type": "number"},
            "mean_interdomain_pae": {"type": "number"},
            "iptm": {"type": "number"},
            "mean_plddt": {"type": "number"},
            "interface_contact_count": {"type": "integer"},
            "clash_count": {"type": "integer"},
            "notes": {"type": "string"},
        },
        ["candidate_id"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

PARSER_STRUCTURE_PREDICTION_TOOL = McpTool(
    name="igem.parsers.structure_prediction",
    title="Parse ColabFold/AF3/Boltz/Chai/ABCFold prediction outputs",
    description="Extract pTM/ipTM/pLDDT/PAE/clash summary metrics from real structure-prediction output folders.",
    input_schema=_schema(
        {
            "path": {"type": "string"},
            "candidate_id": {"type": "string"},
        },
        ["path"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

PARSER_CALVADOS_TOOL = McpTool(
    name="igem.parsers.calvados",
    title="Parse CALVADOS analysis outputs",
    description="Extract dense/dilute concentration, enrichment factor, cSat, Rg, and LLPS score from CALVADOS summaries.",
    input_schema=_schema({"path": {"type": "string"}}, ["path"]),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

SCORING_DOCKING_PENALTY_TOOL = McpTool(
    name="igem.scoring.docking_penalty",
    title="Calculate Vina docking penalty",
    description="Parse wild-type and fusion Vina outputs and convert affinity loss into an activity multiplier.",
    input_schema=_schema(
        {
            "candidate_id": {"type": "string"},
            "reference_vina_output": {"type": "string"},
            "fusion_vina_output": {"type": "string"},
            "allowed_loss_kcal_mol": {"type": "number"},
        },
        ["candidate_id", "reference_vina_output", "fusion_vina_output"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

SCORING_M4_ODE_TOOL = McpTool(
    name="igem.scoring.m4_ode",
    title="Score M4 lightweight ODE",
    description="Run lightweight two-phase ODE scoring with optional docking penalty.",
    input_schema=_schema(
        {
            "candidate_id": {"type": "string"},
            "params": {"type": "object"},
            "docking_penalty": {"type": "object"},
            "t_end": {"type": "number"},
        },
        ["candidate_id"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

SCORING_M4_PIECEWISE_ODE_TOOL = McpTool(
    name="igem.scoring.m4_piecewise_ode",
    title="Score M4 OC-first/DMT-later competitive ODE",
    description="Run the complete piecewise induction ODE with shared DMT substrate competition and byproduct leakage.",
    input_schema=_schema(
        {
            "candidate_id": {"type": "string"},
            "params": {"type": "object"},
            "oc_gate": {"type": "object"},
            "dmt_gate": {"type": "object"},
            "docking_penalty": {"type": "object"},
            "initial": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
            "t_end": {"type": "number"},
        },
        ["candidate_id"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "result": {"type": "object"}}, additional_properties=True),
)

LITERATURE_BUILD_PROMPT_TOOL = McpTool(
    name="igem.literature.build_prompt",
    title="Build literature extraction prompt",
    description="Build a schema-first extraction prompt with optional ICL examples.",
    input_schema=_schema(
        {
            "text": {"type": "string"},
            "text_file": {"type": "string"},
            "schema_path": {"type": "string"},
            "icl_bank": {"type": "string"},
            "top_k": {"type": "integer", "minimum": 0},
            "output_path": {"type": "string"},
        },
        ["schema_path"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "prompt": {"type": ["string", "null"]}},
        additional_properties=True,
    ),
)

LITERATURE_BUILD_DATABASE_TOOL = McpTool(
    name="igem.literature.build_database",
    title="Build literature database",
    description="Build an offline structured evidence database from a manifest of cached article text files.",
    input_schema=_schema(
        {
            "manifest_path": {"type": "string"},
            "schema_path": {"type": "string"},
            "output_dir": {"type": "string"},
            "max_per_paper": {"type": "integer", "minimum": 1},
            "max_contexts_per_paper": {"type": "integer", "minimum": 20},
        },
        ["manifest_path", "schema_path", "output_dir"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "summary": {"type": "object"}}, additional_properties=True),
)

LITERATURE_SEARCH_TOOL = McpTool(
    name="igem.literature.search",
    title="Search literature sources",
    description="Search OpenAlex, Crossref, or Elsevier Scopus and optionally write a manifest CSV.",
    input_schema=_schema(
        {
            "query": {"type": "string"},
            "providers": {"type": "array", "items": {"type": "string"}},
            "output_manifest": {"type": "string"},
            "max_results": {"type": "integer", "minimum": 1},
            "from_year": {"type": "integer"},
            "to_year": {"type": "integer"},
            "mailto": {"type": "string"},
            "api_key_env": {"type": "string"},
        },
        ["query"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "result_count": {"type": "integer"}, "results": {"type": "array"}},
        additional_properties=True,
    ),
)

LITERATURE_EXTRACT_RECORDS_TOOL = McpTool(
    name="igem.literature.extract_records",
    title="Extract literature records",
    description="Call an OpenAI-compatible chat endpoint and parse JSON experimental records.",
    input_schema=_schema(
        {
            "text": {"type": "string"},
            "text_file": {"type": "string"},
            "schema_path": {"type": "string"},
            "icl_bank": {"type": "string"},
            "top_k": {"type": "integer", "minimum": 0},
            "api_key_env": {"type": "string", "default": "DEEPSEEK_API_KEY"},
            "api_base": {"type": "string"},
            "model": {"type": "string"},
            "temperature": {"type": "number"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
            "retries": {"type": "integer", "minimum": 1},
            "output_path": {"type": "string"},
        },
        ["schema_path", "api_base", "model"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "records": {"type": "array"}, "record_count": {"type": "integer"}},
        additional_properties=True,
    ),
)

ELSEVIER_SEARCH_TOOL = McpTool(
    name="igem.elsevier.search_scopus",
    title="Search Elsevier Scopus",
    description="Search Scopus through Elsevier API using an API key from an environment variable.",
    input_schema=_schema(
        {
            "query": {"type": "string"},
            "count": {"type": "integer", "minimum": 1},
            "api_key_env": {"type": "string", "default": "ELSEVIER_API_KEY"},
        },
        ["query"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "entries": {"type": "array"}, "count": {"type": "integer"}},
        additional_properties=True,
    ),
)

ELSEVIER_FETCH_ARTICLE_TEXT_TOOL = McpTool(
    name="igem.elsevier.fetch_article_text",
    title="Fetch Elsevier article text",
    description="Fetch article XML by DOI or PII through Elsevier API and extract plain text.",
    input_schema=_schema(
        {
            "doi": {"type": "string"},
            "pii": {"type": "string"},
            "api_key_env": {"type": "string", "default": "ELSEVIER_API_KEY"},
        }
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "text": {"type": "string"}, "character_count": {"type": "integer"}},
        additional_properties=True,
    ),
)

TOOL_BINDINGS: list[tuple[McpTool, ToolHandler]] = [
    (PIPELINE_VALIDATE_TOOL, pipeline_validate),
    (PIPELINE_RUN_TOOL, pipeline_run),
    (COMPUTE_CHECK_TOOL, compute_check_tool),
    (COMPUTE_RUN_TOOL, compute_run_tool),
    (MULTICHAIN_BUILD_INPUT_TOOL, multichain_build_input),
    (MULTICHAIN_BINDING_EQUILIBRIUM_TOOL, multichain_binding_equilibrium),
    (MULTICHAIN_ASSESS_INTERFACE_TOOL, multichain_assess_interface),
    (MULTICHAIN_EXPAND_FTH1_ARMS_TOOL, multichain_expand_fth1_arms),
    (SCORING_POCKET_SASA_TOOL, scoring_pocket_sasa),
    (SCORING_M2_STRUCTURE_TOOL, scoring_m2_structure),
    (PARSER_STRUCTURE_PREDICTION_TOOL, parser_structure_prediction),
    (PARSER_CALVADOS_TOOL, parser_calvados),
    (SCORING_DOCKING_PENALTY_TOOL, scoring_docking_penalty),
    (SCORING_M4_ODE_TOOL, scoring_m4_ode),
    (SCORING_M4_PIECEWISE_ODE_TOOL, scoring_m4_piecewise_ode),
    (LITERATURE_BUILD_PROMPT_TOOL, literature_build_prompt),
    (LITERATURE_BUILD_DATABASE_TOOL, literature_build_database),
    (LITERATURE_SEARCH_TOOL, literature_search),
    (LITERATURE_EXTRACT_RECORDS_TOOL, literature_extract_records),
    (ELSEVIER_SEARCH_TOOL, elsevier_search),
    (ELSEVIER_FETCH_ARTICLE_TEXT_TOOL, elsevier_fetch_article_text),
]
