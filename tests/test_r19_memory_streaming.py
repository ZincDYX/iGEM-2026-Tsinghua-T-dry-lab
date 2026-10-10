"""Independent JSONL ordering and bounded tail-read software probes."""
import json
from pathlib import Path
from igem_drylab.agent.memory import AgentMemory,MemoryRecord


def test_recent_reads_tail_not_all_history_and_retains_utf8_and_invalid_line_behavior(tmp_path,monkeypatch):
    path=tmp_path/"memory.jsonl"
    memory=AgentMemory(path)
    rows=[MemoryRecord(record_id=str(i),content="历史中文"+"A"*1000) for i in range(200)]
    for row in rows:memory.append(row)
    with path.open("a",encoding="utf-8") as handle:handle.write("invalid-json\n\n")
    read=[]
    original=Path.open
    class Tracked:
        def __init__(self,handle):self.handle=handle
        def __enter__(self):return self
        def __exit__(self,*args):return self.handle.__exit__(*args)
        def __getattr__(self,key):return getattr(self.handle,key)
        def read(self,size=-1):
            value=self.handle.read(size);read.append(len(value));return value
    def track(self,*args,**kwargs):
        handle=original(self,*args,**kwargs)
        return Tracked(handle) if self==path and args and args[0]=="rb" else handle
    monkeypatch.setattr(Path,"open",track)
    assert [r["record_id"] for r in memory.load_recent(3)]==["197","198","199"]
    assert sum(read)<path.stat().st_size
    assert memory.load_recent(0)==[]


def test_streamed_search_preserves_exact_lexical_order_including_ties_and_kinds(tmp_path,monkeypatch):
    memory=AgentMemory(tmp_path/"memory.jsonl")
    fixtures=[MemoryRecord(record_id="old-full",kind="parameter",content="OC DMT",created_at="2020-01-01"),
        MemoryRecord(record_id="new-partial",kind="parameter",content="OC",created_at="2026-01-01"),
        MemoryRecord(record_id="tie-first",kind="parameter",content="OC DMT",created_at="2021-01-01"),
        MemoryRecord(record_id="tie-second",kind="parameter",content="OC DMT",created_at="2021-01-01"),
        MemoryRecord(record_id="irrelevant",content="unrelated",created_at="2026-01-01")]
    for row in fixtures:memory.append(row)
    def forbidden():raise AssertionError("search must not materialize full history")
    monkeypatch.setattr(memory,"records",forbidden)
    assert [r.record_id for r in memory.search("OC DMT",limit=3,kinds={"parameter"})]==["tie-first","tie-second","old-full"]
