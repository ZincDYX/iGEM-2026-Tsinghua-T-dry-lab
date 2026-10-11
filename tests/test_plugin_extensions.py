"""Actual local source import/process lifecycle; no scientific tool simulation."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile,ZipInfo

import pytest

from igem_drylab.workflow.builtins import builtin_tools
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import NodeContext,ToolFailure


def test_import_is_not_execution_and_disable_survives_restart(tmp_path):
    store=WorkflowStore(tmp_path/'ledger.sqlite')
    plugins=PluginManager(tmp_path/'plugins',store,builtin_tools())
    source=Path('examples/plugins/sequence_composition')
    raw=BytesIO()
    with ZipFile(raw,'w') as archive:
        for name in ('plugin.json','composition.py'):
            archive.write(source/name,'uploaded/'+name)
    inspection=plugins.import_archive(raw.getvalue())
    assert plugins.installed()==[]
    assert not list(plugins.root.glob('*/environment'))
    record=plugins.install(Path(inspection['source_path']),trusted=True,expected_hash=inspection['hash'])
    tool=plugins.tools.get(f"plugin.sequence_composition.{record['hash'][:12]}")
    def invoke(name):
        context=NodeContext('software-only',name,tmp_path/name)
        context.work_dir.mkdir()
        return tool.handler(tool.input_model.model_validate({'sequence':'AAC'}),context)
    result=invoke('enabled')
    assert result['counts']=={'A':2,'C':1} and result['length']==3
    plugins.set_enabled(record['hash'],False)
    with pytest.raises(ToolFailure,match='disabled'):
        invoke('disabled')
    assert not (tmp_path/'disabled'/'plugin_input.json').exists()
    restarted=PluginManager(plugins.root,store,builtin_tools())
    restarted.load_installed()
    assert restarted.installed()[0]['enabled'] is False
    restarted.set_enabled(record['hash'],True)
    assert invoke('reenabled')['counts']=={'A':2,'C':1}
    assert len(restarted.installed())==1


@pytest.mark.parametrize('name',['../escape.py','root/../../escape.py','C:/escape.py','root\\escape.py'])
def test_uploaded_archive_paths_are_rejected_before_writing(tmp_path,name):
    plugins=PluginManager(tmp_path/'plugins',WorkflowStore(tmp_path/'ledger.sqlite'),builtin_tools())
    raw=BytesIO()
    with ZipFile(raw,'w') as archive:
        # ZipInfo normally normalizes the host separator on Windows; preserve
        # the hostile cross-platform archive spelling being tested.
        entry=ZipInfo(name)
        entry.filename=name
        archive.writestr(entry,'must not execute')
    with pytest.raises(ValueError): plugins.import_archive(raw.getvalue())
    assert not list(plugins.root.rglob('*.py'))


def test_readable_repository_ref_resolves_once_to_exact_commit(tmp_path,monkeypatch):
    # Transport fixture only: it is not a real third-party repository deployment.
    plugins=PluginManager(tmp_path/'plugins',WorkflowStore(tmp_path/'ledger.sqlite'),builtin_tools())
    calls=[]
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'id':'a'*40}
    class Session:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def get(self,url,**kwargs):
            calls.append((url,kwargs));return Response()
    monkeypatch.setattr('igem_drylab.workflow.plugins.requests.Session',Session)
    monkeypatch.setattr(plugins,'fetch_github',lambda repository,commit:{'commit':commit})
    result=plugins.fetch_repository('https://gitlab.igem.org/example/nested/plugin','develop')
    assert result=={'commit':'a'*40}
    assert calls[0][0].endswith('/example%2Fnested%2Fplugin/repository/commits/develop')
    assert calls[0][1]['allow_redirects'] is False
