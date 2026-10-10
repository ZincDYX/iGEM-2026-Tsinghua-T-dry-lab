"""Bundle canonical rule assets without maintaining duplicate source files."""
from pathlib import Path
from shutil import copyfile
from shutil import copytree
import os

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithScientificRules(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
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
            copytree(source,Path(self.build_lib)/'igem_drylab/software/web_static',dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithScientificRules})
