from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from igem_drylab.literature.qa import answer_question
from igem_drylab.literature.qa_server import PAGE, health_payload, make_handler


def _evidence_file(tmp_path: Path) -> Path:
    path = tmp_path / "evidence.jsonl"
    path.write_text(json.dumps({"record_id": "oc-1", "title": "OC activity study", "doi": "10.1000/oc", "evidence": "OC activity converts an intermediate in glabridin biosynthesis.", "source_file": "paper.txt", "fields": {"enzyme": "OC", "parameter": "activity"}}) + "\n", encoding="utf-8")
    return path


def test_page_has_public_question_and_results_entries() -> None:
    assert "Literature Evidence Explorer" in PAGE
    assert 'id="question-form"' in PAGE
    assert 'id="results"' in PAGE
    assert 'id="mode"' in PAGE


def test_malicious_source_strings_are_rendered_as_text_not_html(tmp_path) -> None:
    """Execute shipped JS against a strict DOM contract double, not a browser audit."""
    import re
    import subprocess
    helpers=('text','fieldLabel','fieldValue','appendFieldRows','renderFields','renderQuote','validDoi','renderSourceCard')
    functions='\n'.join(re.search(r'^function '+name+r'\([^\n]+',PAGE,re.M).group(0) for name in helpers)
    source=dict(title='<img src=x onerror="globalThis.pwned=true">',evidence='<script>globalThis.pwned=true</script>',
        source_file='<svg onload="globalThis.pwned=true">',record_id='fixture',score=.5,doi='javascript:alert(1)',
        fields={'unsafe':'<b>literal markup</b>'})
    harness=r'''
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.classList={add(){}};this.textContent='';}
  append(...nodes){this.children.push(...nodes);}
  get lastChild(){return this.children.at(-1);}
  set innerHTML(v){throw Error('HTML sink used');}
  set outerHTML(v){throw Error('HTML sink used');}
  insertAdjacentHTML(){throw Error('HTML sink used');}
  addEventListener(){}
}
const document={createElement:tag=>new Element(tag),write(){throw Error('HTML sink used');}};
globalThis.pwned=false;
'''
    script=tmp_path/'source-render.js'
    script.write_text(harness+functions+'\nconst card=renderSourceCard('+json.dumps(source)+',0);\n'+r'''
function flatten(node){return [node,...node.children.flatMap(flatten)];}
const nodes=flatten(card);
console.log(JSON.stringify({texts:nodes.map(n=>n.textContent),tags:nodes.map(n=>n.tag),pwned:globalThis.pwned}));
''',encoding='utf-8')
    run=subprocess.run(['node',str(script)],capture_output=True,text=True,check=True,timeout=15)
    rendered=json.loads(run.stdout)
    for field in ('title','evidence'):
        assert source[field] in rendered['texts']
    assert source['fields']['unsafe'] in rendered['texts']
    assert not {'script','img','svg','a'} & set(rendered['tags'])
    assert rendered['pwned'] is False


def test_health_contract_is_unchanged(tmp_path: Path) -> None:
    evidence = _evidence_file(tmp_path)
    assert health_payload(evidence) == {"ok": True, "evidence_path": str(evidence)}
    assert health_payload(tmp_path / "missing.jsonl")["ok"] is False


def test_local_http_demo_smoke_preserves_root_health_and_qa_routes(tmp_path: Path) -> None:
    evidence = _evidence_file(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(evidence))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/health") as response:
            assert json.loads(response.read())["ok"] is True
        request = Request(base + "/api/qa", data=json.dumps({"question": "OC activity"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request) as response:
            assert json.loads(response.read())["status"] == "retrieved"
        synthesis_request = Request(base + "/api/qa", data=json.dumps({"question": "OC activity", "mode": "synthesize", "semantic_enabled": True}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(synthesis_request) as response:
            payload = json.loads(response.read())
            assert payload["status"] == "synthesis_error"
            assert payload["sources"]
        with urlopen(base + "/") as response:
            assert b"Literature Evidence Explorer" in response.read()
    finally:
        server.shutdown(); server.server_close(); worker.join(timeout=2)


def test_retrieved_response_keeps_status_answer_and_sources_contract(tmp_path: Path) -> None:
    response = answer_question("What evidence reports OC activity?", _evidence_file(tmp_path))
    assert response["status"] == "retrieved"
    assert isinstance(response["answer"], str)
    source = response["sources"][0]
    assert {"title", "doi", "evidence", "score", "record_id", "source_file", "fields"} <= set(source)


def test_no_match_and_database_unavailable_states_are_backend_compatible(tmp_path: Path) -> None:
    assert answer_question("unrelated-token", _evidence_file(tmp_path))["status"] == "no_match"
    assert answer_question("OC", tmp_path / "missing.jsonl")["status"] == "database_unavailable"
