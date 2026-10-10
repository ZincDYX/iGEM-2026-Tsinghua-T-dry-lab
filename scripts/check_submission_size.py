"""Measure source, full Git storage and reachable history separately."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def measure(repo):
    repo = Path(repo).resolve()
    def git(*args, input=None):
        return subprocess.check_output(['git', *args], cwd=repo, input=input, text=True, encoding='utf-8')
    commit = git('rev-parse', 'HEAD').strip()
    common = Path(git('rev-parse', '--git-common-dir').strip())
    if not common.is_absolute():
        common = repo/common
    common = common.resolve()
    tracked = git('ls-tree', '-rl', '-z', 'HEAD').split('\0')
    tracked_bytes = sum(int(line.split('\t', 1)[0].split()[3]) for line in tracked
                        if line and line.split()[1] == 'blob')
    submodules = [{'path': line.split('\t', 1)[1], 'commit': line.split()[2]}
                  for line in tracked if line and line.split()[1] == 'commit']
    reachable = git('rev-list', '--objects', '--all')
    identities = '\n'.join(line.split(' ', 1)[0] for line in reachable.splitlines())+'\n'
    objects = git('cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)', input=identities)
    large = []
    small_blobs = []
    names = dict(line.split(' ', 1) for line in reachable.splitlines() if ' ' in line)
    for line in objects.splitlines():
        identity, kind, size = line.split()
        if kind == 'blob' and int(size) < 1024:
            small_blobs.append(identity)
        if kind == 'blob' and int(size) >= 1_000_000:
            large.append({'object': identity, 'path': names.get(identity), 'bytes': int(size)})
    shallow = git('rev-parse', '--is-shallow-repository').strip() == 'true'
    storage_bytes = sum(p.stat().st_size for p in common.rglob('*') if p.is_file() and not p.is_symlink())
    # Cached LFS files can belong to unrelated local refs. Count reachable
    # pointer payloads separately, never hide them behind the small pointer.
    payload = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=repo,
        input=('\n'.join(small_blobs)+'\n').encode()) if small_blobs else b''
    offset = 0
    lfs = {}
    for identity in small_blobs:
        end = payload.index(b'\n', offset)
        header = payload[offset:end].split()
        size = int(header[2])
        content = payload[end+1:end+1+size]
        offset = end+size+2
        if content.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            oid = re.search(rb'^oid sha256:([0-9a-f]{64})$', content, re.M)
            length = re.search(rb'^size ([0-9]+)$', content, re.M)
            if oid and length:
                lfs[oid.group(1).decode()] = int(length.group(1))
    excluded = {}
    for name in ('lfs', 'modules', 'worktrees'):
        excluded[name] = sum(p.stat().st_size for p in (common/name).rglob('*')
                             if p.is_file() and not p.is_symlink())
    core_storage_bytes = storage_bytes - sum(excluded.values())
    upper_bound_bytes = core_storage_bytes + sum(lfs.values()) + tracked_bytes
    remote = git('config', '--get', 'remote.origin.url').strip()
    official = remote.removesuffix('.git').rstrip('/') == 'https://gitlab.igem.org/2026/software/tsinghua-t/galatea'
    return {'commit': commit, 'tracked_source_bytes': tracked_bytes,
            'full_common_git_storage_bytes': storage_bytes,
            'core_git_storage_bytes': core_storage_bytes,
            'local_cache_and_other_worktree_bytes': excluded,
            'reachable_lfs_payload_bytes': sum(lfs.values()),
            'reachable_lfs_payload_count': len(lfs),
            'conservative_source_plus_git_plus_reachable_lfs_bytes': upper_bound_bytes,
            'shallow': shallow, 'official_origin': official,
            'internal_limit_bytes': 50_000_000,
            'internal_size_check_passed': not shallow and upper_bound_bytes < 50_000_000,
            'official_gitlab_server_repository_size_bytes': None,
            'official_freeze_accepted': None,
            'large_reachable_blobs': sorted(large, key=lambda item: item['bytes'], reverse=True),
            'submodule_pins_not_downloaded_storage': submodules,
            'scope': 'Full history/all refs, source plus core Git storage plus reachable LFS payloads. Downloaded submodules, alternate worktree metadata and cached LFS are reported separately, not assumed to be remote submission content. GitLab backend accounting/freeze remain unverified. Decimal 50 MB is an internal conservative rule.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--report-only', action='store_true', help='Audit a non-submission development mirror without treating it as eligible')
    args = parser.parse_args()
    result = measure(args.repo)
    output = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output+'\n', encoding='utf-8')
    print(output)
    if not args.report_only and not result['internal_size_check_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
