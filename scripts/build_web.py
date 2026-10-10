"""Build a pure-Python Web/CLI wheel with the existing production frontend."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from importlib.metadata import version


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    config=json.loads((repo/'requirements/release-toolchain.json').read_text())
    if sys.platform=='linux':
        runtime=json.loads((repo/'requirements/web-toolchain.json').read_text())
    elif sys.platform=='win32': runtime=config
    else: raise SystemExit('Supported Web builders: Windows x64 or Linux x86_64.')
    if '.'.join(map(str,sys.version_info[:3]))!=runtime['python']:
        raise SystemExit('Use the supported Python build runtime: '+runtime['python'])
    from packaging.requirements import Requirement
    for line in (repo/config['build_lock']).read_text().splitlines():
        if not line.strip() or line.startswith('#'): continue
        requirement=Requirement(line)
        if not requirement.specifier.contains(version(requirement.name)):
            raise SystemExit('Install the pinned Python build lock before building: '+requirement.name)
    if args.output.exists(): raise SystemExit('Choose a new output directory. Old builds are preserved.')
    pnpm=shutil.which('pnpm.cmd' if os.name=='nt' else 'pnpm')
    if not pnpm: raise SystemExit('Build prerequisite missing: pnpm '+config['pnpm']+'. End users do not need Node/pnpm/Rust.')
    def run(*cmd,**kwargs): return subprocess.run(cmd,check=True,cwd=repo,**kwargs)
    for cmd,expected in [(('node','--version'),'v'+config['node']),((pnpm,'--version'),config['pnpm'])]:
        if run(*cmd,capture_output=True,text=True).stdout.strip()!=expected: raise SystemExit('Web build tool version mismatch.')
    run(pnpm,'--dir','software/dashboard','install','--frozen-lockfile')
    run(pnpm,'--dir','software/dashboard','build')
    args.output.mkdir(parents=True)
    run(sys.executable,'-B','-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(args.output.resolve()),str(repo),
        env={**os.environ,'FUSIONLAB_WEB_DIST':str(repo/'software/dashboard/dist'),'PYTHONDONTWRITEBYTECODE':'1'})
    print('Web/CLI wheel built. Install the platform-specific runtime lock, then this wheel with --no-deps; run fusionlab serve --open.')


if __name__=='__main__': main()
