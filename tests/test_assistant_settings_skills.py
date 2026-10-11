"""Software-only profile/protocol acceptance. The HTTP fixture is not an LLM."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread

from fastapi.testclient import TestClient

from workbench_fixture import fixture_app
from igem_drylab.workflow.assistant_settings import AssistantSettingsInput


def test_hosted_model_settings_reject_internal_endpoints_and_none_keeps_manual_tools(tmp_path):
    app=fixture_app(tmp_path)
    with TestClient(app) as client:
        before=client.get('/api/platform/tools').json()
        response=client.post('/api/platform/assistant/settings',json={'provider':'local_endpoint','model':'fixture',
            'endpoint':'http://127.0.0.1:19091/v1/chat/completions'})
        assert response.status_code==403
        response=client.post('/api/platform/assistant/settings',json={'provider':'compatible_api','model':'fixture',
            'endpoint':'https://unapproved.example/v1/chat/completions'})
        assert response.status_code==403
        assert client.post('/api/platform/assistant/settings',json={'provider':'none'}).status_code==200
        assert client.get('/api/platform/tools').json()==before
        assert not client.get('/api/platform/assistant/settings').json()['configured']
        assert app.state.platform_store.runs()==[] and app.state.fixture_calls==[]


def test_private_saved_model_real_http_protocol_probes_and_restart(tmp_path):
    calls=[]
    class ProtocolFixture(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"SOFTWARE_PROTOCOL_FIXTURE"}]}')
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append(body)
            self.send_response(200);self.end_headers()
            if body.get('stream'):
                self.wfile.write(b'data: {"choices":[{"delta":{"content":"OK"}}]}\n\ndata: [DONE]\n\n')
            else:
                message={'content':'{"ok":true}'}
                if body.get('tools'): message={'tool_calls':[{'function':{'name':'ping','arguments':'{}'}}]}
                self.wfile.write(json.dumps({'choices':[{'message':message}]}).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),ProtocolFixture)
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        app=fixture_app(tmp_path)
        app.state.application.assistant_settings.configure_deployment(local_workspace=True)
        endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
        secret='SOFTWARE_FIXTURE_WRITE_ONLY_SECRET'
        with TestClient(app) as client:
            result=client.post('/api/platform/assistant/settings',json={'provider':'local_endpoint','model':'SOFTWARE_PROTOCOL_FIXTURE',
                'endpoint':endpoint,'secret':secret}).json()
            assert result['configured'] and result['has_secret']
            assert app.state.application.planning.backend is None
            assert secret not in json.dumps(result) and endpoint not in json.dumps(result)
            response=client.post('/api/platform/assistant/settings/test',json={})
            assert response.status_code==200,response.text
            assert set(response.json()['capabilities'].values())=={'observed'}
            assert len(calls)==3
            assert app.state.platform_store.runs()==[] and app.state.fixture_calls==[]
            assert secret not in client.get('/api/platform/projects/software-fixture').text
            import os
            if os.name=='nt': assert secret not in app.state.application.assistant_settings.path.read_text()
        # Persisted private profile restores only in a permitted deployment.
        from igem_drylab.software.application import ApplicationService
        other=ApplicationService(tmp_path,workflow_tools=app.state.application.tools)
        other.assistant_settings.configure_deployment(local_workspace=True)
        assert other.assistant_settings.view().has_secret
        assert other.assistant_settings.view().configured
        assert other.planning.backend is not None
        other.assistant_settings.save(AssistantSettingsInput(
            provider='local_endpoint',model='SOFTWARE_PROTOCOL_FIXTURE',endpoint=endpoint.replace('/v1/','/v2/')))
        assert not other.assistant_settings.view().has_secret
        assert other.planning.backend is None
    finally:
        server.shutdown();server.server_close()


def test_unavailable_os_secret_does_not_block_manual_workspace(tmp_path,monkeypatch):
    from igem_drylab.workflow.models import WorkflowError
    from igem_drylab.software.application import ApplicationService
    app=fixture_app(tmp_path)
    settings=app.state.application.assistant_settings
    settings.path.parent.mkdir(parents=True,exist_ok=True)
    profile={**settings.profile,'secret':'dpapi:ZmFrZQ==','provider':'local_endpoint',
             'endpoint':'http://127.0.0.1:19091/v1/chat/completions','model':'fixture',
             'capabilities':{'json':'observed'}}
    settings.path.write_text(json.dumps(profile))
    def unavailable(*args,**kwargs): raise WorkflowError('assistant_private_secret_unavailable')
    monkeypatch.setattr('igem_drylab.workflow.assistant_settings.windows_secret',unavailable)
    service=ApplicationService(tmp_path,workflow_tools=app.state.application.tools)
    service.assistant_settings.configure_deployment(local_workspace=True)
    assert service.planning.backend is None
    assert service.assistant_settings.view().capabilities['json']=='secret_unavailable'
    assert json.loads(settings.path.read_text())==profile
    assert service.store.runs()==[]


def test_skill_is_plain_instructions_revision_bound_and_not_scientific_authority(tmp_path):
    app=fixture_app(tmp_path)
    text='---\nname: SOFTWARE_FIXTURE\ndescription: Explicit instruction document\ntrigger: Review software tasks\nversion: "1"\nsource: User-authored fixture\nlicense: Apache-2.0\n---\nDo not run this code: ```python\nraise RuntimeError()\n```\n'
    with TestClient(app) as client:
        response=client.post('/api/platform/skills',json={'text':text,'enabled':True})
        assert response.status_code==200,response.text
        skill=response.json()
        assert skill['execution']=='instructions_only' and skill['revision']==1
        assert client.get('/api/platform/skills').json()['items']==[skill]
        updated=client.post('/api/platform/skills/'+skill['id'],json={'text':text,'enabled':False,'expected_revision':1}).json()
        assert updated['revision']==2 and not updated['enabled']
        assert client.post('/api/platform/skills/'+skill['id'],json={'text':text,'enabled':True,'expected_revision':1}).status_code==409
        assert app.state.application.skills.guidance()==''
        assert app.state.platform_store.runs()==[] and app.state.fixture_calls==[]
