"""Software packaging contracts; no biological or numerical reproduction."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace


def packaging_module():
    spec = spec_from_file_location('windows_packager', Path(__file__).parents[1] / 'scripts/package_windows_desktop.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_runtime_closure_handles_extras_and_excludes_development(tmp_path, monkeypatch):
    module = packaging_module()
    project = {'dependencies': ['core[api]>=1'], 'optional-dependencies': {'software': ['web']}}
    def dist(name, requires=()):
        return SimpleNamespace(metadata={'Name': name}, version='1.0', requires=requires)
    installed = [dist('core', ['nested', 'optional; extra == "api"', 'dev; extra == "test"']),
                 dist('web', ['nested']), dist('nested'), dist('optional'), dist('dev'), dist('pytest')]
    monkeypatch.setattr(module.importlib.metadata, 'distributions', lambda **kwargs: installed)
    assert set(module.runtime_distributions(project, tmp_path)) == {'core', 'web', 'nested', 'optional'}


def test_runtime_copy_retains_native_data_testing_api_and_licenses(tmp_path, monkeypatch):
    module = packaging_module()
    source = tmp_path / 'site'
    included = ['numpy/__init__.py', 'numpy/testing/__init__.py', 'numpy/data/table.txt',
                'numpy.libs/blas.dll', 'numpy-1.dist-info/licenses/LICENSE.txt']
    excluded = ['numpy/tests/data.txt', 'numpy/__pycache__/cached.pyc', 'numpy-1.dist-info/direct_url.json']
    for name in included + excluded:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('software fixture', encoding='utf-8')
    dist = SimpleNamespace(metadata={'Name': 'numpy'}, version='1.0', files=included+excluded,
                           locate_file=lambda name: source/name)
    monkeypatch.setattr(module, 'runtime_distributions', lambda *args: {'numpy': dist})
    output = tmp_path/'runtime'
    assert module.copy_runtime_dependencies(tmp_path/'unused', source, output) == {'numpy': '1.0'}
    assert sorted(p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()) == sorted(included)
