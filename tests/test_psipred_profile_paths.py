"""Legacy list-file path oracle; synthetic format outputs, not native jobs."""
import json
from hashlib import sha256
from pathlib import Path

import pytest

from igem_drylab.psipred_runner import finish_profile


@pytest.mark.data_contract
def test_legacy_makemat_prefix_and_list_entries_are_relative(tmp_path,monkeypatch):
    output=tmp_path/'nested'/'prediction';output.mkdir(parents=True)
    sequence='GSGSGSGSGSGS'
    (output/'native.chk').write_bytes(b'synthetic-checkpoint-not-native-data')
    (output/'input.fasta').write_text('>fixture\n'+sequence+'\n')
    (output/'native.blast').write_text('UniRef90_SYNTHETIC_FORMAT_FIXTURE\n')
    seen=[]
    def synthetic_run(command,**kwargs):
        seen.append(command)
        if Path(command[0]).name=='makemat':
            assert command[1:]==['-P','native']
            # This emulates the legacy prefix concatenation that broke actual
            # jobs. An absolute listed path would be prefixed a second time.
            for suffix in ('pn','sn'):
                listed=(output/('native.'+suffix)).read_text().strip()
                assert not Path(listed).is_absolute()
                assert (output/listed).is_file()
        elif Path(command[0]).name=='psipass2':
            (output/'native.ss2').write_text(''.join(f'{i} {aa} C 0.8 0.1 0.1\n' for i,aa in enumerate(sequence,1)))
    monkeypatch.setattr('igem_drylab.psipred_runner.subprocess.run',synthetic_run)
    identity=dict(tool_version='synthetic-fixture',input_sha256=sha256(sequence.encode()).hexdigest(),database_release='synthetic')
    result=finish_profile(output,tmp_path/'tool',tmp_path/'ncbi',identity,[])
    assert result.states=='C'*len(sequence)
    assert len(seen)==3
    assert json.loads((output/'native-state.json').read_text())['status']=='validated'


@pytest.mark.integration
def test_real_MCP_profile_parser_publishes_assets_not_private_paths(tmp_path):
    from igem_drylab.workflow.builtins import builtin_tools
    from igem_drylab.workflow.mcp_bridge import register_scientific_mcp
    from igem_drylab.workflow.engine import WorkflowEngine
    from igem_drylab.workflow.store import WorkflowStore
    from igem_drylab.workflow.models import Project,Workflow,WorkflowNode,LiteralInput
    raw=tmp_path/'synthetic-format.ss2';raw.write_text('1 G C 0.8 0.1 0.1\n2 S C 0.8 0.1 0.1\n')
    tools=builtin_tools();register_scientific_mcp(tools)
    engine=WorkflowEngine(WorkflowStore(tmp_path/'ledger.sqlite'),tools,tmp_path/'artifacts')
    asset=engine.disclosure.asset(raw,project_id='p')
    arguments=dict(path=asset['path'],tool_name='PSIPRED',tool_version='synthetic-format-not-native-job',input_sha256=sha256(b'GS').hexdigest())
    workflow=Workflow(id='profile',name='Synthetic format transport',nodes=[WorkflowNode(id='parse',label='Parse',
        tool_id='igem.m1.parse_secondary_structure',inputs={k:LiteralInput(value=v) for k,v in arguments.items()})])
    run=engine.run(engine.create(Project(id='p',name='Synthetic transport'),workflow))
    assert run['status']=='succeeded'
    public=engine.disclosure.run(run)
    serialized=json.dumps(public)
    assert str(raw) not in serialized and asset['path'] in serialized
    assert 'CC' in serialized
