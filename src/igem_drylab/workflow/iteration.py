"""Byte-preserving dependency closure and atomic project/grant publication."""
from hashlib import sha256
from pathlib import Path
import os
import shutil
from tempfile import TemporaryDirectory
from uuid import uuid4

from igem_drylab.resources import default_config_path
from .models import Project, WorkflowError
from .scientific_project import ScientificProject


def rebind_paths(value, replacements):
    if isinstance(value, str) and Path(value).is_absolute():
        return str(replacements.get(Path(value).resolve(), value))
    if isinstance(value, dict):
        return {key: rebind_paths(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [rebind_paths(item, replacements) for item in value]
    return value


def create_iteration(store, boundary, engine, run_id, data_dir):
    frozen = store.run(run_id)
    project = Project.model_validate(frozen["snapshot"]["project"])
    sources = {Path(item["path"]).resolve(): item["sha256"] for item in project.files}
    if project.scientific_project:
        science = ScientificProject.model_validate(project.scientific_project)
        sources.update({item.path.resolve(): item.sha256 for item in science.evidence_files})
    with store.connection() as db:
        bundles = [(row["id"], Path(row["root"]).resolve()) for row in db.execute("SELECT * FROM scientific_bundles")]
    trusted = {default_config_path(name).resolve() for name in ("m1_feature_definitions.yaml", "m1_rules_v3.yaml")}
    unbundled = [source for source in sources if source not in trusted and not any(source.is_relative_to(root) for _, root in bundles)]
    common = Path(os.path.commonpath([str(source.parent) for source in unbundled])) if unbundled else None
    logical = {}
    for source in sources:
        owners = [(identifier, root) for identifier, root in bundles if source.is_relative_to(root)]
        if owners:
            identifier, root = max(owners, key=lambda item: len(item[1].parts))
            logical[source] = Path("bundles") / identifier / source.relative_to(root)
        elif source in trusted:
            logical[source] = Path("trusted-rules") / source.name
        else:
            logical[source] = Path("inputs") / source.relative_to(common)
    identity = str(uuid4())
    imports = (data_dir / "imports").resolve()
    imports.mkdir(parents=True, exist_ok=True)
    published = imports / identity
    committed = False
    try:
        engine.verify_snapshot(frozen, execution_identity=False)
        with TemporaryDirectory(prefix=".iteration-", dir=imports) as directory:
            staging = Path(directory)
            for source, relative in logical.items():
                raw = source.read_bytes()
                if sha256(raw).hexdigest() != sources[source]:
                    raise WorkflowError("iteration_dependency_graph_invalid", logical_files=(relative.as_posix(),))
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            original = project.model_dump(mode="json")
            original.update(id=identity, name=project.name + " · iteration", revision=1,
                            parent_run_id=run_id, parent_snapshot_sha256=frozen["snapshot_hash"])
            draft = Project.model_validate(rebind_paths(original, {source: staging / relative for source, relative in logical.items()}))
            if draft.scientific_project:
                ScientificProject.model_validate(draft.scientific_project).verify()
            # The copied closure is private until the project and all grants commit.
            staging.rename(published)
            draft = Project.model_validate(rebind_paths(draft.model_dump(mode="json"),
                                                       {staging / relative: published / relative for relative in logical.values()}))
            if draft.scientific_project:
                ScientificProject.model_validate(draft.scientific_project).verify()
            with store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                updated = store.save_project(draft, db=db)
                public = boundary.project(updated, db=db)
                db.execute("INSERT INTO scientific_bundles VALUES(?,?)", (identity, str(published)))
            committed = True
            return {"project": public, "parent_run_id": run_id, "parent_snapshot_sha256": frozen["snapshot_hash"],
                    "reuse_supported": False,
                    "explanation": "Independent byte-preserving iteration from the frozen snapshot. Review a new plan; cross-run computation reuse is not supported."}
    except (OSError, ValueError) as error:
        if isinstance(error, WorkflowError):
            raise
        raise WorkflowError("iteration_dependency_graph_invalid", logical_files=tuple(sorted(path.as_posix() for path in logical.values())),
                            private_detail=str(error)) from error
    finally:
        if not committed and published.is_dir() and published.parent == imports:
            # Only this invocation's newly created copy; never original evidence.
            shutil.rmtree(published)
