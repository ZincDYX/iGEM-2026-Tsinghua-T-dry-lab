from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_API_TXT = PROJECT_ROOT / "API.txt"
DEFAULT_AGENT_RUN_ROOT = PROJECT_ROOT / "agent_runs"


def _mask(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def _read_api_config(api_txt: str | None = None) -> dict[str, Any]:
    path = Path(api_txt) if api_txt else DEFAULT_API_TXT
    result: dict[str, Any] = {"path": str(path), "exists": path.exists(), "keys": {}}
    if not path.exists():
        return result
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        match = re.match(r"([A-Za-z0-9_\-]+)\s*=\s*['\"]?([^'\"]+)", item)
        if not match:
            match = re.match(r"([A-Za-z0-9_\-]+)\s*[:]\s*['\"]?([^'\"]+)", item)
        if not match:
            continue
        name, value = match.group(1), match.group(2).strip()
        result["keys"][name] = {
            "present": bool(value),
            "length": len(value),
            "masked": _mask(value),
        }
    return result


def _get_secret(api_txt: str | None, name: str) -> str | None:
    path = Path(api_txt) if api_txt else DEFAULT_API_TXT
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(rf"{re.escape(name)}\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else None


def _check_packages() -> dict[str, bool]:
    packages = [
        "pandas",
        "numpy",
        "sklearn",
        "scipy",
        "requests",
        "openpyxl",
        "docx",
        "pypdf",
        "matplotlib",
        "seaborn",
        "freesasa",
        "Bio",
    ]
    return {name: importlib.util.find_spec(name) is not None for name in packages}


def _resolve_command(command: str | None, default_exe: str) -> dict[str, Any]:
    raw = (command or default_exe).strip()
    if not raw:
        return {"raw": raw, "executable": "", "available": False, "path": None}
    parts = shlex.split(raw, posix=False)
    exe = parts[0] if parts else raw
    path = shutil.which(exe)
    return {"raw": raw, "executable": exe, "available": path is not None, "path": path}


def _check_commands() -> dict[str, dict[str, Any]]:
    specs = {
        "boltz2": (os.getenv("BOLTZ_COMMAND"), "boltz"),
        "alphafold3_legacy": (os.getenv("AF3_COMMAND"), "alphafold3"),
        "mpipi": (os.getenv("MPIPI_COMMAND"), "mpipi"),
        "psap": (os.getenv("PSAP_COMMAND"), "psap"),
        "autodock_vina": (os.getenv("VINA_COMMAND"), "vina"),
        "openbabel": (os.getenv("OBABEL_COMMAND"), "obabel"),
        "python": (None, "python"),
        "git": (None, "git"),
    }
    return {name: _resolve_command(cmd, default) for name, (cmd, default) in specs.items()}


def _safe_id(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text or "job").strip("_")
    return text[:80] or "job"


def _prepare_output_dir(output_dir: str | Path | None, run_root: Path, job_name: str) -> tuple[Path, dict[str, Any] | None]:
    output = Path(output_dir) if output_dir else run_root / _safe_id(job_name)
    try:
        output.mkdir(parents=True, exist_ok=True)
        return output, None
    except PermissionError as ex:
        fallback = Path(tempfile.gettempdir()) / "CatalystOptimizationSystem_agent_runs" / _safe_id(job_name)
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback, {
            "requested_output_dir": str(output),
            "fallback_output_dir": str(fallback),
            "reason": f"permission denied: {ex}",
        }


def _run_process(args: list[str], cwd: str | Path | None = None, timeout: int = 900) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "elapsed_s": round(time.time() - started, 2),
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
            "command": args[:1] + ["<args_hidden>" if len(args) > 1 else ""],
        }
    except FileNotFoundError as ex:
        return {
            "ok": False,
            "error_type": "FileNotFoundError",
            "error": str(ex),
            "elapsed_s": round(time.time() - started, 2),
            "command": args[:1],
        }
    except subprocess.TimeoutExpired as ex:
        return {
            "ok": False,
            "error_type": "TimeoutExpired",
            "error": str(ex),
            "elapsed_s": round(time.time() - started, 2),
            "command": args[:1],
        }


def _version_check(tool_name: str, command: str | None, default_exe: str, version_args: str = "--version") -> dict[str, Any]:
    resolved = _resolve_command(command, default_exe)
    item = {
        "tool": tool_name,
        "command": resolved["raw"],
        "available": resolved["available"],
        "path": resolved["path"],
    }
    if not resolved["available"]:
        item.update({"callable": False, "status": "missing_executable"})
        return item
    args = shlex.split(resolved["raw"], posix=False) + shlex.split(version_args, posix=False)
    probe = _run_process(args, timeout=30)
    item.update({"callable": bool(probe["ok"]), "status": "ok" if probe["ok"] else "probe_failed", "probe": probe})
    return item


def _request_json(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    import requests

    started = time.time()
    try:
        if method.upper() == "POST":
            response = requests.post(url, timeout=kwargs.pop("timeout", 30), **kwargs)
        else:
            response = requests.get(url, timeout=kwargs.pop("timeout", 30), **kwargs)
        item: dict[str, Any] = {
            "status_code": response.status_code,
            "ok": response.ok,
            "elapsed_s": round(time.time() - started, 2),
            "content_type": response.headers.get("content-type", "")[:80],
        }
        if response.ok:
            try:
                item["json_keys"] = list(response.json().keys())[:8]
            except Exception:
                item["body_prefix"] = response.text[:120]
        else:
            item["body_prefix"] = response.text[:240]
        return item
    except Exception as ex:
        return {
            "ok": False,
            "error_type": type(ex).__name__,
            "error": str(ex)[:240],
            "elapsed_s": round(time.time() - started, 2),
        }


def _network_checks(api_txt: str | None = None) -> dict[str, Any]:
    elsevier = _get_secret(api_txt, "ELSEVIER_API_KEY")
    deepseek = _get_secret(api_txt, "DEEPSEEK_API_KEY")
    wos = _get_secret(api_txt, "WOS_API_KEY")
    checks: dict[str, Any] = {}

    if elsevier:
        headers = {"X-ELS-APIKey": elsevier, "Accept": "application/json"}
        checks["elsevier_scopus_search"] = _request_json(
            "GET",
            "https://api.elsevier.com/content/search/scopus",
            headers=headers,
            params={"query": "TITLE-ABS-KEY(glabridin)", "count": 1},
        )
        checks["elsevier_sciencedirect_search"] = _request_json(
            "GET",
            "https://api.elsevier.com/content/search/sciencedirect",
            headers=headers,
            params={"query": "glabridin", "count": 1},
        )
    else:
        checks["elsevier"] = {"ok": False, "error": "ELSEVIER_API_KEY missing"}

    if wos:
        checks["wos_starter_search"] = _request_json(
            "GET",
            "https://api.clarivate.com/apis/wos-starter/v1/documents",
            headers={"X-ApiKey": wos, "Accept": "application/json"},
            params={"db": "WOS", "q": "TS=(glabridin)", "limit": 1, "page": 1},
        )
    else:
        checks["wos_starter_search"] = {"ok": False, "error": "WOS_API_KEY missing"}

    if deepseek:
        checks["deepseek_chat"] = _request_json(
            "POST",
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {deepseek}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Return exactly OK."}],
                "max_tokens": 4,
                "temperature": 0,
            },
        )
    else:
        checks["deepseek_chat"] = {"ok": False, "error": "DEEPSEEK_API_KEY missing"}
    return checks


@dataclass(frozen=True)
class ExternalToolRegistry:
    run_root: Path = DEFAULT_AGENT_RUN_ROOT

    def health(self, network: bool = False, api_txt: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "api_config": _read_api_config(api_txt),
            "files": {
                "api_txt": {"path": str(Path(api_txt) if api_txt else DEFAULT_API_TXT), "exists": (Path(api_txt) if api_txt else DEFAULT_API_TXT).exists()},
                "project_conditioned_evidence_database": {
                    "path": str(PROJECT_ROOT / "essay" / "project_conditioned_evidence_database.csv"),
                    "exists": (PROJECT_ROOT / "essay" / "project_conditioned_evidence_database.csv").exists(),
                },
                "lkd_agent_module": {
                    "path": str(PROJECT_ROOT / "CatalystOptimizationSystem" / "core" / "lkd_agent.py"),
                    "exists": (PROJECT_ROOT / "CatalystOptimizationSystem" / "core" / "lkd_agent.py").exists(),
                },
            },
            "python_packages": _check_packages(),
            "commands": _check_commands(),
            "external_tool_probes": {
                "boltz2": _version_check(
                    "boltz2",
                    os.getenv("BOLTZ_COMMAND"),
                    "boltz",
                    os.getenv("BOLTZ_VERSION_ARGS", "--version"),
                ),
                "alphafold3_legacy": _version_check(
                    "alphafold3_legacy",
                    os.getenv("AF3_COMMAND"),
                    "alphafold3",
                    os.getenv("AF3_VERSION_ARGS", "--version"),
                ),
                "mpipi": _version_check("mpipi", os.getenv("MPIPI_COMMAND"), "mpipi", os.getenv("MPIPI_VERSION_ARGS", "--version")),
                "psap": _version_check("psap", os.getenv("PSAP_COMMAND"), "psap", os.getenv("PSAP_VERSION_ARGS", "--version")),
                "autodock_vina": _version_check(
                    "autodock_vina",
                    os.getenv("VINA_COMMAND"),
                    "vina",
                    os.getenv("VINA_VERSION_ARGS", "--version"),
                ),
            },
            "network_checked": bool(network),
            "network_services": _network_checks(api_txt) if network else {},
        }
        return json.loads(json.dumps(result, ensure_ascii=False))

    def run_boltz2(
        self,
        sequence: str = "",
        chains: list[dict[str, Any]] | None = None,
        ligands: list[dict[str, Any]] | None = None,
        job_name: str = "boltz2_job",
        output_dir: str | Path | None = None,
        command_template: str | None = None,
        use_msa_server: bool = True,
        use_potentials: bool = True,
        accelerator: str | None = None,
        recycling_steps: int | None = None,
        diffusion_samples: int | None = None,
        predict_affinity_for: str | None = None,
        timeout: int = 7200,
    ) -> dict[str, Any]:
        chains = chains or []
        if sequence and not chains:
            chains = [{"id": "A", "sequence": sequence}]
        if not chains:
            return {"ok": False, "status": "missing_input", "error": "sequence or chains are required"}
        output, fallback_note = _prepare_output_dir(output_dir, self.run_root, job_name)
        input_yaml = output / f"{_safe_id(job_name)}.boltz2.yaml"
        yaml_lines = ["version: 1", "sequences:"]
        for idx, chain in enumerate(chains, 1):
            seq = re.sub(r"[^A-Za-z]", "", str(chain.get("sequence", ""))).upper()
            if not seq:
                continue
            chain_id = chain.get("id") or chr(ord("A") + idx - 1)
            yaml_lines.extend([
                "  - protein:",
                f"      id: {chain_id}",
                f"      sequence: {seq}",
            ])
            msa = chain.get("msa")
            if msa:
                yaml_lines.append(f"      msa: {msa}")
        for idx, ligand in enumerate(ligands or [], 1):
            ligand_id = ligand.get("id") or chr(ord("L") + idx - 1)
            yaml_lines.extend(["  - ligand:", f"      id: {ligand_id}"])
            if ligand.get("smiles"):
                yaml_lines.append(f"      smiles: '{str(ligand.get('smiles')).replace(chr(39), chr(39)+chr(34)+chr(39)+chr(34)+chr(39))}'")
            elif ligand.get("ccd"):
                yaml_lines.append(f"      ccd: {ligand.get('ccd')}")
            else:
                return {"ok": False, "status": "missing_input", "error": "each ligand needs smiles or ccd"}
        if predict_affinity_for:
            yaml_lines.extend(["properties:", "  - affinity:", f"      binder: {predict_affinity_for}"])
        input_yaml.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

        template = command_template or os.getenv("BOLTZ_COMMAND_TEMPLATE")
        if template:
            cmd = template.format(input_yaml=str(input_yaml), input_path=str(input_yaml), output_dir=str(output))
            args = shlex.split(cmd, posix=False)
        else:
            resolved = _resolve_command(os.getenv("BOLTZ_COMMAND"), "boltz")
            if not resolved["available"]:
                return {
                    "ok": False,
                    "status": "missing_executable",
                    "tool": "boltz2",
                    "input_yaml": str(input_yaml),
                    "output_dir": str(output),
                    "hint": "Install boltz or set BOLTZ_COMMAND/BOLTZ_COMMAND_TEMPLATE.",
                }
            args = shlex.split(resolved["raw"], posix=False) + ["predict", str(input_yaml), "--out_dir", str(output)]
            if use_msa_server:
                args.append("--use_msa_server")
            if use_potentials:
                args.append("--use_potentials")
            if accelerator:
                args.extend(["--accelerator", str(accelerator)])
            if recycling_steps is not None:
                args.extend(["--recycling_steps", str(recycling_steps)])
            if diffusion_samples is not None:
                args.extend(["--diffusion_samples", str(diffusion_samples)])
        result = _run_process(args, cwd=output, timeout=timeout)
        result.update({"tool": "boltz2", "input_yaml": str(input_yaml), "output_dir": str(output)})
        if fallback_note:
            result["output_dir_fallback"] = fallback_note
        return result

    def run_alphafold3(self, **kwargs: Any) -> dict[str, Any]:
        result = self.run_boltz2(**kwargs)
        result["requested_tool"] = "alphafold3"
        result["compatibility_note"] = "AlphaFold3 calls are redirected to Boltz2 in this project configuration."
        return result

    def run_phase_predictor(
        self,
        tool: str,
        sequences: list[dict[str, str]] | None = None,
        job_name: str = "phase_job",
        output_dir: str | Path | None = None,
        command_template: str | None = None,
        timeout: int = 1800,
    ) -> dict[str, Any]:
        tool = tool.lower().strip()
        if tool not in {"mpipi", "psap"}:
            return {"ok": False, "status": "unsupported_tool", "error": "tool must be mpipi or psap"}
        sequences = sequences or []
        if not sequences:
            return {"ok": False, "status": "missing_input", "error": "sequences are required"}
        output, fallback_note = _prepare_output_dir(output_dir, self.run_root, job_name)
        fasta = output / f"{_safe_id(job_name)}.{tool}.fasta"
        lines = []
        for idx, item in enumerate(sequences, 1):
            seq = re.sub(r"[^A-Za-z]", "", item.get("sequence", "")).upper()
            if not seq:
                continue
            lines.extend([f">{_safe_id(item.get('id') or item.get('name') or f'seq{idx}')}", seq])
        if not lines:
            return {"ok": False, "status": "missing_input", "error": "no valid sequence after cleaning"}
        fasta.write_text("\n".join(lines) + "\n", encoding="utf-8")

        env_prefix = tool.upper()
        template = command_template or os.getenv(f"{env_prefix}_COMMAND_TEMPLATE")
        if template:
            cmd = template.format(input_fasta=str(fasta), output_dir=str(output))
            args = shlex.split(cmd, posix=False)
        else:
            resolved = _resolve_command(os.getenv(f"{env_prefix}_COMMAND"), tool)
            if not resolved["available"]:
                return {
                    "ok": False,
                    "status": "missing_executable",
                    "tool": tool,
                    "input_fasta": str(fasta),
                    "output_dir": str(output),
                    "hint": f"Set {env_prefix}_COMMAND or {env_prefix}_COMMAND_TEMPLATE.",
                }
            args = shlex.split(resolved["raw"], posix=False) + ["--input", str(fasta), "--output", str(output)]
        result = _run_process(args, cwd=output, timeout=timeout)
        result.update({"tool": tool, "input_fasta": str(fasta), "output_dir": str(output)})
        if fallback_note:
            result["output_dir_fallback"] = fallback_note
        return result

    def run_vina(
        self,
        receptor_pdbqt: str = "",
        ligand_pdbqt: str = "",
        center: dict[str, float] | None = None,
        size: dict[str, float] | None = None,
        job_name: str = "vina_job",
        output_dir: str | Path | None = None,
        exhaustiveness: int = 8,
        timeout: int = 1800,
    ) -> dict[str, Any]:
        center = center or {}
        receptor = Path(receptor_pdbqt) if receptor_pdbqt else Path()
        ligand = Path(ligand_pdbqt) if ligand_pdbqt else Path()
        missing = [name for name, path in {"receptor_pdbqt": receptor, "ligand_pdbqt": ligand}.items() if not path.exists()]
        if missing:
            return {"ok": False, "status": "missing_input", "missing": missing}
        resolved = _resolve_command(os.getenv("VINA_COMMAND"), "vina")
        if not resolved["available"]:
            return {"ok": False, "status": "missing_executable", "tool": "autodock_vina", "hint": "Install vina or set VINA_COMMAND."}

        size = size or {"x": 20.0, "y": 20.0, "z": 20.0}
        output, fallback_note = _prepare_output_dir(output_dir, self.run_root, job_name)
        out_pdbqt = output / f"{_safe_id(job_name)}_out.pdbqt"
        log_path = output / f"{_safe_id(job_name)}.log"
        args = shlex.split(resolved["raw"], posix=False) + [
            "--receptor", str(receptor),
            "--ligand", str(ligand),
            "--center_x", str(center.get("x", 0)),
            "--center_y", str(center.get("y", 0)),
            "--center_z", str(center.get("z", 0)),
            "--size_x", str(size.get("x", 20)),
            "--size_y", str(size.get("y", 20)),
            "--size_z", str(size.get("z", 20)),
            "--exhaustiveness", str(exhaustiveness),
            "--out", str(out_pdbqt),
            "--log", str(log_path),
        ]
        result = _run_process(args, cwd=output, timeout=timeout)
        result.update({"tool": "autodock_vina", "output_pdbqt": str(out_pdbqt), "log_path": str(log_path)})
        if fallback_note:
            result["output_dir_fallback"] = fallback_note
        return result

    def run_requested_tools(self, tool_inputs: dict[str, Any], run_external: bool = True) -> dict[str, Any]:
        if not run_external:
            return {"run_external": False, "results": {}, "note": "external execution disabled"}
        tool_inputs = tool_inputs or {}
        results: dict[str, Any] = {}
        if "boltz2" in tool_inputs:
            boltz = tool_inputs["boltz2"] or {}
            results["boltz2"] = self.run_boltz2(**boltz)
        if "boltz" in tool_inputs:
            boltz = tool_inputs["boltz"] or {}
            results["boltz2"] = self.run_boltz2(**boltz)
        if "alphafold3" in tool_inputs:
            af3 = tool_inputs["alphafold3"] or {}
            results["boltz2"] = self.run_alphafold3(**af3)
        if "mpipi" in tool_inputs:
            mpipi = tool_inputs["mpipi"] or {}
            results["mpipi"] = self.run_phase_predictor("mpipi", **mpipi)
        if "psap" in tool_inputs:
            psap = tool_inputs["psap"] or {}
            results["psap"] = self.run_phase_predictor("psap", **psap)
        if "autodock_vina" in tool_inputs:
            vina = tool_inputs["autodock_vina"] or {}
            results["autodock_vina"] = self.run_vina(**vina)
        return {"run_external": True, "results": results}


def check_external_tools(api_txt: str | None = None, network: bool = False) -> dict[str, Any]:
    return ExternalToolRegistry().health(network=network, api_txt=api_txt)
