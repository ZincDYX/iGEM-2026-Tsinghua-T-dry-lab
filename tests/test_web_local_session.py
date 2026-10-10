"""Actual HTTP security and durable service checks; no scientific calculation."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from igem_drylab.software.dashboard import create_app

ORIGIN='http://127.0.0.1:8780'


def browser(tmp_path):
    frontend=tmp_path/'frontend';frontend.mkdir()
    (frontend/'index.html').write_text('<html><body>HTTP routing fixture, not UI acceptance</body></html>')
    app=create_app(data_dir=tmp_path/'workspace',session_token='private-test-token',discover_tools=False,
        local_web_origin=ORIGIN,frontend_dir=frontend)
    return TestClient(app,base_url=ORIGIN,client=('127.0.0.1',55000))


def test_http_only_origin_checked_bootstrap_and_cookie_csrf(tmp_path):
    with browser(tmp_path) as client:
        assert client.get('/').status_code==200
        assert client.get('/api/platform/projects').status_code==401
        assert client.post('/api/session/bootstrap',headers={'Origin':'https://attacker.invalid'}).status_code==403
        ready=client.post('/api/session/bootstrap',headers={'Origin':ORIGIN})
        assert ready.status_code==200 and 'private-test-token' not in ready.text
        assert 'HttpOnly' in ready.headers['set-cookie'] and 'SameSite=strict' in ready.headers['set-cookie']
        assert client.get('/api/platform/projects').status_code==200
        assert client.post('/api/platform/projects',json={'project':{'id':'p','name':'Study'}}).status_code==403
        assert client.post('/api/platform/projects',json={'project':{'id':'p','name':'Study'}},headers={'Origin':ORIGIN}).status_code==200
        assert client.post('/api/platform/projects',json={},headers={'Origin':'https://attacker.invalid','Authorization':'Basic ignored'}).status_code==401


def test_spa_does_not_swallow_missing_api_assets_or_files(tmp_path):
    with browser(tmp_path) as client:
        client.post('/api/session/bootstrap',headers={'Origin':ORIGIN})
        assert client.get('/inputs').status_code==200
        for path in ['/assets/absent.js','/api/platform/absent','/api/platform/files/not-owned?project_id=p','/unknown-route']:
            response=client.get(path)
            assert response.status_code!=200
            assert 'HTTP routing fixture' not in response.text


def test_http_and_cli_service_share_project_revision_and_approval_store(tmp_path):
    from typer.testing import CliRunner
    from igem_drylab.software.cli import app
    root=tmp_path/'workspace'
    runner=CliRunner()
    value=runner.invoke(app,['--data-dir',str(root),'--json','project','create','--name','Shared study'])
    assert value.exit_code==0,value.output
    import json
    project=json.loads(value.stdout)
    backend=create_app(data_dir=root,session_token='test',discover_tools=False)
    with TestClient(backend) as client:
        response=client.get('/api/platform/projects/'+project['id'],headers={'X-FusionLab-Token':'test'})
        assert response.status_code==200 and response.json()['name']=='Shared study'
    check=runner.invoke(app,['--data-dir',str(root),'--json','check-inputs','--project',project['id'],'--through','M2'])
    assert check.exit_code==2
    assert json.loads(check.stdout)['missing'][0]['field_path']=='scientific_project'


def test_port_busy_reports_problem_without_silently_using_other_service(tmp_path):
    import socket
    from igem_drylab.software.web import serve_local
    with socket.socket() as owned:
        owned.bind(('127.0.0.1',0));owned.listen()
        frontend=tmp_path/'frontend';frontend.mkdir();(frontend/'index.html').write_text('fixture')
        with pytest.raises(RuntimeError,match='--port 0'):
            serve_local(port=owned.getsockname()[1],data_dir=tmp_path/'workspace',frontend_dir=frontend)
