"""Build the supported Windows release through the single existing packager."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New portable folder (and sibling ZIP)')
    parser.add_argument('--download-cache', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    config = json.loads((repo/'requirements/release-toolchain.json').read_text())
    def run(*command, cwd=repo, capture=False):
        return subprocess.run(command, cwd=cwd, check=True, text=True,
                              encoding='utf-8',
                              stdout=subprocess.PIPE if capture else None)
    if run('git', 'status', '--porcelain', capture=True).stdout.strip():
        raise SystemExit('Build from a clean committed checkout; do not discard local changes.')
    commit = run('git', 'rev-parse', 'HEAD', capture=True).stdout.strip()
    pnpm = shutil.which('pnpm.cmd') if sys.platform == 'win32' else shutil.which('pnpm')
    if not pnpm:
        raise SystemExit('Install pnpm '+config['pnpm']+' before building.')
    for command, expected in [(('node', '--version'), 'v'+config['node']),
                              ((pnpm, '--version'), config['pnpm'])]:
        if run(*command, capture=True).stdout.strip() != expected:
            raise SystemExit('Release toolchain version mismatch: '+command[0])
    if run('rustc', '--version', capture=True).stdout.split()[1] != config['rust']:
        raise SystemExit('Release Rust toolchain version mismatch.')
    run(sys.executable, '-B', str(repo/'scripts/install_locked.py'))
    dashboard = repo/'software/dashboard'
    run(pnpm, 'install', '--frozen-lockfile', cwd=dashboard)
    run(pnpm, 'build', cwd=dashboard)
    run('cargo', 'build', '--release', '--locked', '--features', 'custom-protocol',
        '--manifest-path', str(dashboard/'src-tauri/Cargo.toml'))
    target = Path(os.environ.get('CARGO_TARGET_DIR', dashboard/'src-tauri/target'))
    exe = target/'release/fusionlab-desktop.exe'
    cache = args.download_cache.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    embedded = cache/Path(config['python_embedded_url']).name
    if not embedded.exists():
        with urlopen(config['python_embedded_url'], timeout=120) as response, embedded.open('wb') as output:
            shutil.copyfileobj(response, output)
    if sha256(embedded.read_bytes()).hexdigest() != config['python_embedded_sha256']:
        raise SystemExit('CPython archive differs from the fixed official release; preserve and inspect the cache.')
    source = cache/('source-'+commit+'.tar')
    run('git', 'archive', '--format=tar', '--output', str(source), commit)
    run(sys.executable, '-B', str(repo/'scripts/package_windows_desktop.py'),
        '--exe', str(exe.resolve()), '--source-tar', str(source), '--commit', commit,
        '--python-archive', str(embedded), '--python-archive-sha256', config['python_embedded_sha256'],
        '--site-packages', sysconfig.get_path('purelib'), '--stdlib', sysconfig.get_path('stdlib'),
        '--output', str(args.output.resolve()))


if __name__ == '__main__':
    main()
