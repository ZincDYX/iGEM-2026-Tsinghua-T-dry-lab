"""Bundle canonical rule assets without maintaining duplicate source files."""
from pathlib import Path
from shutil import copyfile

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


setup(cmdclass={"build_py": BuildWithScientificRules})
