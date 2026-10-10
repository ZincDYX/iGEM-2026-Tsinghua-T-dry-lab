"""Release dependency contract tests; no numerical calculations or installs."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from packaging.markers import default_environment

if sys.version_info < (3, 11):
    pytest.skip('The release checker uses the supported Python 3.13 toolchain.', allow_module_level=True)

spec = importlib.util.spec_from_file_location('release_lock', Path(__file__).parents[1]/'scripts/verify_release_lock.py')
lock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lock)


@pytest.mark.parametrize('line', ['core>=1', 'core==1.*', 'core[extra]==1', 'core @ https://invalid.example/w.whl'])
def test_lock_rejects_resolving_requirements(tmp_path, line):
    path = tmp_path/'lock'
    path.write_text(line)
    with pytest.raises(ValueError, match='exact versions'):
        lock.read_pins([path])


def test_lock_applies_platform_markers_and_detects_conflicting_pins(tmp_path):
    path = tmp_path/'lock'
    path.write_text('core==1\nwindows==2; sys_platform == "win32"\n')
    environment = {**default_environment(), 'sys_platform': 'linux'}
    assert lock.read_pins([path], environment) == {'core': '1'}
    assert lock.read_pins([path], {**environment, 'sys_platform': 'win32'}) == {'core': '1', 'windows': '2'}
    other = tmp_path/'other'
    other.write_text('core==2\n')
    with pytest.raises(ValueError, match='Conflicting pin'):
        lock.read_pins([path, other], environment)


def test_lock_checks_transitive_extra_and_declared_floor():
    installed = {'core': SimpleNamespace(version='1', requires=['nested>=2; extra == "api"']),
                 'nested': SimpleNamespace(version='2', requires=[])}
    pins = {'core': '1', 'nested': '2'}
    assert lock.verify(pins, ['core[api]>=1'], installed)['installed_closure_verified']
    with pytest.raises(ValueError, match='violates declared'):
        lock.verify({'core': '1', 'nested': '1'}, ['core[api]>=1'], installed)
    with pytest.raises(ValueError, match='Missing release pin'):
        lock.verify({'core': '1'}, ['core[api]>=1'], installed)
    with pytest.raises(ValueError, match='Installed version differs'):
        lock.verify(pins, ['core'], {'core': SimpleNamespace(version='9', requires=[])})


def test_current_release_pins_satisfy_project_and_build_requirements():
    import json
    import tomllib
    repo = Path(__file__).parents[1]
    config = json.loads((repo/'requirements/release-toolchain.json').read_text())
    project = tomllib.loads((repo/'pyproject.toml').read_text())
    environment = {**default_environment(), 'sys_platform': 'win32'}
    pins = lock.read_pins([repo/config['runtime_lock'], repo/config['build_lock']], environment)
    required = project['project']['dependencies'] + project['project']['optional-dependencies']['software'] + project['build-system']['requires']
    assert lock.verify(pins, required, environment=environment)['checked_pins'] == 55


def test_root_requirements_reuses_the_release_locks_without_duplicate_pins():
    import json
    repo = Path(__file__).parents[1]
    config = json.loads((repo/'requirements/release-toolchain.json').read_text())
    entries = [line.strip() for line in (repo/'requirements.txt').read_text().splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
    assert entries == ['-r '+config['runtime_lock'], '-r '+config['build_lock']]


def test_linux_web_lock_is_independent_and_covers_active_dependencies():
    import json
    import tomllib
    repo=Path(__file__).parents[1]
    config=json.loads((repo/'requirements/web-toolchain.json').read_text())
    project=tomllib.loads((repo/'pyproject.toml').read_text())
    environment={**default_environment(),'sys_platform':'linux','python_version':'3.12','python_full_version':'3.12.14'}
    pins=lock.read_pins([repo/config['runtime_lock'],repo/config['build_lock']],environment)
    required=project['project']['dependencies']+project['project']['optional-dependencies']['software']+project['build-system']['requires']
    assert lock.verify(pins,required,environment=environment)['checked_pins']>=49
    assert config['runtime_lock']!='requirements/runtime-py313-windows.lock'
