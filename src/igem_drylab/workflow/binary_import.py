"""Bounded byte-preserving scientific ZIP import; no extraction of active content."""
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import tempfile
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

from .models import WorkflowError

MAX_BYTES = 128_000_000
MAX_FILES = 2048


def validate_archive_members(infos):
    """One byte/name policy shared by importers, including read-only previews."""
    if len(infos) > MAX_FILES or sum(i.file_size for i in infos) > MAX_BYTES:
        raise WorkflowError('scientific_upload_budget_exceeded', status_code=413)
    names = set()
    for item in infos:
        name = item.orig_filename
        mode = item.external_attr >> 16
        parts = PurePosixPath(name).parts
        if (not name or '\\' in name or PurePosixPath(name).is_absolute()
            or PureWindowsPath(name).drive
            or any(p in {'..', '.', ''} for p in name.rstrip('/').split('/'))
            or stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}
            or item.flag_bits & 1):
            raise WorkflowError('invalid_upload_identity')
        if any(':' in p or '\x00' in p or p.endswith(('.', ' '))
               or p.split('.', 1)[0].casefold() in {'con', 'prn', 'aux', 'nul',
                   *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
               for p in parts):
            raise WorkflowError('invalid_upload_identity')
        folded = name.rstrip('/').casefold()
        if folded in names:
            raise WorkflowError('invalid_upload_identity')
        names.add(folded)


async def receive_bundle(request, imports: Path, config_filename: str, publish):
    imports.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(imports).free < MAX_BYTES * 3:
        raise WorkflowError("scientific_upload_disk_budget_exceeded", status_code=413)
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > MAX_BYTES):
        raise WorkflowError("scientific_upload_budget_exceeded", status_code=413)
    with tempfile.TemporaryDirectory(prefix="binary-staging-", dir=imports) as staging:
        archive = Path(staging) / "bundle.zip"
        received = 0
        with archive.open("wb") as output:
            async for block in request.stream():
                received += len(block)
                if received > MAX_BYTES:
                    raise WorkflowError("scientific_upload_budget_exceeded", status_code=413)
                output.write(block)
        root = Path(staging) / "tree"
        root.mkdir()
        hashes = {}
        try:
            with ZipFile(archive) as bundle:
                infos = bundle.infolist()
                validate_archive_members(infos)
                total = 0
                for item in infos:
                    # ZipInfo normalizes platform separators on Windows;
                    # authorize the original central-directory name, not its repair.
                    name = item.orig_filename
                    parts = PurePosixPath(name).parts
                    if item.is_dir():
                        continue
                    target = root.joinpath(*parts)
                    if not target.resolve().is_relative_to(root):
                        raise WorkflowError("invalid_upload_identity")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    digest = sha256()
                    with bundle.open(item) as source, target.open("xb") as output:
                        while block := source.read(65536):
                            total += len(block)
                            if total > MAX_BYTES:
                                raise WorkflowError("scientific_upload_budget_exceeded", status_code=413)
                            digest.update(block)
                            output.write(block)
                    hashes[name] = digest.hexdigest()
                    if sha256(target.read_bytes()).hexdigest() != hashes[name]:
                        raise WorkflowError("file_identity_changed")
        except (BadZipFile, OSError) as exc:
            raise WorkflowError("invalid_scientific_archive") from exc
        if config_filename not in hashes:
            raise WorkflowError("missing_uploaded_scientific_config")
        # Validate before moving and publish only a completely valid bundle.
        from .scientific_project import load_scientific_project
        from igem_drylab.resources import default_config_path
        rules = (default_config_path("m1_feature_definitions.yaml"), default_config_path("m1_rules_v3.yaml"))
        import yaml
        raw = yaml.safe_load((root / config_filename).read_bytes())
        if not isinstance(raw, dict) or raw.get("tools"):
            raise WorkflowError("runtime_settings_not_scientific_input")
        load_scientific_project(root / config_filename, allowed_roots=(root, *rules))
        final = imports / str(uuid4())
        root.rename(final)
        try:
            return publish(final, config_filename, hashes)
        except BaseException:
            if final.exists():
                shutil.rmtree(final)  # Only this newly owned, exact directory.
            raise
