"""Bundle canonical rule assets without maintaining duplicate source files."""
from pathlib import Path
from shutil import copyfile
from shutil import copytree, rmtree
import os

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithScientificRules(build_py):
    def run(self):
        root = Path(__file__).resolve().parent
        # Setuptools reuses build/lib. A removed Python module or old hashed
        # frontend chunk must not survive into a subsequent release wheel.
        built_package = Path(self.build_lib).resolve() / 'igem_drylab'
        if built_package.exists():
            if (not built_package.resolve().is_relative_to(root / 'build')
                    or built_package.is_symlink()):
                raise ValueError('choose_an_empty_external_build_directory')
            rmtree(built_package)
        super().run()
        destination = Path(self.build_lib) / "igem_drylab" / "assets"
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("m1_feature_definitions.yaml", "m1_rules_v3.yaml"):
            copyfile(root / "configs" / name, destination / name)
        # Only the Web release builder opts in. No extra frontend source copy
        # or Node dependency is needed in the installed Python runtime.
        frontend=os.environ.get('FUSIONLAB_WEB_DIST')
        if frontend:
            source=Path(frontend).resolve()
            if not (source/'index.html').is_file(): raise ValueError('built_web_frontend_missing')
            copytree(source,Path(self.build_lib)/'igem_drylab/software/web_static')


setup(cmdclass={"build_py": BuildWithScientificRules})
