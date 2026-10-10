"""Install the supported backend from exact locks, without external predictors."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import struct


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel-dir',type=Path,help='Retain the built project wheel here')
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    config=json.loads((repo/'requirements/release-toolchain.json').read_text())
    if sys.platform!='win32' or struct.calcsize('P')!=8 or '.'.join(map(str,sys.version_info[:3]))!=config['python']:
        raise SystemExit('This release lock supports Windows x64 / Python '+config['python']+'. Compatibility test environments are separate.')
    if sys.prefix==sys.base_prefix:
        raise SystemExit('Create and activate a virtual environment before installing the release.')
    def run(*command):subprocess.run(command,cwd=repo,check=True)
    run(sys.executable,'-B','-m','pip','install','--no-cache-dir','--no-compile','-r',str(repo/'requirements.txt'))
    run(sys.executable,'-B',str(repo/'scripts/verify_release_lock.py'),'--installed')
    if args.wheel_dir:
        args.wheel_dir.mkdir(parents=True,exist_ok=True)
        run(sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(args.wheel_dir.resolve()),str(repo))
        wheels=list(args.wheel_dir.glob('igem_drylab_2026-*.whl'))
        if len(wheels)!=1:raise SystemExit('Use a wheel directory containing exactly one project version.')
        run(sys.executable,'-m','pip','install','--no-deps','--force-reinstall',str(wheels[0].resolve()))
    else:
        run(sys.executable,'-m','pip','install','--no-deps','--no-build-isolation',str(repo))
    run(sys.executable,'-m','pip','check')


if __name__=='__main__':main()
