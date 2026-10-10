"""Full-history submission sizing, including removed artifacts; software only."""
import importlib.util
import json
from pathlib import Path
import subprocess


spec = importlib.util.spec_from_file_location('submission_size', Path(__file__).parents[1]/'scripts/check_submission_size.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_full_clone_records_removed_history_and_does_not_expose_workstation_path(tmp_path):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=tmp_path)
    git('init')
    git('config', 'user.email', 'fixture@example.invalid')
    git('config', 'user.name', 'Software fixture')
    git('remote', 'add', 'origin', 'https://gitlab.igem.org/2026/software/tsinghua-t/galatea.git')
    (tmp_path/'已移除的产物.bin').write_bytes(b'fixture'*150_000)
    git('add', '.')
    git('commit', '-m', 'Historical software artifact fixture')
    (tmp_path/'已移除的产物.bin').unlink()
    (tmp_path/'README.md').write_text('Small current tree.\n')
    git('add', '-A')
    git('commit', '-m', 'Current tree excludes artifact')
    result = checker.measure(tmp_path)
    assert result['tracked_source_bytes'] == 20
    assert not result['shallow'] and result['official_origin']
    assert len(result['large_reachable_blobs']) == 1
    assert result['large_reachable_blobs'][0]['bytes'] == 1_050_000
    assert result['official_gitlab_server_repository_size_bytes'] is None
    assert result['reachable_lfs_payload_bytes'] == 0
    assert str(tmp_path) not in json.dumps(result)
