"""Persist real sequence-tool jobs using the existing private runtime adapter.

These are diagnostic tool tasks, not automatic approval of M1 or M2. The
workflow owns snapshots/recovery; tool deployment settings never come from
node inputs, Agent prose or the browser.
"""
from hashlib import sha256
import json
from pathlib import Path
from pydantic import Field

from igem_drylab.constructs.linker_features import parse_iupred2a_output, parse_seg_fasta, parse_secondary_structure_output
from igem_drylab.parsers.structure_prediction import parse_colabfold_models
from igem_drylab.pipeline.adapters import create_tool_adapter
from igem_drylab.pipeline.config import ToolConfig
from .models import Contract, SequenceRecord
from .tools import NodeContext, ToolDefinition, ToolDeferred, ToolFailure


def uses_native_jpred_route(config):
    return uses_native_route(config, "jpred_runner")


def uses_native_route(config, module):
    from igem_drylab.pipeline.adapters import _split_command
    if not config.command:
        return False
    command=_split_command(config.command)
    return any(command[index:index+2]==["-m","igem_drylab."+module] for index in range(len(command)-1))


def reconcile_catgranule(node_directory):
    state_file = node_directory / "remote-job.json"
    if not state_file.is_file():
        return False
    state = json.loads(state_file.read_text())
    if state.get("protocol") != "catgranule2016-official-form-v1":
        return False
    if state.get("job_id"):
        return True
    ack = Path(state["acknowledgement_file"])
    if not ack.is_file():
        return False
    from igem_drylab.catgranule_runner import _accepted
    try:
        _accepted(json.loads(ack.read_text()))
    except (ValueError, KeyError):
        return False
    return True


def reconcile_jpred(node_directory):
    state_file = node_directory / "remote-job.json"
    if not state_file.is_file():
        return False
    state = json.loads(state_file.read_text())
    # This native protocol cannot submit again when an intent exists, including
    # unknown acknowledgements. Other arbitrary configured commands get no
    # automatic recovery permission from merely writing a job-id-shaped string.
    if state.get("protocol") != "jpred-known-job-v2":
        return False
    if state.get("job_id"):
        return True
    from igem_drylab.jpred_runner import _accepted_job
    log = Path(state["acknowledgement_log"])
    if not log.is_file():
        return False
    try:
        _accepted_job(log.read_text())
    except ValueError:
        return False
    return True


class SequencePredictionInput(Contract):
    item: SequenceRecord
    prechecks: list[dict] = Field(default_factory=list)


def predict_sequence(tool: str, payload: SequencePredictionInput, context: NodeContext) -> dict:
    sequence = payload.item.sequence
    digest = sha256(sequence.encode()).hexdigest()
    config = ToolConfig.model_validate(context.runtime_tools.get(tool, {}))
    adapter = create_tool_adapter(tool, config)
    result = dict(schema_version="sequence-prediction-v1", candidate_id=payload.item.id,
        tool_input_id="sequence_input",
        tool=tool, input_sequence_sha256=digest, sequence_length=len(sequence),
        tool_status="not_configured", parse_status="not_run", outputs={}, parsed=None,
        scientific_status="diagnostic_not_formal_M1_M2_acceptance")
    fusion_tool = tool in {"signalp","deeptmhmm","tango"}
    if fusion_tool and payload.item.role != "full_fusion":
        result.update(tool_status="not_eligible",blocker="Full-fusion predictors require the complete actual fusion sequence.")
        return result
    if tool == "catgranule" and payload.item.role != "idr":
        result.update(tool_status="not_eligible", blocker="The original M1 LLPS ranking route applies to explicitly bound IDRs.")
        return result
    if payload.prechecks:
        matching = [row for row in payload.prechecks if row.get("candidate_id") == payload.item.id]
        if len(matching) != 1 or matching[0].get("input_sequence_sha256") != digest:
            raise ValueError("prediction_precheck_sequence_identity_mismatch")
        if not matching[0].get("eligible_for_tools"):
            result.update(tool_status="not_eligible", blocker="M1 cheap veto, explicit role missing, or full-fusion-specific tools required.")
            return result
    if not adapter.is_available():
        result["blocker"] = "Configure an authorized external route in the private backend runtime profile."
        return result
    if tool == "pscore" and len(sequence) < 140:
        result.update(tool_status="not_eligible", blocker="Original PScore requires at least 140 residues; no padding or sequence repetition is allowed.")
        return result
    if tool == "jpred" and not 20 <= len(sequence) <= 800:
        result.update(tool_status="not_eligible", blocker="JPred requires 20–800 residues; the original sequence is not padded or cropped.")
        return result
    source = context.work_dir / "input.fasta"
    # Keep arbitrary user labels out of external-tool argv and output paths.
    # The fixed IO identifier is explicitly mapped to the original candidate;
    # the full biological sequence and its identity are unchanged.
    source.write_text(f">sequence_input\n{sequence}\n", encoding="utf-8")
    output_dir = context.work_dir / "prediction"
    if tool == "jpred":
        native = uses_native_jpred_route(config)
        if not native:
            raise ToolFailure("jpred_requires_recoverable_native_route", "A submit-only or arbitrary command cannot recover a JPred job. Configure the native JPred runner with the official client.")
        config = config.model_copy(update={"command":config.command + " --poll-once"})
        adapter = create_tool_adapter(tool, config)
    if tool == "catgranule" and not uses_native_route(config, "catgranule_runner"):
        raise ToolFailure("catgranule_requires_recoverable_native_route", "Use the original web-form runner; unknown submissions must not be repeated.")
    run = adapter.run(output_dir=output_dir, fasta=source, record="sequence_input",
        sequence=sequence,
        job_state=context.work_dir.parent / "remote-job.json",
        input_files={"sequence": source}, timeout_seconds=7200)
    result["tool_status"] = run.status
    if run.status != "succeeded":
        if tool == "catgranule":
            if not reconcile_catgranule(context.work_dir.parent):
                raise ToolFailure("remote_submission_reconciliation_required", "Original service acknowledgement unknown; do not resubmit.")
            raise ToolFailure("remote_retrieval_failed", "Retrieve only the saved original catGRANULE job.", retryable=True)
        if tool == "jpred" and native:
            state_file = context.work_dir.parent / "remote-job.json"
            if state_file.is_file() and not json.loads(state_file.read_text()).get("job_id"):
                raise ToolFailure("remote_submission_reconciliation_required", "Submission acknowledgement unknown; never resubmit blindly.")
            raise ToolFailure("remote_retrieval_failed", "Original JPred job retained; retry retrieves that job only.",retryable=True)
        result["blocker"] = "External tool did not complete; its private execution record is retained."
        return result
    if tool == "jpred" and native and not (output_dir / "secondary.json").is_file():
        state = json.loads((context.work_dir.parent / "remote-job.json").read_text())
        if state["status"] == "waiting_for_result":
            raise ToolDeferred(state["job_id"],poll_after_seconds=60)
        raise ValueError("JPred returned neither validated results nor a known waiting job")
    if tool == "catgranule" and not (output_dir / "scores.run.json").is_file():
        state = json.loads((context.work_dir.parent / "remote-job.json").read_text())
        if state["status"] == "waiting_for_result":
            raise ToolDeferred(state["job_id"], poll_after_seconds=60)
        raise ValueError("catGRANULE returned neither validated original results nor a known waiting job")
    parsed = None
    if fusion_tool:
        from igem_drylab.fusion_tool_import import NativeFusionArtifact, parse_native_artifact
        from igem_drylab.constructs.linker_features import FusionToolEvidence
        from igem_drylab.constructs.tool_evidence import ToolEvidenceProvenance
        names = {"signalp":("SignalP","signalp","signalp6_summary","prediction_results.txt"),
            "deeptmhmm":("DeepTMHMM","deeptmhmm","deeptmhmm1_3line","predicted_topologies.3line"),
            "tango":("TANGO","aggregation","tango_residue_out","sequence_input.out")}
        name,prefix,format,filename = names[tool]
        if not config.verified_version:
            result.update(parse_status="blocked",blocker="Record the actual installed tool version before importing predictions.")
            return result
        output = output_dir/filename
        artifact = NativeFusionArtifact(path=output,tool_version=config.verified_version,format=format,
            record_id="sequence_input",aggregation_rule=config.extra.get("aggregation_rule") if tool=="tango" else None)
        observations = parse_native_artifact(artifact,sequence)
        record_path = output.with_suffix(".run.json")
        record = dict(tool_name=name,tool_version=config.verified_version,origin="automated",returncode=run.return_code,
            command=run.argv,input_sha256=digest,output_sha256=sha256(output.read_bytes()).hexdigest(),
            record_id="sequence_input",native_format=format,aggregation_rule=artifact.aggregation_rule.model_dump() if artifact.aggregation_rule else None)
        record_path.write_text(json.dumps(record,indent=2),encoding="utf-8")
        evidence = FusionToolEvidence(input_sha256=digest,
            provenance={name:ToolEvidenceProvenance(origin="automated",output_sha256=record["output_sha256"],
                record_file=record_path,record_sha256=sha256(record_path.read_bytes()).hexdigest())},
            native_formats={name:format},native_rules={name:record["aggregation_rule"]},**observations,
            **{prefix+"_source_file":output,prefix+"_tool_version":config.verified_version})
        if tool=="tango":
            evidence.aggregation_tool="TANGO"
        parsed = evidence.model_dump(mode="json")
        result["outputs"] = {"raw_output":str(output),"execution_record":str(record_path)}
    elif tool == "colabfold":
        from Bio.PDB import PDBParser
        from Bio.SeqUtils import seq1
        summaries = parse_colabfold_models(output_dir, candidate_id="sequence_input")
        for row in summaries:
            model = PDBParser(QUIET=True).get_structure(payload.item.id, row.model_file)
            observed = "".join(seq1(residue.resname) for residue in next(model.get_models()).get_residues() if residue.id[0] == " ")
            if observed != sequence or row.residue_count != len(sequence):
                raise ValueError("predicted structure does not match complete input sequence")
        parsed = [row.model_copy(update={"candidate_id": payload.item.id}).model_dump(mode="json") for row in summaries]
        result["outputs"] = {f"model_{row['model_rank']}": row["model_file"] for row in parsed}
        result["outputs"].update({f"confidence_{row['model_rank']}": row["confidence_file"] for row in parsed})
    elif tool == "jpred":
        evidence = json.loads((output_dir / "secondary.json").read_text())
        output = Path(evidence["source_file"])
        parsed = parse_secondary_structure_output(output, tool_name="JPred", tool_version=evidence["tool_version"],
            input_sha256=digest, sequence_file=Path(evidence["sequence_file"])).model_dump(mode="json")
        result["outputs"] = {"raw_output": str(output), "sequence_companion": evidence["sequence_file"]}
    elif tool == "pscore":
        from igem_drylab.pscore_runner import parse_pscore_output
        output = output_dir / "pscore.txt"
        parsed = parse_pscore_output(output, sequence=sequence)
        from igem_drylab.llps_artifacts import automated_predictor_score
        parsed["predictor_scores"] = [automated_predictor_score(output, tool="PScore", sequence=sequence,
            raw_score=parsed["pscore"]).model_dump(mode="json")]
        result["outputs"] = {"raw_output": str(output)}
    elif tool == "catgranule":
        from igem_drylab.llps_artifacts import read_native_llps, automated_predictor_score
        output = output_dir / "scores.txt"
        parsed = read_native_llps(output, format="catgranule2016_scores", sequence=sequence,
            sequence_file=output_dir/"prot.fa", profile_file=output_dir/"profiles.txt")
        parsed["predictor_scores"] = [automated_predictor_score(output, tool="catGRANULE_2016", sequence=sequence,
            raw_score=parsed["raw_score"]).model_dump(mode="json")]
        result["outputs"] = {"raw_output": str(output), "sequence_companion": str(output_dir/"prot.fa"),
            "native_profile": str(output_dir/"profiles.txt")}
    else:
        output = output_dir / ("iupred2a.txt" if tool == "iupred2a" else "seg.fasta")
        if not output.is_file():
            output.write_text(run.stdout, encoding="utf-8")
        result["outputs"] = {"raw_output": str(output)}
        if tool == "iupred2a":
            record = output.with_suffix(".run.json")
            if not record.is_file():
                result["parse_status"] = "blocked"
                result["blocker"] = "IUPred route must produce a versioned execution record, for example igem_drylab.iupred_runner."
                return result
            version = json.loads(record.read_text())["tool_version"]
            parsed = parse_iupred2a_output(output, tool_version=version, input_sha256=digest).model_dump(mode="json")
        else:
            version = config.verified_version
            if not version:
                result["parse_status"] = "blocked"
                result["blocker"] = "Backend deployment has not recorded the actual SEG version."
                return result
            output.with_suffix(".run.json").write_text(json.dumps(dict(tool_name="SEG", tool_version=version,
                input_sha256=digest, output_sha256=sha256(output.read_bytes()).hexdigest(), origin="automated",
                command=run.argv, returncode=run.return_code)), encoding="utf-8")
            parsed = parse_seg_fasta(output, tool_version=version, input_sha256=digest,
                expected_length=len(sequence)).model_dump(mode="json")
    result.update(parse_status="succeeded", parsed=parsed)
    return result


def sequence_prediction_tools():
    # Distinct resource declarations share a single adapter/parser path.
    def handler(tool):
        def invoke(payload, context):
            return predict_sequence(tool, payload, context)
        return invoke
    implementation = (Path(__file__), Path(__file__).parents[1] / "pipeline/adapters.py",
        Path(__file__).parents[1] / "constructs/linker_features.py",
        Path(__file__).parents[1] / "parsers/structure_prediction.py",
        Path(__file__).parents[1] / "pscore_runner.py", Path(__file__).parents[1] / "jpred_runner.py",
        Path(__file__).parents[1] / "fusion_tool_import.py",Path(__file__).parents[1]/"tango_runner.py",
        Path(__file__).parents[1] / "deeptmhmm_runner.py",
        Path(__file__).parents[1] / "iupred_runner.py")
    implementation += (Path(__file__).parents[1]/"llps_artifacts.py", Path(__file__).parents[1]/"catgranule_runner.py")
    return [ToolDefinition(f"prediction.{name}", label, "Real diagnostic sequence prediction using a private configured route; no scientific approval.",
        "1", SequencePredictionInput, handler(name), "scientific_project",
        implementation_files=implementation, resource="gpu" if name == "colabfold" else "cpu", idempotent=False,
        reconcile=reconcile_jpred if name == "jpred" else reconcile_catgranule if name == "catgranule" else None)
        for name, label in (("iupred2a", "IUPred2 disorder prediction"), ("seg", "SEG low-complexity prediction"),
                            ("colabfold", "ColabFold enzyme / fusion prediction"),
                            ("pscore", "Original PScore — diagnostic LLPS propensity"),
                            ("jpred", "JPred — exact-sequence secondary structure"),
                            ("signalp", "SignalP 6 — actual full-fusion signal peptide"),
                            ("deeptmhmm", "DeepTMHMM 1 — actual full-fusion topology"),
                            ("tango", "Licensed TANGO — actual full-fusion aggregation"),
                            ("catgranule", "Original catGRANULE — IDR propensity and native profile"))]
