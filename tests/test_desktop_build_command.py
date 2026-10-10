"""Real Windows command preflight/error behavior; never build or calculate here."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows desktop entry')
REPO = Path(__file__).parents[1]
SCRIPT = REPO/'build-desktop.ps1'


def invoke(*args):
    return subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass',
        '-File',str(SCRIPT),*map(str,args)],capture_output=True,text=True,timeout=60)


def test_windows_51_parses_entry_and_reported_prerequisites_are_real():
    # Legacy Windows PowerShell argument quoting differs from PowerShell 7;
    # invoke the actual 5.1 entry, not only a script-string assertion.
    if sys.version_info[:3] != (3,13,13) or not all(shutil.which(x) for x in ['node','rustup','git']):
        pytest.skip('Requires the supported desktop toolchain for real preflight.')
    if subprocess.check_output(['node','--version'],text=True).strip() != 'v24.19.0':
        pytest.skip('Node toolchain is not the supported release version.')
    before = {p.name for p in (REPO/'build').iterdir()} if (REPO/'build').exists() else set()
    result = invoke('-Check','-Python',sys.executable)
    assert result.returncode == 0, result.stdout+result.stderr
    assert 'Prerequisites found' in result.stdout
    assert 'No dependencies were installed' in result.stdout
    after = {p.name for p in (REPO/'build').iterdir()} if (REPO/'build').exists() else set()
    assert before == after


def test_missing_selected_python_fails_before_install_or_packaging(tmp_path):
    output = tmp_path/'should-not-be-built'
    result = invoke('-Python',tmp_path/'missing-python.exe','-Output',output)
    assert result.returncode != 0
    assert not output.exists() and not output.with_suffix('.zip').exists()


def test_dirty_checkout_is_not_deleted_or_built(tmp_path):
    if sys.version_info[:3] != (3,13,13) or not all(shutil.which(x) for x in ['node','rustup','git']):
        pytest.skip('Requires supported preflight tools to reach the dirty-check gate.')
    if subprocess.check_output(['node','--version'],text=True).strip() != 'v24.19.0':
        pytest.skip('Node toolchain is not the supported release version.')
    # Copy only the command/config into a new Git fixture; preserve user sources.
    shutil.copy2(SCRIPT,tmp_path/'build-desktop.ps1')
    (tmp_path/'requirements').mkdir()
    shutil.copy2(REPO/'requirements/release-toolchain.json',tmp_path/'requirements/release-toolchain.json')
    subprocess.run(['git','init',str(tmp_path)],check=True,capture_output=True)
    output=tmp_path/'build/releases/FusionLab'
    result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(tmp_path/'build-desktop.ps1'),'-Python',sys.executable],capture_output=True,text=True,timeout=60)
    assert result.returncode != 0
    assert 'clean Git checkout' in result.stderr
    assert (tmp_path/'build-desktop.ps1').read_bytes() == SCRIPT.read_bytes()
    assert not output.exists() and not (tmp_path/'.venv').exists()
