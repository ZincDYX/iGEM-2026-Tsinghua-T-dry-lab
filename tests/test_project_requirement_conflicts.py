from __future__ import annotations

from pathlib import Path

from igem_drylab.parameters import ParameterRecord, ParameterRegistry
from igem_drylab.parameters.requirements import requirements_for_stage
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import RecruitmentConfig


def _project_with_recruitment():
    project = load_config(Path("configs/m1_m4_real_scoring_example.yaml")).model_copy(deep=True)
    project.stages.m3_concentration.recruitment = [
        RecruitmentConfig(
            enzyme_id="OC",
            enzyme_total_parameter="oc_total",
            site_total_parameter="oc_site_total",
            kd_parameter="oc_recruit_kd",
        )
    ]
    return project


def _catalog(project):
    return {
        requirement.name: requirement
        for stage in ("m3", "m4")
        for requirement in requirements_for_stage(project, stage)
    }


def _record(identifier: str, value: float, unit: str = "uM", *, supersedes: str | None = None) -> ParameterRecord:
    return ParameterRecord(
        parameter_id=identifier,
        name="oc_recruit_kd",
        value=value,
        unit=unit,
        parameter_type="kd",
        enzyme_id="OC",
        source_type="wetlab",
        derivation_type="direct_measurement",
        source_reference="assay",
        review_status="approved",
        supersedes=supersedes,
    )


def test_project_specific_recruitment_conflicts_use_explicit_catalog() -> None:
    registry = ParameterRegistry([_record("a", 1), _record("b", 2)])
    assert {item.parameter_id for item in registry.list_conflicts(requirements=_catalog(_project_with_recruitment()))} == {"a", "b"}


def test_project_specific_recruitment_canonical_equivalence_is_not_conflict() -> None:
    registry = ParameterRegistry([_record("a", 1, "mM"), _record("b", 1000, "uM")])
    assert registry.list_conflicts(requirements=_catalog(_project_with_recruitment())) == []


def test_project_specific_recruitment_transitive_lineage_has_one_leaf() -> None:
    registry = ParameterRegistry([_record("a", 1), _record("b", 2, supersedes="a"), _record("c", 3, supersedes="b")])
    catalog = _catalog(_project_with_recruitment())
    assert registry.resolve(catalog["oc_recruit_kd"]).selected_parameter.parameter_id == "c"
    assert registry.list_conflicts(requirements=catalog) == []


def test_legacy_parameter_not_in_project_catalog_is_skipped() -> None:
    legacy = ParameterRecord(parameter_id="legacy", name="legacy_parameter", value=1, unit="1", parameter_type="other", source_type="assumption", derivation_type="other", source_reference="manual", review_status="approved")
    registry = ParameterRegistry([legacy, _record("a", 1), _record("b", 2)])
    assert {item.parameter_id for item in registry.list_conflicts(requirements=_catalog(_project_with_recruitment()))} == {"a", "b"}
