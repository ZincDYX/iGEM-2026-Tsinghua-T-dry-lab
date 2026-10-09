from hashlib import sha256
from io import BytesIO
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from igem_drylab.workflow.builtins import builtin_tools
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import NodeContext


def manager(tmp_path):
    return PluginManager(tmp_path / "plugins", WorkflowStore(tmp_path / "ledger.sqlite"), builtin_tools())


def test_two_plugins_really_use_incompatible_dependency_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    plugins = manager(tmp_path)
    prefixes = []
    for version in ("1.0", "2.0"):
        source = tmp_path / f"plugin-{version}"
        source.mkdir()
        wheel = source / f"shared_dependency-{version}-py3-none-any.whl"
        with ZipFile(wheel, "w") as archive:
            archive.writestr("shared_dependency/__init__.py", f"VERSION = '{version}'\n")
            archive.writestr(f"shared_dependency-{version}.dist-info/METADATA", f"Metadata-Version: 2.1\nName: shared-dependency\nVersion: {version}\n")
            archive.writestr(f"shared_dependency-{version}.dist-info/WHEEL", "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
            archive.writestr(f"shared_dependency-{version}.dist-info/RECORD", "")
        (source / "requirements.lock").write_text(f"shared-dependency @ {wheel.as_uri()} --hash=sha256:{sha256(wheel.read_bytes()).hexdigest()}\n", encoding="utf-8")
        (source / "plugin.json").write_text(json.dumps({"id": "dependency_test", "name": "dependency test", "description": "test", "version": version, "capability": "test", "license": "MIT", "entrypoint": "entry.py", "requirements_lock": "requirements.lock", "input_schema": {"type": "object"}, "output_schema": {"type": "object", "required": ["version"]}}))
        (source / "entry.py").write_text("import argparse,json\nfrom pathlib import Path\nimport shared_dependency\np=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--output'); args=p.parse_args()\nPath(args.output).write_text(json.dumps({'version':shared_dependency.VERSION}))\n")
        record = plugins.install(source, trusted=True)
        tool = plugins.tools.get(f"plugin.dependency_test.{record['hash'][:12]}")
        context = NodeContext("test", version, tmp_path / f"work-{version}")
        context.work_dir.mkdir()
        result = tool.handler(tool.input_model.model_validate({}), context)
        assert result["version"] == version
        # Private independent oracle, not a path published by the plugin.
        prefixes.append(subprocess.check_output([record['python'], '-I', '-c', 'import sys; print(sys.prefix)'], text=True).strip())
        assert subprocess.check_output([record['python'], '-I', '-c',
            'import importlib.util; print(importlib.util.find_spec("igem_drylab") is None)'], text=True).strip() == 'True'
    assert prefixes[0] != prefixes[1]


def test_github_fetch_rejects_unpinned_revision_without_network(tmp_path):
    with pytest.raises(ValueError, match="40_character_commit"):
        manager(tmp_path).fetch_github("https://github.com/example/tool", "main")


def test_github_archive_is_checked_before_any_extraction(tmp_path, monkeypatch):
    content = BytesIO()
    with ZipFile(content, "w") as zipped:
        zipped.writestr("root/../../escape.py", "raise RuntimeError('must not execute')")
    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def raise_for_status(self): pass
        def iter_content(self, _): yield content.getvalue()
    monkeypatch.setattr("igem_drylab.workflow.plugins.requests.get", lambda *args, **kwargs: Response())
    with pytest.raises(ValueError, match="outside_root"):
        manager(tmp_path).fetch_github("https://github.com/example/tool", "a" * 40)
    assert not (tmp_path / "escape.py").exists()


def test_plugin_schema_is_the_manifest_schema(tmp_path):
    plugins = manager(tmp_path)
    record = plugins.install(Path("examples/plugins/sequence_composition"), trusted=True)
    metadata = next(item for item in plugins.tools.list() if item["plugin_hash"] == record["hash"])
    assert metadata["input_schema"]["required"] == ["sequence"]
    assert metadata["input_schema"]["additionalProperties"] is False


def test_install_rechecks_the_user_approved_source_hash(tmp_path):
    plugins = manager(tmp_path)
    source = tmp_path / "source"
    import shutil
    shutil.copytree("examples/plugins/sequence_composition", source)
    approved = plugins.inspect(source)["hash"]
    (source / "composition.py").write_text("raise RuntimeError('changed after inspection')")
    with pytest.raises(ValueError, match="changed_since_inspection"):
        plugins.install(source, trusted=True, expected_hash=approved)
    assert plugins.installed() == []
