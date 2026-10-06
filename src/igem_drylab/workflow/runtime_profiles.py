"""Maintainer-owned runtime configuration. No HTTP credential mutation route."""
from hashlib import sha256
import json

from .models import WorkflowError
from .store import canonical


class RuntimeProfiles:
    def __init__(self, store):
        self.store = store

    def install(self, profile_id: str, tools: dict) -> dict:
        """Private maintainer integration; callers never receive its payload."""
        from igem_drylab.pipeline.config import ToolConfig
        checked = {name: ToolConfig.model_validate(value).model_dump(mode="json") for name, value in tools.items()}
        encoded = canonical(checked)
        digest = sha256(encoded.encode()).hexdigest()
        with self.store.connection() as db:
            old = db.execute("SELECT revision,hash FROM runtime_profiles WHERE id=?", (profile_id,)).fetchone()
            revision = old["revision"] if old and old["hash"] == digest else (old["revision"] + 1 if old else 1)
            db.execute("INSERT OR REPLACE INTO runtime_profiles VALUES(?,?,?,?)", (profile_id, revision, digest, encoded))
        return {"id": profile_id, "revision": revision, "hash": digest}

    def get(self, profile_id: str) -> tuple[dict, dict]:
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM runtime_profiles WHERE id=?", (profile_id,)).fetchone()
        if row is None:
            raise WorkflowError("runtime_profile_not_authorized", status_code=403)
        return {"id": row["id"], "revision": row["revision"], "hash": row["hash"]}, json.loads(row["payload"])
