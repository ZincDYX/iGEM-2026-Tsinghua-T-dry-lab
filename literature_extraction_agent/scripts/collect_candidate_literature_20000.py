import csv
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict

import requests


ROOT = Path.cwd()
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

API_TXT = ROOT / "API.txt"
TARGET = 20000
CSV_PATH = OUT / "candidate_literature_20000.csv"
JSONL_PATH = OUT / "candidate_literature_20000.jsonl"
STATE_PATH = OUT / "candidate_literature_20000_state.json"
SUMMARY_PATH = OUT / "candidate_literature_20000_summary.json"

SCOPUS_ENDPOINT = "https://api.elsevier.com/content/search/scopus"
WOS_ENDPOINT = "https://api.clarivate.com/apis/wos-starter/v1/documents"

KEYWORD_GROUPS = [
    {
        "label": "regulation",
        "description": "调控关键词",
        "query": '("concentration dependent" OR "threshold" OR "bistable" OR "switch-like" OR "nonlinear response" OR "cooperative assembly") AND ("enzyme activity" OR "metabolic reaction" OR "biosynthetic pathway" OR "product formation" OR "in vivo catalysis")',
    },
    {
        "label": "product",
        "description": "产物关键词",
        "query": '("flavonoid" OR "isoflavonoid" OR "pterocarpan" OR "isoprenoid" OR "plant natural product" OR "specialized metabolite") AND ("yeast" OR "Saccharomyces cerevisiae" OR "metabolic engineering" OR "heterologous biosynthesis" OR "titer improvement")',
    },
    {
        "label": "yeast_inclusion",
        "description": "酵母内包涵体",
        "query": '("Saccharomyces cerevisiae" OR "yeast") AND ("puncta" OR "foci" OR "granule" OR "body" OR "aggregate" OR "inclusion body" OR "protein condensate" OR "liquid droplet") AND ("enzyme" OR "metabolism" OR "biosynthesis" OR "heterologous expression")',
    },
    {
        "label": "llps",
        "description": "LLPS关键词",
        "query": '("phase separation" OR "phase transition" OR "membraneless organelle" OR "biomolecular condensate" OR "protein assembly" OR "protein aggregate" OR "intracellular compartment") AND ("metabolic engineering" OR "synthetic biology" OR "enzyme engineering" OR "pathway optimization" OR "metabolic flux" OR "enzyme colocalization" OR "metabolic channeling")',
    },
]

COLUMNS = [
    "candidate_id",
    "dedupe_key",
    "source_apis",
    "keyword_groups",
    "keyword_description",
    "title",
    "doi",
    "year",
    "journal",
    "authors",
    "scopus_eid",
    "wos_uid",
    "citedby_count",
    "document_type",
    "openaccess",
    "source_links",
    "abstract",
    "raw_source_count",
]


def parse_keys() -> tuple[str, str]:
    text = API_TXT.read_text(encoding="utf-8")
    elsevier = (
        re.search(r"ELSEVIER_API_KEY='([^']+)'", text)
        or re.search(r"--elsevier-key\s+(?:ELSEVIER_API_KEY=)?'([^']+)'", text)
    )
    wos = re.search(r"WOS_API_KEY='([^']+)'", text)
    if not elsevier:
        raise SystemExit("API.txt missing ELSEVIER_API_KEY")
    if not wos:
        raise SystemExit("API.txt missing WOS_API_KEY")
    return elsevier.group(1), wos.group(1)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(clean_text(v) for v in value if v)
    return " ".join(str(value).split())


def norm_title(title: str) -> str:
    text = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower().strip()
    return text[:220]


def dedupe_key(doi: str, title: str) -> str:
    doi = (doi or "").strip().lower()
    if doi:
        return "doi:" + doi
    title_key = norm_title(title)
    return "title:" + title_key if title_key else ""


def add_value(existing: str, value: Any) -> str:
    value = clean_text(value)
    if not value:
        return existing or ""
    parts = [p for p in (existing or "").split("; ") if p]
    if value not in parts:
        parts.append(value)
    return "; ".join(parts)


def load_records() -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    seed_paths = [CSV_PATH, OUT / "candidate_literature_2000.csv"]
    for path in seed_paths:
        if not path.exists() or path.stat().st_size == 0:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                key = row.get("dedupe_key") or dedupe_key(row.get("doi", ""), row.get("title", ""))
                if key and key not in records:
                    records[key] = dict(row)
        if records:
            break
    return records


def add_record(records: Dict[str, Dict[str, Any]], rec: Dict[str, Any]) -> None:
    key = dedupe_key(rec.get("doi", ""), rec.get("title", ""))
    if not key:
        return
    rec["dedupe_key"] = key
    if key not in records:
        records[key] = rec
        return
    cur = records[key]
    for field in ["source_apis", "keyword_groups", "source_links", "scopus_eid", "wos_uid", "document_type"]:
        cur[field] = add_value(cur.get(field, ""), rec.get(field, ""))
    for field in ["doi", "title", "year", "journal", "authors", "openaccess"]:
        if not cur.get(field) and rec.get(field):
            cur[field] = rec[field]
    try:
        cur["citedby_count"] = max(int(cur.get("citedby_count") or 0), int(rec.get("citedby_count") or 0))
    except Exception:
        pass
    cur["raw_source_count"] = int(cur.get("raw_source_count") or 1) + 1


def parse_scopus(entry: Dict[str, Any], group: Dict[str, str]) -> Dict[str, Any]:
    links = entry.get("link") or []
    link_text = ""
    if isinstance(links, list):
        link_text = "; ".join(l.get("@href", "") for l in links if isinstance(l, dict) and l.get("@href"))
    return {
        "source_apis": "scopus",
        "keyword_groups": group["label"],
        "keyword_description": group["description"],
        "title": clean_text(entry.get("dc:title")),
        "doi": clean_text(entry.get("prism:doi")),
        "year": clean_text(str(entry.get("prism:coverDate", ""))[:4]),
        "journal": clean_text(entry.get("prism:publicationName")),
        "authors": clean_text(entry.get("dc:creator")),
        "scopus_eid": clean_text(entry.get("eid")),
        "wos_uid": "",
        "citedby_count": clean_text(entry.get("citedby-count")),
        "document_type": clean_text(entry.get("subtypeDescription") or entry.get("subtype")),
        "openaccess": clean_text(entry.get("openaccess") or entry.get("openaccessFlag")),
        "source_links": link_text,
        "abstract": "",
        "raw_source_count": 1,
    }


def parse_wos(hit: Dict[str, Any], group: Dict[str, str]) -> Dict[str, Any]:
    source = hit.get("source") or {}
    names = hit.get("names") or {}
    authors = names.get("authors") or []
    identifiers = hit.get("identifiers") or {}
    citations = hit.get("citations") or []
    links = hit.get("links") or {}
    cited = citations[0].get("count", "") if citations and isinstance(citations[0], dict) else ""
    return {
        "source_apis": "wos_starter",
        "keyword_groups": group["label"],
        "keyword_description": group["description"],
        "title": clean_text(hit.get("title")),
        "doi": clean_text(identifiers.get("doi") or identifiers.get("DOI") or ""),
        "year": clean_text(source.get("publishYear")),
        "journal": clean_text(source.get("sourceTitle")),
        "authors": clean_text("; ".join(a.get("displayName", "") for a in authors if isinstance(a, dict))),
        "scopus_eid": "",
        "wos_uid": clean_text(hit.get("uid")),
        "citedby_count": clean_text(cited),
        "document_type": clean_text(hit.get("types") or hit.get("sourceTypes")),
        "openaccess": "",
        "source_links": "; ".join(v for v in links.values() if isinstance(v, str)),
        "abstract": "",
        "raw_source_count": 1,
    }


def default_state() -> Dict[str, Any]:
    tasks = []
    for group in KEYWORD_GROUPS:
        tasks.append({"source": "scopus", "group": group["label"], "start": 0, "count": 25, "done": False, "total": None, "pages": 0})
        tasks.append({"source": "wos_starter", "group": group["label"], "page": 1, "limit": 50, "done": False, "total": None, "pages": 0})
    return {"tasks": tasks, "raw_seen": 0}


def load_state() -> Dict[str, Any]:
    if STATE_PATH.exists() and STATE_PATH.stat().st_size:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return default_state()


def save_outputs(records: Dict[str, Dict[str, Any]], state: Dict[str, Any]) -> None:
    rows = list(records.values())[:TARGET]
    for idx, row in enumerate(rows, start=1):
        row["candidate_id"] = idx
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "target": TARGET,
        "unique_candidates": len(rows),
        "raw_seen": state.get("raw_seen", 0),
        "active_tasks": sum(1 for t in state["tasks"] if not t.get("done")),
        "tasks": state["tasks"],
        "csv": str(CSV_PATH),
        "jsonl": str(JSONL_PATH),
        "state": str(STATE_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def request_json(session: requests.Session, url: str, *, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    for attempt in range(3):
        resp = session.get(url, headers=headers, params=params, timeout=35)
        if resp.status_code in {429, 500, 502, 503, 504} and attempt < 2:
            wait = resp.headers.get("Retry-After")
            try:
                wait_s = float(wait) if wait else 1.5 * (2**attempt)
            except Exception:
                wait_s = 1.5 * (2**attempt)
            time.sleep(wait_s)
            continue
        if resp.status_code >= 400:
            raise RuntimeError(f"{resp.status_code}: {resp.text[:300]}")
        return resp.json()
    raise RuntimeError("request failed")


def main(max_requests: int = 600) -> None:
    elsevier_key, wos_key = parse_keys()
    group_by_label = {g["label"]: g for g in KEYWORD_GROUPS}
    records = load_records()
    state = load_state()
    session = requests.Session()
    requests_done = 0
    while len(records) < TARGET and any(not t.get("done") for t in state["tasks"]) and requests_done < max_requests:
        for task in state["tasks"]:
            if len(records) >= TARGET or requests_done >= max_requests:
                break
            if task.get("done"):
                continue
            group = group_by_label[task["group"]]
            try:
                if task["source"] == "scopus":
                    js = request_json(
                        session,
                        SCOPUS_ENDPOINT,
                        headers={"X-ELS-APIKey": elsevier_key, "Accept": "application/json"},
                        params={"query": f'TITLE-ABS-KEY({group["query"]})', "count": task["count"], "start": task["start"]},
                    )
                    sr = js.get("search-results", {})
                    task["total"] = int(sr.get("opensearch:totalResults") or 0)
                    entries = sr.get("entry") or []
                    if not entries:
                        task["done"] = True
                    for entry in entries:
                        if isinstance(entry, dict) and entry.get("dc:title"):
                            add_record(records, parse_scopus(entry, group))
                            state["raw_seen"] = state.get("raw_seen", 0) + 1
                    task["start"] += len(entries)
                    task["pages"] += 1
                    if task["start"] >= task["total"] or len(entries) < task["count"]:
                        task["done"] = True
                else:
                    js = request_json(
                        session,
                        WOS_ENDPOINT,
                        headers={"X-ApiKey": wos_key, "Accept": "application/json"},
                        params={"db": "WOS", "q": f'TS=({group["query"]})', "limit": task["limit"], "page": task["page"], "detail": "full"},
                    )
                    md = js.get("metadata") or {}
                    task["total"] = int(md.get("total") or 0)
                    hits = js.get("hits") or []
                    if not hits:
                        task["done"] = True
                    for hit in hits:
                        if isinstance(hit, dict) and hit.get("title"):
                            add_record(records, parse_wos(hit, group))
                            state["raw_seen"] = state.get("raw_seen", 0) + 1
                    task["page"] += 1
                    task["pages"] += 1
                    if (task["page"] - 1) * task["limit"] >= task["total"] or len(hits) < task["limit"]:
                        task["done"] = True
                requests_done += 1
                if requests_done % 25 == 0:
                    save_outputs(records, state)
                    print(f"progress unique={len(records)} requests={requests_done} active={sum(1 for t in state['tasks'] if not t.get('done'))}", flush=True)
                time.sleep(0.05)
            except Exception as ex:
                task["last_error"] = str(ex)
                task["done"] = True
                requests_done += 1
    save_outputs(records, state)
    print(json.dumps(json.loads(SUMMARY_PATH.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
