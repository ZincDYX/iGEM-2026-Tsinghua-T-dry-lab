# LLPS-LKD-AI Agent external tool integration

## What changed

The Agent now has two layers:

1. External tool registry and executor
   - `CatalystOptimizationSystem/core/external_tools.py`
   - Probes local executables and optional network APIs.
   - Runs Boltz2, Mpipi, PSAP and AutoDock Vina when strict inputs and executables are available.
   - Redirects legacy `alphafold3` requests to Boltz2 so older calls do not break.
   - Returns `missing_input` or `missing_executable` instead of fabricating results.

2. Autonomous bounded Agent loop
   - `LkdAgent.agent_run(...)`
   - Chooses the next step from current state.
   - Records trace observations.
   - Checks tool availability before execution.
   - Runs external tools only with explicit inputs.
   - Produces final recommendations with missing-input and external-result provenance.

## HTTP APIs

### Check external tools

```http
POST /agent/external-tools
Content-Type: application/json

{
  "network": false
}
```

Use `"network": true` to also test DeepSeek, WOS Starter, Elsevier Scopus Search and Elsevier ScienceDirect Search.

### Run the autonomous Agent

```http
POST /agent/run
Content-Type: application/json

{
  "goal": "Design a substrate-sensing LLPS system for Glabridin in yeast",
  "top_k": 5,
  "max_steps": 10,
  "run_external": true,
  "network_check": false,
  "tool_inputs": {
    "boltz2": {
      "sequence": "MSEQUENCE...",
      "job_name": "GgDMT1_boltz2"
    },
    "psap": {
      "sequences": [
        {
          "id": "FUS_test",
          "sequence": "SYGQQSSYGQQSRGGRGGRGG"
        }
      ]
    }
  }
}
```

### Run one external tool

```http
POST /agent/run-external-tool
Content-Type: application/json

{
  "tool": "boltz2",
  "payload": {
    "sequence": "MSEQUENCE...",
    "job_name": "GgDMT1_boltz2"
  }
}
```

Valid tool names:

- `boltz2`
- `boltz`
- `alphafold3` legacy alias redirected to Boltz2
- `mpipi`
- `psap`
- `autodock_vina`

## Boltz2 configuration

Boltz is now the preferred local structure-prediction backend because it avoids the local AlphaFold3 database burden.

Recommended GPU installation:

```powershell
pip install boltz[cuda] -U
```

CPU-only installation is possible but much slower:

```powershell
pip install boltz -U
```

Default executable:

```powershell
$env:BOLTZ_COMMAND = "boltz"
```

The Agent writes a Boltz YAML file and runs:

```powershell
boltz predict input.yaml --out_dir output_dir --use_msa_server --use_potentials
```

If Boltz is installed in a conda environment or remote wrapper, configure a command template:

```powershell
$env:BOLTZ_COMMAND_TEMPLATE = "conda run -n boltz boltz predict {input_yaml} --out_dir {output_dir} --use_msa_server --use_potentials"
```

### Minimal protein input

```json
{
  "boltz2": {
    "sequence": "MSEQUENCE...",
    "job_name": "GgDMT1_boltz2"
  }
}
```

### Protein plus ligand input

```json
{
  "boltz2": {
    "chains": [
      {
        "id": "A",
        "sequence": "MSEQUENCE..."
      }
    ],
    "ligands": [
      {
        "id": "L",
        "smiles": "COc1cc(O)ccc1"
      }
    ],
    "predict_affinity_for": "L",
    "job_name": "DMT_glabridin_boltz2"
  }
}
```

### Legacy AlphaFold3 input

This still works, but is redirected to Boltz2:

```json
{
  "alphafold3": {
    "sequence": "MSEQUENCE...",
    "job_name": "legacy_request_redirected_to_boltz2"
  }
}
```

## Mpipi

```powershell
$env:MPIPI_COMMAND = "mpipi"
```

or:

```powershell
$env:MPIPI_COMMAND_TEMPLATE = "python D:\tools\mpipi\run_mpipi.py --input {input_fasta} --output {output_dir}"
```

## PSAP

```powershell
$env:PSAP_COMMAND = "psap"
```

or:

```powershell
$env:PSAP_COMMAND_TEMPLATE = "python D:\tools\psap\predict.py --input {input_fasta} --output {output_dir}"
```

## AutoDock Vina

```powershell
$env:VINA_COMMAND = "vina"
```

Required payload fields:

```json
{
  "receptor_pdbqt": "path/to/receptor.pdbqt",
  "ligand_pdbqt": "path/to/ligand.pdbqt",
  "center": {"x": 0, "y": 0, "z": 0},
  "size": {"x": 20, "y": 20, "z": 20},
  "exhaustiveness": 8
}
```

## Why this is now an Agent rather than only a pipeline

The previous `design()` method was a deterministic pipeline:

```text
evidence -> components -> constructs -> screen -> partition
```

The new `agent_run()` method is a bounded agent loop:

```text
goal
-> choose next action from current state
-> call retrieval/tool/scoring module
-> observe result
-> decide whether inputs are missing or execution can continue
-> continue until recommendation is ready
```

Agentic properties now implemented:

- Goal-conditioned execution.
- Tool registry and executable probing.
- Conditional external tool calling.
- Missing-input tracking.
- Traceable observation log.
- No fabricated outputs for missing Boltz2/Mpipi/PSAP/Vina results.

## Current local test result

In the tested local environment before installing Boltz:

- DeepSeek API: callable.
- WOS Starter API: callable.
- Elsevier Scopus Search API: callable.
- Elsevier ScienceDirect Search API: reachable but unauthorized.
- Boltz2 executable: missing.
- Mpipi executable: missing.
- PSAP executable: missing.
- AutoDock Vina executable: missing.

Therefore the code path is implemented and tested, but strict external computation will produce real results only after those tools are installed or command templates are configured.
