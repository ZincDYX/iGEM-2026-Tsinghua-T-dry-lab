import json
import shlex
import sys

from igem_drylab.pipeline.adapters import ExternalToolAdapter
from igem_drylab.pipeline.config import ToolConfig
from igem_drylab.mcp.tools import _persist_standard_output


def test_real_fixture_process_records_hashes_but_is_not_a_scientific_tool(tmp_path):
    config = ToolConfig(enabled=True,mode='external',command=shlex.join([sys.executable,'-c',"print('fixture stdout, not a prediction')"]))
    input_file = tmp_path/'input.txt'
    input_file.write_text('software-fixture')
    result = ExternalToolAdapter('iupred2a',config).run(output_dir=tmp_path/'job',input_files={'input':input_file})
    result = _persist_standard_output('iupred2a',result)
    manifest = json.loads(result.manifest_file.read_text())
    assert manifest['status']=='succeeded' and manifest['return_code']==0
    assert manifest['executable_sha256'] and manifest['input_sha256']
    assert manifest['output_sha256'][str(result.outputs['standard_output'].resolve())]
    assert manifest['stdout_sha256'] and manifest['stderr_sha256']


def test_timeout_retains_failure_record_instead_of_erasing_job(tmp_path):
    config = ToolConfig(enabled=True,mode='external',command=shlex.join([sys.executable,'-c','import time; time.sleep(2)']))
    result = ExternalToolAdapter('fixture-process-not-scientific-tool',config).run(output_dir=tmp_path,timeout_seconds=.02)
    assert result.status=='timed_out' and result.return_code is None
    assert result.manifest_file.is_file() and result.executable_sha256


def test_mock_is_not_execution_and_has_no_executable_hash(tmp_path):
    config = ToolConfig(enabled=True,mode='mock',command='does-not-run')
    result = ExternalToolAdapter('fixture',config).run(output_dir=tmp_path)
    assert result.status=='mock' and result.executable_sha256 is None and result.return_code is None


def test_freesasa_summary_does_not_overwrite_residue_artifact(tmp_path):
    from igem_drylab.pipeline.adapters import ToolRunResult
    artifact = tmp_path/'freesasa.json'
    raw = '{"residueAreas":{"A":{"1":{"total":1.}}}}'
    artifact.write_text(raw)
    run = ToolRunResult(tool='freesasa',mode='external',status='succeeded',argv=['fixture'],
        output_dir=tmp_path,stdout='{"output":"freesasa.json","totalArea":1.}',return_code=0)
    updated = _persist_standard_output('freesasa',run)
    assert artifact.read_text()==raw
    assert updated.outputs['standard_output']!=artifact
    assert updated.outputs['freesasa']==artifact
