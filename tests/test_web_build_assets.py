"""Real setuptools build behavior; no scientific calculations or downloads."""
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
import setuptools
from setuptools import Distribution


def test_rebuilding_removes_obsolete_generated_chunks_and_modules_only(tmp_path,monkeypatch):
    # Run the actual build class in an independent minimal build checkout.
    script=tmp_path/'setup.py'
    script.write_bytes((Path(__file__).parents[1]/'setup.py').read_bytes())
    (tmp_path/'configs').mkdir()
    for name in ('m1_feature_definitions.yaml','m1_rules_v3.yaml'):
        (tmp_path/'configs'/name).write_text('software_build_fixture: true\n')
    source=tmp_path/'src/igem_drylab';source.mkdir(parents=True)
    (source/'__init__.py').write_text('')
    frontend=tmp_path/'dist';frontend.mkdir()
    (frontend/'index.html').write_text('current index')
    (frontend/'current.js').write_text('current chunk')
    build=tmp_path/'build/lib/igem_drylab';build.mkdir(parents=True)
    (build/'removed_module.py').write_text('obsolete')
    (build/'software/web_static').mkdir(parents=True)
    (build/'software/web_static/old.js').write_text('obsolete chunk')
    original=source/'retained.py';original.write_text('SOURCE_MUST_REMAIN=True\n')
    monkeypatch.setattr(setuptools,'setup',lambda **kwargs:None)
    monkeypatch.setenv('FUSIONLAB_WEB_DIST',str(frontend))
    spec=spec_from_file_location('actual_release_builder',script)
    module=module_from_spec(spec);spec.loader.exec_module(module)
    distribution=Distribution({'packages':['igem_drylab'],'package_dir':{'igem_drylab':str(source)}})
    distribution.script_name=str(script)
    monkeypatch.chdir(tmp_path)
    command=module.BuildWithScientificRules(distribution)
    command.ensure_finalized();command.build_lib=str(tmp_path/'build/lib')
    command.run()
    assert not (build/'removed_module.py').exists()
    assert {path.name for path in (build/'software/web_static').iterdir()}=={'index.html','current.js'}
    assert original.read_text()=='SOURCE_MUST_REMAIN=True\n'
    assert (build/'retained.py').read_bytes()==original.read_bytes()
