"""Check current release pins against declared and installed dependency closure."""
import argparse
from importlib.metadata import distributions
import json
from pathlib import Path
import sys
import tomllib

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def read_pins(paths, environment=None):
    environment=environment or default_environment()
    pins={}
    for path in paths:
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):continue
            requirement=Requirement(line)
            if requirement.marker and not requirement.marker.evaluate(environment):continue
            specifiers=list(requirement.specifier)
            if requirement.url or requirement.extras or len(specifiers)!=1 or specifiers[0].operator!='==' or '*' in specifiers[0].version:
                raise ValueError('Release dependencies must be exact versions: '+requirement.name)
            name=canonicalize_name(requirement.name)
            version=specifiers[0].version
            if name in pins and pins[name]!=version:raise ValueError('Conflicting pin: '+name)
            pins[name]=version
    return pins


def verify(pins, requirements, installed=None, environment=None):
    """Validate direct requirements, then all active installed wheel dependencies."""
    environment=environment or default_environment()
    pending=[(Requirement(value),'') for value in requirements]
    visited=set()
    while pending:
        requirement,extra=pending.pop()
        if requirement.marker and not requirement.marker.evaluate({**environment,'extra':extra}):continue
        name=canonicalize_name(requirement.name)
        if name not in pins:raise ValueError('Missing release pin: '+name)
        if not requirement.specifier.contains(pins[name],prereleases=True):
            raise ValueError('Release pin violates declared requirement: '+str(requirement))
        if installed is None:continue
        dist=installed.get(name)
        if dist is None or dist.version!=pins[name]:raise ValueError('Installed version differs from release pin: '+name)
        for child_extra in {''}|set(requirement.extras):
            if (name,child_extra) in visited:continue
            visited.add((name,child_extra))
            pending.extend((Requirement(value),child_extra) for value in dist.requires or [])
    if installed is not None:
        for name,version in pins.items():
            if name not in installed or installed[name].version!=version:
                raise ValueError('Installed release dependency absent or different: '+name)
    return {'checked_pins':len(pins),'installed_closure_verified':installed is not None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installed',action='store_true')
    parser.add_argument('--runtime-only',action='store_true')
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    config=json.loads((repo/'requirements/release-toolchain.json').read_text())
    project=tomllib.loads((repo/'pyproject.toml').read_text())
    locks=[repo/config['runtime_lock']]+([] if args.runtime_only else [repo/config['build_lock']])
    pins=read_pins(locks)
    requirements=project['project']['dependencies']+project['project']['optional-dependencies']['software']
    if not args.runtime_only:requirements+=project['build-system']['requires']
    installed={canonicalize_name(d.metadata['Name']):d for d in distributions()} if args.installed else None
    if args.installed and '.'.join(map(str,sys.version_info[:3]))!=config['python']:
        raise ValueError('Release Python differs from supported toolchain')
    print(json.dumps(verify(pins,requirements,installed)))


if __name__=='__main__':main()
