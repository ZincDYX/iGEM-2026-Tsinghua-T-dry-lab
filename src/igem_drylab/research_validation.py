"""Calibration -> immutable prediction snapshot -> holdout, without refitting."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np

from .prediction import PredictionContract, observe_prediction, SCIENTIFIC_ASSAY_FIELDS
from .wetlab.canonical import canonicalize_metabolite
from .wetlab.models import load_wetlab_results


def _digest(payload):
    return sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), allow_nan=False).encode()).hexdigest()


def freeze_prediction(prediction_file: Path, parameter_file: Path, calibration_datasets: dict[str,Path],
                      *, freeze_id: str, construct_id: str, condition_id: str, claim_scope: str) -> dict:
    raw = prediction_file.read_bytes()
    artifact = json.loads(raw)
    contract = PredictionContract.model_validate(artifact["prediction_contract"]).model_dump(mode="json")
    if not all((freeze_id.strip(), construct_id.strip(), condition_id.strip(), claim_scope.strip())):
        raise ValueError("freeze_requires_explicit_identity_and_claim_scope")
    if claim_scope not in {"software_fixture_only", "conditional_mechanism", "published_reference_reproduction"}:
        raise ValueError("freeze_cannot_declare_an_unvalidated_biological_claim")
    experimental = artifact.get("experimental_contract",{})
    context = contract["experiment_context"]
    for key in ("assay_mode", "expression_mode", "input_boundary", "assay_conditions"):
        if key in experimental or key in context:
            left, right = experimental.get(key), context.get(key)
            if key == "assay_conditions" and isinstance(left, dict) and isinstance(right, dict):
                left = {field: left.get(field) for field in SCIENTIFIC_ASSAY_FIELDS}
                right = {field: right.get(field) for field in SCIENTIFIC_ASSAY_FIELDS}
            if left != right:
                raise ValueError("freeze_experimental_contract_conflict:" + key)
    if claim_scope=="conditional_mechanism" and (not experimental.get("assay_mode") or not experimental.get("expression_mode")):
        raise ValueError("freeze_requires_declared_experimental_mode_not_inferred_metadata")
    if claim_scope == "conditional_mechanism" and any(context.get("assay_conditions", {}).get(key) is None
            for key in ("host", "temperature_c", "pH", "assay_system")):
        raise ValueError("freeze_requires_scientific_assay_conditions")
    for field,value in (("construct_id",construct_id),("condition_id",condition_id)):
        recorded = artifact.get(field,contract["kernel_inputs"].get(field))
        if recorded is not None and recorded!=value:
            raise ValueError("freeze_identity_does_not_match_prediction")
    training = {}
    identities = []
    for dataset_id,path in calibration_datasets.items():
        records = load_wetlab_results(path)
        training[dataset_id] = {"path":str(path),"sha256":sha256(path.read_bytes()).hexdigest(),
                                "record_identities":[list(r.record_key) for r in records]}
        identities.extend(list(r.record_key) for r in records)
    source_root = Path(__file__).resolve().parent
    snapshot = {"schema_version":"research-freeze-v1","freeze_id":freeze_id,
        "frozen_at":datetime.now(timezone.utc).isoformat(),"construct_id":construct_id,"condition_id":condition_id,
        "claim_scope":claim_scope,"prediction_contract":contract,"prediction_file_sha256":sha256(raw).hexdigest(),
        "experimental_contract":artifact.get("experimental_contract",{}),
        "parameter_file_sha256":sha256(parameter_file.read_bytes()).hexdigest(),
        "calibration_dataset_ids":list(training),"calibration_datasets":training,
        "calibration_record_identities":identities,
        "source_sha256":{str(p.relative_to(source_root)):sha256(p.read_bytes()).hexdigest() for p in sorted(source_root.rglob("*.py"))},
        "environment":{name:version(name) for name in ("numpy","scipy","pydantic")},
        "validation_status":"pending_independent_data_no_validation_claim"}
    snapshot["manifest_sha256"] = _digest(snapshot)
    return snapshot


def validate_holdout(snapshot: dict, dataset_id: str, dataset_file: Path) -> dict:
    body = {k:v for k,v in snapshot.items() if k!="manifest_sha256"}
    if _digest(body)!=snapshot.get("manifest_sha256"):
        raise ValueError("frozen_manifest_integrity_mismatch")
    if snapshot["schema_version"]!="research-freeze-v1":
        raise ValueError("unsupported_research_freeze_version")
    data_hash = sha256(dataset_file.read_bytes()).hexdigest()
    if dataset_id in snapshot["calibration_dataset_ids"] or data_hash in {
            row["sha256"] for row in snapshot["calibration_datasets"].values()}:
        raise ValueError("validation_dataset_overlaps_calibration")
    records = load_wetlab_results(dataset_file)
    metrics = []
    freeze_time = datetime.fromisoformat(snapshot["frozen_at"])
    for record in records:
        if list(record.record_key) in snapshot["calibration_record_identities"]:
            raise ValueError("validation_record_overlaps_calibration_even_with_new_file_name")
        if (record.construct_id,record.condition_id)!=(snapshot["construct_id"],snapshot["condition_id"]):
            raise ValueError("holdout_identity_does_not_match_frozen_prediction")
        if snapshot["claim_scope"]=="conditional_mechanism":
            if record.assay_mode is None or record.expression_mode is None or not record.input_boundary:
                raise ValueError("real_holdout_requires_declared_assay_expression_and_boundary")
            if record.observation_kind=="steady_state" and not record.steady_state_confirmation_reference:
                raise ValueError("steady_holdout_requires_observed_platform_evidence")
        time,predicted = observe_prediction(snapshot["prediction_contract"],record,
            require_assay_conditions=snapshot["claim_scope"] == "conditional_mechanism")
        observed_time = np.asarray(record.time_hours())
        if len(time)==0 or observed_time.size==0 or observed_time.min()<time.min() or observed_time.max()>time.max():
            raise ValueError("holdout_outside_frozen_prediction_horizon")
        series = {}
        for compound in record.metabolites:
            canonical = canonicalize_metabolite(record,compound)
            if compound not in predicted:
                raise ValueError("holdout_observable_not_predicted")
            aligned = np.interp(observed_time,time,predicted[compound])
            indices = [i for i,flag in enumerate(canonical.censor_mask) if flag=="quantified"]
            residual = np.asarray(canonical.concentration_uM)[indices]-aligned[indices]
            series[compound] = {"status":"evaluated_without_acceptance_threshold" if indices else "all_censored",
                "observed_uM":canonical.concentration_uM,"predicted_uM":aligned.tolist(),
                "censor_mask":canonical.censor_mask,"quantified_indices":indices,"residual_uM":residual.tolist(),
                "rmse_uM":float(np.linalg.norm(residual)/np.sqrt(len(indices))) if indices else None,
                "mae_uM":float(np.mean(np.abs(residual))) if indices else None,
                "bias_uM":float(np.mean(residual)) if indices else None}
        timestamp = record.timestamp
        temporal = "unconfirmed_measurement_timestamp"
        if timestamp is not None:
            if timestamp.tzinfo is None:
                temporal = "unconfirmed_timestamp_timezone"
            else:
                temporal = "prospective_measurement_after_freeze" if timestamp>freeze_time else "retrospective_holdout"
        metrics.append({"record_identity":list(record.record_key),"temporal_scope":temporal,"series":series})
    return {"schema_version":"research-holdout-v1","freeze_id":snapshot["freeze_id"],
        "frozen_manifest_sha256":snapshot["manifest_sha256"],"validation_dataset_ids":[dataset_id],
        "validation_raw_sha256":data_hash,"records":metrics,"parameters_refitted":False,
        "claim_scope":"independent_holdout_error_report_no_unstated_pass_threshold",
        "iteration_policy":"new_calibration_or_data_revision_requires_a_new_freeze_not_overwriting_this_prediction"}
