"""Local-only browser page for the offline evidence retriever.

This intentionally exposes no upload, arbitrary command, or API-key endpoint.
Start it with a fixed evidence path and visit the printed localhost URL.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .qa import answer_question

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GLOSS Literature Evidence Explorer</title>
<style>
/* Foundation */
:root { color-scheme: dark; --bg:#07111f; --panel:rgba(14,31,53,.76); --line:rgba(170,210,246,.16); --text:#edf6ff; --muted:#9aafc4; --cyan:#61d9e8; --violet:#a78bfa; --green:#68d391; --red:#ff8295; }
* { box-sizing:border-box } body { margin:0; min-width:320px; color:var(--text); font:16px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:radial-gradient(circle at 14% 12%,rgba(44,166,199,.16),transparent 28rem),radial-gradient(circle at 86% 18%,rgba(129,93,218,.15),transparent 26rem),var(--bg); }
body:before { content:""; position:fixed; inset:0; pointer-events:none; opacity:.3; background-image:linear-gradient(rgba(122,188,224,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(122,188,224,.045) 1px,transparent 1px); background-size:36px 36px; mask-image:linear-gradient(#000,transparent 90%); }
.shell { width:min(1120px,calc(100% - 36px)); margin:0 auto; padding:28px 0 54px; position:relative } .glass { border:1px solid var(--line); background:var(--panel); box-shadow:0 20px 70px rgba(0,0,0,.18); backdrop-filter:blur(14px); border-radius:18px; }
/* Header */
header { display:flex; gap:24px; justify-content:space-between; align-items:flex-start; padding:24px 26px; } .brand { color:var(--cyan); letter-spacing:.18em; font-size:.78rem; font-weight:800 } .project { margin-top:4px; color:var(--muted); font-size:.78rem } h1 { margin:12px 0 2px; font-size:clamp(2rem,5vw,3.4rem); letter-spacing:-.04em; line-height:1.05 } .subtitle { margin:0; color:var(--muted); font-size:1.04rem }
.badges { display:flex; flex-wrap:wrap; gap:7px; margin-top:16px } .badge { border:1px solid var(--line); border-radius:999px; padding:3px 9px; color:#c9d8e8; font-size:.7rem; letter-spacing:.08em; font-weight:700 } .badge.tool { color:#c9f8ff; border-color:rgba(97,217,232,.4) }.badge:before { content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:currentColor; margin:0 6px 1px 0 }
.connection { min-width:205px; text-align:right; color:var(--muted); font-size:.84rem }.health { display:inline-flex; align-items:center; gap:8px; color:var(--text); font-weight:650 }.dot { width:9px; height:9px; border-radius:50%; background:#8494a7; box-shadow:0 0 0 4px rgba(132,148,167,.1) }.dot.connected { background:var(--green); box-shadow:0 0 0 4px rgba(104,211,145,.12) }.dot.unavailable { background:var(--red); box-shadow:0 0 0 4px rgba(255,130,149,.12) }.connection small { display:block; margin-top:7px }
/* Search */
.search-panel { margin-top:18px; padding:24px } .command { display:flex; align-items:center; gap:12px; padding:8px 8px 8px 17px; border:1px solid rgba(120,205,230,.3); background:rgba(3,12,25,.58); border-radius:14px; box-shadow:inset 0 0 0 1px rgba(255,255,255,.025) }.search-icon { color:var(--cyan); font-size:1.35rem } input { min-width:0; flex:1; color:var(--text); background:transparent; border:0; outline:0; font:inherit; font-size:1.05rem; padding:10px 0 } input::placeholder { color:#71879f } button { cursor:pointer; border:0; border-radius:10px; color:#03101c; background:linear-gradient(120deg,var(--cyan),#94b9ff); padding:11px 17px; font:700 .9rem/1 system-ui; transition:transform .16s ease,filter .16s ease } button:hover { filter:brightness(1.08); transform:translateY(-1px) } button:disabled { cursor:wait; opacity:.65; transform:none }.chips { display:flex; flex-wrap:wrap; gap:8px; margin:15px 0 8px }.chip { padding:7px 10px; color:#c7d8e9; border:1px solid var(--line); background:rgba(255,255,255,.025); font:inherit; font-size:.82rem }.hint,.disclaimer { color:var(--muted); font-size:.83rem }.disclaimer { margin:12px 0 0; padding-left:12px; border-left:2px solid rgba(97,217,232,.45) }
/* Results */
#results { margin-top:20px }.initial,.empty,.error { padding:36px 26px; text-align:center; color:var(--muted) }.initial-mark { margin:auto auto 12px; width:48px; height:48px; border:1px solid rgba(97,217,232,.35); border-radius:16px; display:grid; place-items:center; color:var(--cyan); font-size:1.35rem }.results-head { display:flex; align-items:end; justify-content:space-between; gap:18px; padding:0 4px 13px }.eyebrow { color:var(--cyan); font-size:.74rem; font-weight:800; letter-spacing:.13em }.results-head h2 { margin:2px 0 0; font-size:1.35rem }.query { max-width:410px; color:var(--muted); font-size:.82rem; text-align:right }.latency { color:#c6d8ea; white-space:nowrap }.cards { display:grid; gap:14px }.card { padding:21px 23px }.card-top { display:flex; gap:14px; justify-content:space-between; align-items:start }.rank { color:var(--cyan); font-weight:800; font-size:.76rem; letter-spacing:.1em }.card h3 { margin:3px 0 0; font-size:1.2rem; line-height:1.3 }.relevance { min-width:105px; color:var(--muted); font-size:.78rem; text-align:right }.meter { height:5px; margin-top:6px; border-radius:99px; background:#1c3047; overflow:hidden }.meter i { display:block; height:100%; background:linear-gradient(90deg,var(--cyan),var(--violet)); border-radius:inherit }.quote { margin:18px 0 14px; padding:14px 16px; border-left:3px solid var(--cyan); background:rgba(97,217,232,.055); color:#e6f5ff; font-size:1.02rem }.metadata { display:flex; flex-wrap:wrap; gap:8px; color:var(--muted); font-size:.78rem }.metadata span { border:1px solid var(--line); border-radius:7px; padding:3px 7px }.actions { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px }.action { display:inline-block; color:#bdeeff; border:1px solid rgba(97,217,232,.32); border-radius:8px; padding:6px 9px; background:transparent; font:600 .8rem system-ui; text-decoration:none }.action:hover { background:rgba(97,217,232,.09) } details { margin-top:15px; color:var(--muted); font-size:.85rem } summary { cursor:pointer; color:#c5d5e6 } .fields { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:7px; margin-top:9px }.field { padding:7px; background:rgba(255,255,255,.035); border-radius:6px; overflow-wrap:anywhere }.field b { display:block; color:#d7e6f3; font-size:.72rem; margin-bottom:2px }
.skeleton { height:166px; padding:20px; overflow:hidden }.shimmer { height:12px; margin:10px 0; border-radius:8px; background:linear-gradient(90deg,#12263c 25%,#1c3854 37%,#12263c 63%); background-size:400% 100%; animation:shine 1.2s infinite }.shimmer.short { width:42% }.footer { display:flex; justify-content:space-between; gap:16px; margin-top:23px; padding:14px 5px; color:var(--muted); font-size:.78rem }.workflow { color:#c4d5e8 }.workflow b { color:var(--cyan) } #raw { margin-top:16px; color:var(--muted) } pre { max-height:320px; overflow:auto; padding:13px; color:#c6d7e8; background:#050c16; border:1px solid var(--line); border-radius:10px; white-space:pre-wrap; overflow-wrap:anywhere }
@keyframes shine { to { background-position:-400% 0 } } @media (max-width:720px) { .shell{width:min(100% - 22px,1120px);padding-top:11px} header{padding:21px;display:block}.connection{text-align:left;margin-top:18px}.search-panel{padding:15px}.command{align-items:stretch;flex-wrap:wrap}.command input{flex-basis:80%}.results-head,.card-top,.footer{align-items:flex-start;flex-direction:column}.query,.relevance{text-align:left}.relevance{width:100%}.meter{max-width:160px} } @media (prefers-reduced-motion:reduce) { *,*:before,*:after { animation-duration:.01ms!important; transition-duration:.01ms!important } }
</style></head><body><div class="shell">
<header class="glass"><div><div class="brand">GLOSS</div><div class="project">Glabridin through LLPS-Organized Sequential Synthesis</div><h1>Literature Evidence Explorer</h1><p class="subtitle">Search locally curated scientific evidence with explicit provenance.</p><div class="badges"><span class="badge tool">AGENT TOOL</span><span class="badge">LOCAL EVIDENCE</span><span class="badge">TRACEABLE</span><span class="badge">REVIEW REQUIRED</span></div></div><div class="connection"><div class="health"><span class="dot" id="health-dot"></span><span id="health-text">Checking evidence database…</span></div><small>Local only · No generated claims</small></div></header>
<section class="glass search-panel"><form id="question-form"><div class="command"><span class="search-icon" aria-hidden="true">⌕</span><input id="question" required autocomplete="off" placeholder="Ask about an enzyme, parameter, pathway, or experimental result…"><button id="search-button" type="submit">Search Evidence</button></div></form><div class="chips" id="chips"></div><div class="hint">For this demo, English scientific queries provide the most reliable retrieval.</div><p class="disclaimer">Retrieved evidence is not automatically a validated parameter. Review the quoted source before using it in the production model.</p></section>
<section id="results" aria-live="polite"></section><footer class="footer"><span class="workflow"><b>Retrieval</b> → Review → Approval</span><span><b>Agent integration</b> · <code>igem.literature.qa</code></span></footer><details id="raw"><summary>Raw response</summary><pre id="raw-response"></pre></details>
</div><script>
const examples = ['What evidence reports OC activity?', 'What evidence supports DMT activity on intermediate 9?', 'Which evidence reports glabridin production?', 'What evidence is available for DMT kinetics?'];
const form = document.getElementById('question-form'); const input = document.getElementById('question'); const results = document.getElementById('results'); const button = document.getElementById('search-button'); const raw = document.getElementById('raw-response');
function text(tag, value, className) { const node=document.createElement(tag); node.textContent=value || ''; if(className) node.className=className; return node; }
function setStatus(state, message) { const dot=document.getElementById('health-dot'); dot.className='dot '+state; document.getElementById('health-text').textContent=message; }
async function checkHealth() { try { const response=await fetch('/health'); const data=await response.json(); setStatus(data.ok ? 'connected' : 'unavailable', data.ok ? 'Evidence database connected' : 'Evidence database unavailable'); } catch (_) { setStatus('unavailable','Evidence database unavailable'); } }
function renderInitial() { const panel=document.createElement('div');panel.className='initial glass';panel.append(text('div','⌬','initial-mark'),text('div','Ask a question to search the local evidence database.'));results.replaceChildren(panel); }
function renderLoading() { const holder=document.createElement('div'); holder.className='cards'; for(let i=0;i<3;i++){ const card=document.createElement('div'); card.className='glass skeleton'; ['short','',''].forEach(kind=>{const line=document.createElement('div');line.className='shimmer '+kind;card.append(line)});holder.append(card) } results.replaceChildren(holder); }
function renderNoMatch() { results.replaceChildren(text('div','No matching local evidence found. Try a more specific term such as an enzyme name, intermediate, or parameter.','empty glass')); }
function renderError(message, database) { results.replaceChildren(text('div',database ? 'Evidence database unavailable. Check the evidence path used when starting the server.' : 'Unable to complete the search. '+message,'error glass')); }
function renderFields(fields) { const details=document.createElement('details'); details.append(text('summary','Structured record')); const grid=document.createElement('div');grid.className='fields'; Object.entries(fields || {}).forEach(([key,value])=>{const field=document.createElement('div');field.className='field';field.append(text('b',key),text('span',typeof value==='object'?JSON.stringify(value):String(value)));grid.append(field)}); details.append(grid); return details; }
function validDoi(doi) { return typeof doi==='string' && /^10\.\S+\/\S+$/i.test(doi.trim()); }
function renderSourceCard(source, index) { const card=document.createElement('article');card.className='card glass'; const top=document.createElement('div');top.className='card-top'; const heading=document.createElement('div'); heading.append(text('div','EVIDENCE '+String(index+1).padStart(2,'0'),'rank'),text('h3',source.title || 'Untitled source')); const relevance=document.createElement('div');relevance.className='relevance';const score=Math.max(0,Math.min(1,Number(source.score)||0));relevance.append(text('div','Relevance '+score.toFixed(2)),Object.assign(document.createElement('div'),{className:'meter'}));relevance.lastChild.append(Object.assign(document.createElement('i'),{style:'width:'+(score*100)+'%'}));top.append(heading,relevance);card.append(top,text('blockquote',source.evidence || 'No quoted evidence text available.','quote')); const meta=document.createElement('div');meta.className='metadata';if(source.source_file)meta.append(text('span','Source: '+source.source_file));if(source.record_id)meta.append(text('span','Record: '+source.record_id));meta.append(text('span',validDoi(source.doi)?'DOI-LINKED':'LOCAL RECORD'));card.append(meta);if(validDoi(source.doi)){const actions=document.createElement('div');actions.className='actions';const link=document.createElement('a');link.className='action';link.textContent='Open DOI';link.href='https://doi.org/'+encodeURIComponent(source.doi.trim());link.target='_blank';link.rel='noopener noreferrer';const copy=document.createElement('button');copy.className='action';copy.type='button';copy.textContent='Copy DOI';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(source.doi);copy.textContent='Copied';setTimeout(()=>copy.textContent='Copy DOI',1100)}catch(_){copy.textContent='Copy unavailable'}});actions.append(link,copy);card.append(actions)}if(source.fields && Object.keys(source.fields).length)card.append(renderFields(source.fields));return card; }
function renderResponse(payload, question, latency) { raw.textContent=JSON.stringify(payload,null,2); if(payload.status==='no_match'){renderNoMatch();return} if(payload.status==='database_unavailable'){renderError('',true);return} if(payload.status!=='retrieved'){renderError(payload.answer || 'Request failed.',false);return} const head=document.createElement('div');head.className='results-head';const left=document.createElement('div');left.append(text('div','EVIDENCE RETRIEVED','eyebrow'),text('h2',payload.sources.length+' matching record'+(payload.sources.length===1?'':'s')+' found in the local evidence database.'));const query=text('div','QUERY\n“'+question+'” · '+latency+' ms','query');head.append(left,query);const cards=document.createElement('div');cards.className='cards';payload.sources.forEach((source,index)=>cards.append(renderSourceCard(source,index)));results.replaceChildren(head,cards); }
async function submitQuestion(question) { if(!question.trim() || button.disabled)return; button.disabled=true;button.textContent='Searching local evidence…';renderLoading();const started=performance.now();try{const response=await fetch('/api/qa',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});const payload=await response.json();renderResponse(payload,question,Math.round(performance.now()-started));}catch(_){renderError('Please try again.',false)}finally{button.disabled=false;button.textContent='Search Evidence'} }
function setupChips(){const holder=document.getElementById('chips');examples.forEach(example=>{const chip=document.createElement('button');chip.type='button';chip.className='chip';chip.textContent=example;chip.addEventListener('click',()=>{input.value=example;submitQuestion(example)});holder.append(chip)})}
form.addEventListener('submit',event=>{event.preventDefault();submitQuestion(input.value)});setupChips();renderInitial();checkHealth();
</script></body></html>"""


def health_payload(evidence_path: Path) -> dict[str, object]:
    """Stable `/health` payload used by the browser connection indicator."""
    return {"ok": evidence_path.is_file(), "evidence_path": str(evidence_path)}


def make_handler(evidence_path: Path) -> type[BaseHTTPRequestHandler]:
    """Build the fixed-database handler for serving and local HTTP tests."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path == "/health":
                self._json(health_payload(evidence_path))
            elif urlparse(self.path).path == "/":
                body = PAGE.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers(); self.wfile.write(body)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/api/qa":
                self.send_error(HTTPStatus.NOT_FOUND); return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 20_000:
                    raise ValueError("request body is too large")
                payload = json.loads(self.rfile.read(length))
                question = payload.get("question") if isinstance(payload, dict) else None
                if not isinstance(question, str) or not question.strip():
                    raise ValueError("question must be a non-empty string")
                self._json(answer_question(question, evidence_path))
            except (ValueError, json.JSONDecodeError) as exc:
                self._json({"ok": False, "status": "invalid_request", "answer": str(exc), "sources": []}, HTTPStatus.BAD_REQUEST)

        def _json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return
    return Handler


def serve(evidence_path: Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve a fixed evidence file. Bind localhost by default for safety."""
    server = ThreadingHTTPServer((host, port), make_handler(evidence_path))
    print(f"Evidence QA listening at http://{host}:{port}/ (database: {evidence_path})")
    server.serve_forever()
