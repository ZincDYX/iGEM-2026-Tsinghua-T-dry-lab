"""Versioned, editable workflow instructions, not executable extensions."""
from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import Field
import yaml

from .models import Contract, WorkflowError
from .store import canonical, now


class SkillInput(Contract):
    text: str = Field(min_length=1,max_length=65536)
    enabled: bool = False
    expected_revision: int | None = None


class SkillView(Contract):
    id: str
    name: str
    description: str
    trigger: str
    version: str
    source: str
    license: str
    enabled: bool
    revision: int
    text: str
    updated_at: str
    execution: Literal['instructions_only'] = 'instructions_only'


class SkillPage(Contract):
    items: list[SkillView]
    has_more: bool


class Skills:
    def __init__(self, store, boundary):
        self.store,self.boundary = store,boundary
        with store.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS workspace_skills(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')

    def list(self, offset=0):
        import json
        with self.store.connection() as db:
            rows = db.execute('SELECT payload FROM workspace_skills ORDER BY id LIMIT 21 OFFSET ?',(offset,)).fetchall()
        return SkillPage(items=[SkillView.model_validate(json.loads(row[0])) for row in rows[:20]],has_more=len(rows)>20)

    def save(self, request: SkillInput, skill_id=None):
        import json
        self.boundary.check(request.text)
        if not request.text.startswith('---\n') and not request.text.startswith('---\r\n'):
            raise WorkflowError('skill_requires_yaml_frontmatter')
        parts=request.text.split('---',2)
        if len(parts)!=3: raise WorkflowError('skill_requires_yaml_frontmatter')
        try: metadata=yaml.safe_load(parts[1])
        except yaml.YAMLError: raise WorkflowError('skill_frontmatter_invalid') from None
        required=('name','description','trigger','version','source','license')
        if not isinstance(metadata,dict) or any(not isinstance(metadata.get(key),str) or not metadata[key].strip() for key in required):
            raise WorkflowError('skill_name_description_trigger_version_source_license_required')
        # Source metadata is prose, not a path to execute or permission grant.
        self.boundary.check(metadata)
        skill_id = skill_id or str(uuid4())
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload FROM workspace_skills WHERE id=?',(skill_id,)).fetchone()
            revision = json.loads(row[0])['revision'] if row else 0
            if revision and request.expected_revision != revision:
                raise WorkflowError('skill_revision_changed',status_code=409)
            record=SkillView(id=skill_id,**{key:metadata[key] for key in required},enabled=request.enabled,
                revision=revision+1,text=request.text,updated_at=now())
            db.execute('INSERT OR REPLACE INTO workspace_skills VALUES(?,?)',(skill_id,canonical(record.model_dump(mode='json'))))
        return record

    def guidance(self):
        """Bounded optional model guidance, never scientific gate input."""
        import json
        with self.store.connection() as db:
            rows=db.execute('SELECT payload FROM workspace_skills ORDER BY id LIMIT 100').fetchall()
        text='\n'.join(record['text'] for row in rows if (record:=json.loads(row[0]))['enabled'])
        return text[:6000]
