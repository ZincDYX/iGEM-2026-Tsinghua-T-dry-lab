from __future__ import annotations

from pathlib import Path

import pytest

from igem_drylab.mcp import create_default_registry
from igem_drylab.parameters import ParameterRecord, ParameterRegistry
from igem_drylab.parameters.requirements import m3_requirements, m4_requirements
from igem_drylab.project_state import ProjectState
from igem_drylab.wetlab import WetLabResult, replicate_variation


def _requirement(name: str):
    return next(item for item in [*m3_requirements(), *m4_requirements()] if item.name == name)


def test_state_approval_reuses_strict_requirement_identity() -> None:
    state = ProjectState(project_id="p")
    wrong = ParameterRecord(parameter_id="bad", name="phi", value=0.2, unit="1", parameter_type="kp", source_type="wetlab", source_reference="run", review_status="validated")
    with pytest.raises(ValueError, match="candidate_requirement_mismatch"):
        state.approve_parameter(wrong, reviewer="reviewer", target_stage="m3")


def test_registry_rejects_cross_identity_supersedes() -> None:
    parent = ParameterRecord(parameter_id="a", name="km_dmt_11", value=1, unit="uM", parameter_type="km", enzyme_id="DMT", substrate_id="11", source_type="literature", doi="10/x", evidence_text="table", review_status="approved")
    child = parent.model_copy(update={"parameter_id": "b", "substrate_id": "9", "supersedes": "a"})
    with pytest.raises(ValueError, match="incompatible_supersedes"):
        ParameterRegistry([parent, child])


def test_scoped_resolution_prefers_exact_construct_and_condition() -> None:
    requirement = _requirement("oc_total")
    base = dict(name="oc_total", unit="uM", parameter_type="abundance", enzyme_id="OC", source_type="wetlab", source_reference="run", review_status="approved")
    registry = ParameterRegistry([
        ParameterRecord(parameter_id="global", value=1, **base),
        ParameterRecord(parameter_id="construct", value=2, construct_id="c", **base),
        ParameterRecord(parameter_id="exact", value=3, construct_id="c", condition_id="d", **base),
    ])
    assert registry.resolve(requirement, construct_id="c", condition_id="d").canonical_value == 3
    assert registry.resolve(requirement, construct_id="c", condition_id="other").canonical_value == 2
    assert registry.resolve(requirement, construct_id="other", condition_id="other").canonical_value == 1


def test_replicate_variation_uses_canonical_units_and_censoring() -> None:
    common = dict(construct_id="c", condition_id="d", metabolite_time=[0, 24], metabolites={"15": [0, 1]})
    first = WetLabResult(experiment_id="e1", replicate_id="r1", metabolite_concentration_unit="mM", metabolite_lod={"15": 0.1}, **common)
    second = WetLabResult(experiment_id="e2", replicate_id="r2", metabolite_concentration_unit="uM", metabolites={"15": [0, 1000]}, metabolite_lod={"15": 100}, construct_id="c", condition_id="d", metabolite_time=[0, 24])
    values = replicate_variation([first, second])
    assert values[("c", "d", "15", 0.0)] is None
    assert values[("c", "d", "15", 24.0)] == pytest.approx(0)


def test_mcp_approval_requires_reviewer_and_revalidates_candidate(tmp_path: Path) -> None:
    import yaml
    from test_experimental_condition_chain import assay
    from igem_drylab.pipeline import load_config
    from igem_drylab.pipeline.config import ExperimentalContext
    from igem_drylab.parameters import ParameterRegistry,resolve_requirement
    from igem_drylab.parameters.requirements import requirements_for_stage
    source = Path("configs/m1_m4_real_scoring_example.yaml")
    config = source.read_text(encoding="utf-8").replace("../examples/", str((Path("examples").resolve())).replace("\\", "/") + "/")
    project = tmp_path / "project.yaml"
    project.write_text(config, encoding="utf-8")
    candidate = {"parameter_id": "reviewed-phi", "name": "phi", "value": 0.2, "unit": "1", "parameter_type": "phi", "source_type": "wetlab", "source_reference": "assay:rep1", "review_status": "validated"}
    registry=create_default_registry()
    rejected=registry.call('igem.parameters.approve',{'config_path':str(project),'candidate':candidate,
        'stage':'m3','requirement_name':'phi','reviewer':'human'})
    assert rejected.is_error
    actual=load_config(project)
    actual.experimental_context=ExperimentalContext(host='yeast',strain='s',temperature_c=30.,pH=7.,assay_system='in_cell')
    actual.stages.m4_reaction.condition_id='d'
    project.write_text(yaml.safe_dump(actual.model_dump(mode='json')),encoding='utf-8')
    candidate.update(construct_id='c',condition_id='d',conditions=assay().parameter_conditions())
    assert registry.call('igem.parameters.approve',{'config_path':str(project),'candidate':candidate,
        'stage':'m3','requirement_name':'phi','reviewer':''}).is_error
    result = create_default_registry().call("igem.parameters.approve", {"config_path": str(project), "candidate": candidate, "stage": "m3", "requirement_name": "phi", "reviewer": "human"})
    assert result.is_error is False
    assert result.as_protocol_dict()["structuredContent"]["approved_parameter"]["approved_by"] == "human"
    reloaded=load_config(project)
    requirement=next(r for r in requirements_for_stage(reloaded,'m3') if r.name=='phi')
    resolved=resolve_requirement(ParameterRegistry(reloaded.parameters),requirement,reloaded.experimental_context,
        allow_assumptions=False,construct_id='c',condition_id='d',require_provenance=True)
    assert resolved.status=='resolved' and resolved.canonical_value==.2
