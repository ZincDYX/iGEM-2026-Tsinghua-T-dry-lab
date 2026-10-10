"""Server-only synthetic numerical checks, not project empirical uncertainty."""
from hashlib import sha256
import math

import pytest

from igem_drylab.m3_equilibrium import solve_m3_equilibrium
from igem_drylab.m4_workflow import M3M4JointSamples,M4ReportInput,run_m4_report
from test_m3_markdown_contract import _input as m3_input
from test_m4_markdown_contract import _input as m4_input


def paired_case(tmp_path, text="sample_id,oc_total,oc_kcat\npaired-high,4,20\npaired-low,1,2\n"):
    m3=m3_input()
    solved=solve_m3_equilibrium(m3)
    m4=m4_input()
    for enzyme,species in (("OC",solved.oc),("DMT",solved.dmt)):
        m4.enzymes[enzyme].dense_um=species.total_dense_um
        m4.enzymes[enzyme].dilute_um=species.free_dilute_um
    source=tmp_path/"synthetic-paired.csv"
    source.write_text(text)
    settings=M3M4JointSamples(construct_id="construct",condition_id="condition",
        source={"path":source,"sha256":sha256(source.read_bytes()).hexdigest()},source_reference="SYNTHETIC SOFTWARE FIXTURE",
        reviewed_by="fixture_not_human_experimental_approval",sample_basis="supplied_joint_model_draws",
        sampling_method_reference="two fixed paired synthetic rows, not empirical biology",
        columns=[{"column":"oc_total","stage":"m3","parameter_name":"c_oc_total_um","parameter_id":"oc-total","unit":"uM"},
            {"column":"oc_kcat","stage":"m4","parameter_name":"kcat_r3","parameter_id":"kcat-R3","unit":"1/h"}])
    return m3,m4,settings


def test_each_correlated_row_recalculates_M3_before_all_M4_controls(tmp_path,monkeypatch):
    import igem_drylab.m4_workflow as workflow
    m3,m4,settings=paired_case(tmp_path)
    captured=[]
    original=workflow._solve_scenarios
    def inspect(case):
        captured.append(case)
        return original(case)
    monkeypatch.setattr(workflow,"_solve_scenarios",inspect)
    result=run_m4_report(M4ReportInput(steady_input=m4,recruitment_input=m3,joint_samples=settings))
    joint=result["joint_uncertainty"]
    assert joint["complete"] and joint["valid_samples"]==2
    assert [row["sample_id"] for row in joint["samples"]]==["paired-high","paired-low"]
    assert [case.reactions[2].kcat_per_h for case in captured[1:]]==[20,2]
    for total,case,row in zip((4,1),captured[1:],joint["samples"],strict=True):
        # Independent E1 quadratic oracle: a*c + phi*N*K*c/(Kd+K*c)=total.
        a=(1-m3.phi)+m3.phi*m3.k_oc
        n=m3.s_sh3*m3.eta_acc_sh3*m3.eta_bind_sh3*m3.c_dense_um
        b=a*m3.kd_sh3_um+m3.phi*n*m3.k_oc-total*m3.k_oc
        c=2*total*m3.kd_sh3_um/(b+math.sqrt(b*b+4*a*m3.k_oc*total*m3.kd_sh3_um))
        assert case.enzymes["OC"].dilute_um==pytest.approx(c,rel=1e-10)
        assert m3.phi*case.enzymes["OC"].dense_um+(1-m3.phi)*case.enzymes["OC"].dilute_um==pytest.approx(total,abs=1e-10)
        assert row["source_values"]["oc_total"]==str(total)
    assert captured[1].enzymes["OC"].dense_um!=captured[2].enzymes["OC"].dense_um
    assert "not_independent_LHS" in joint["method"]


def test_failed_rows_are_retained_and_envelope_is_explicitly_conditional(tmp_path):
    m3,m4,settings=paired_case(tmp_path,"sample_id,oc_total,oc_kcat\nvalid,4,20\ninvalid,-1,2\n")
    joint=run_m4_report(M4ReportInput(steady_input=m4,recruitment_input=m3,joint_samples=settings))["joint_uncertainty"]
    assert len(joint["samples"])==2 and joint["failed_samples"]==1
    assert joint["samples"][1]["status"]=="invalid_input" and joint["samples"][1]["error"]
    assert not joint["complete"] and joint["scope"]=="conditional_on_valid_samples"


def test_joint_sources_and_baseline_are_not_silently_rebound(tmp_path):
    m3,m4,settings=paired_case(tmp_path)
    m4.enzymes["OC"].dense_um+=1
    with pytest.raises(ValueError,match="match_actual_M3"):
        run_m4_report(M4ReportInput(steady_input=m4,recruitment_input=m3,joint_samples=settings))
    m3,m4,settings=paired_case(tmp_path)
    settings.source.path.write_text("modified source")
    with pytest.raises(ValueError,match="ER_source_artifact_identity_changed"):
        run_m4_report(M4ReportInput(steady_input=m4,recruitment_input=m3,joint_samples=settings))


def test_joint_samples_execute_through_actual_MCP_stdio(tmp_path):
    import asyncio
    import os
    import sys
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    from pathlib import Path
    m3,m4,settings=paired_case(tmp_path)
    async def exercise():
        root=Path(__file__).resolve().parents[1]
        parameters=StdioServerParameters(command=sys.executable,args=["-m","igem_drylab.mcp.server"],cwd=root,
            env={"PYTHONPATH":os.environ.get("PYTHONPATH",str(root/"src")),"OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1"})
        async with Client(parameters,read_timeout_seconds=60) as client:
            response=await client.call_tool("igem.m4.report",{"payload":M4ReportInput(steady_input=m4,
                recruitment_input=m3,joint_samples=settings).model_dump(mode="json")})
            assert not response.is_error
            assert response.structured_content["result"]["joint_uncertainty"]["valid_samples"]==2
    asyncio.run(exercise())
