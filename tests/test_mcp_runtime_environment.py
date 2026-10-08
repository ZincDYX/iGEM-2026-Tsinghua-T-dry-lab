"""Transport resource controls only; not scientific/biological validation."""
from pathlib import Path
import sys
from igem_drylab.workflow.mcp_bridge import server_parameters


def test_explicit_runtime_controls_are_kept_but_tokens_are_not(monkeypatch):
    monkeypatch.setenv('OPENBLAS_NUM_THREADS','1')
    monkeypatch.setenv('OMP_NUM_THREADS','2')
    monkeypatch.setenv('FUSIONLAB_SESSION_TOKEN','software_fixture_not_a_secret')
    monkeypatch.setenv('UNRELATED_API_KEY','software_fixture_not_a_secret')
    parameters = server_parameters(Path('/software_fixture/src/igem_drylab'))
    assert parameters.command == sys.executable
    assert parameters.args == ['-B','-m','igem_drylab.mcp.server']
    assert parameters.env['OPENBLAS_NUM_THREADS'] == '1'
    assert parameters.env['OMP_NUM_THREADS'] == '2'
    assert 'FUSIONLAB_SESSION_TOKEN' not in parameters.env
    assert 'UNRELATED_API_KEY' not in parameters.env


def test_absent_controls_are_not_invented_for_server_runs(monkeypatch):
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','PYTHONUTF8'):
        monkeypatch.delenv(key,raising=False)
    assert server_parameters(Path('/software_fixture/src/igem_drylab')).env == {'PYTHONPATH': '/software_fixture/src'}
