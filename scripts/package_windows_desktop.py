"""Package a Windows portable app; mechanical copying, not scientific reproduction."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile
import importlib.metadata

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def runtime_distributions(metadata, site_packages):
    """Resolve declared backend + software requirements, not the build venv."""
    installed = {canonicalize_name(d.metadata['Name']): d
                 for d in importlib.metadata.distributions(path=[str(site_packages)])}
    pending = [(Requirement(r), '') for r in
               metadata['dependencies'] + metadata['optional-dependencies']['software']]
    selected = {}
    expanded = set()
    while pending:
        requirement, parent_extra = pending.pop()
        if requirement.marker and not requirement.marker.evaluate({'extra': parent_extra}):
            continue
        name = canonicalize_name(requirement.name)
        dist = installed[name]
        if not requirement.specifier.contains(dist.version, prereleases=True):
            raise ValueError('runtime_dependency_version_mismatch:' + name)
        selected[name] = dist
        for extra in {''} | set(requirement.extras):
            if (name, extra) in expanded:
                continue
            expanded.add((name, extra))
            pending.extend((Requirement(r), extra) for r in dist.requires or [])
    return selected


def copy_runtime_dependencies(metadata, site_packages, destination):
    """Wheel RECORD owns modules, native DLLs, data, metadata and licenses."""
    selected = runtime_distributions(metadata, site_packages)
    source_root = site_packages.resolve()
    files = set()
    for dist in selected.values():
        if dist.files is None:
            raise ValueError('missing_runtime_wheel_record:' + dist.metadata['Name'])
        for entry in dist.files:
            source = Path(dist.locate_file(entry)).resolve()
            # Wheel entry-point Scripts live outside site-packages; runtime
            # invokes Python modules, not development venv launchers.
            if not source.is_relative_to(source_root):
                continue
            relative = source.relative_to(source_root)
            if '__pycache__' in relative.parts or source.suffix in {'.pyc', '.pyo'} or source.name == 'direct_url.json':
                continue
            # Only upstream NumPy/SciPy test suites. Retain numpy.testing,
            # runtime data, all native libraries and distribution licenses.
            if relative.parts[0] in {'numpy', 'scipy'} and 'tests' in relative.parts[1:-1]:
                continue
            files.add(relative)
    for relative in sorted(files):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / relative, target)
    return {name: dist.version for name, dist in sorted(selected.items())}


def main():
    import tomllib  # Windows release builder uses CPython 3.13.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--source-tar',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--python-archive',type=Path,required=True)
    parser.add_argument('--python-archive-sha256',required=True)
    parser.add_argument('--site-packages',type=Path,required=True)
    parser.add_argument('--stdlib',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--release-inventory',type=Path,
                        help='Optional directory with dated CycloneDX component inventory and OSV report')
    args = parser.parse_args()
    for path in (args.exe,args.source_tar,args.python_archive):
        if not path.is_file(): raise FileNotFoundError(path)
    if not args.site_packages.is_dir(): raise FileNotFoundError(args.site_packages)
    if args.output.exists() or args.output.with_suffix('.zip').exists():
        raise ValueError('preserve_previous_package_select_new_output')
    if sha256(args.python_archive.read_bytes()).hexdigest() != args.python_archive_sha256.lower():
        raise ValueError('python_archive_identity_mismatch')
    root = args.output.resolve(); root.mkdir(parents=True)
    shutil.copy2(args.exe,root/'FusionLab.exe')
    resources = root/'resources'; resources.mkdir()
    with tarfile.open(args.source_tar) as archive:
        for member in archive.getmembers():
            # Runtime allowlist. Full source/tests/operations stay in the bundle.
            if not (member.name.startswith("src/") or member.name in {"configs/m1_feature_definitions.yaml", "configs/m1_rules_v3.yaml", "LICENSE", "pyproject.toml", "software/dashboard/THIRD_PARTY_NOTICES.txt"}):
                continue
            target = (resources/member.name).resolve()
            if not target.is_relative_to(resources) or not member.isfile():
                raise ValueError('unsafe_or_nonfile_source_member')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    python = root/'python'; python.mkdir()
    with zipfile.ZipFile(args.python_archive) as archive:
        for member in archive.infolist():
            if not (python/member.filename).resolve().is_relative_to(python):
                raise ValueError('unsafe_python_archive')
        archive.extractall(python)
    # Wheel-native dependencies already installed in the matching CPython ABI.
    # Do not ship editable source pointers, caches or workstation paths.
    project_metadata = tomllib.loads((resources/'pyproject.toml').read_text(encoding='utf-8'))['project']
    selected_dependencies = copy_runtime_dependencies(project_metadata, args.site_packages, python/'Lib/site-packages')
    for module in ('venv','ensurepip'):
        shutil.copytree(args.stdlib/module,python/'Lib'/module,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    pth = next(python.glob('python*._pth'))
    stdlib_zip = next(python.glob('python3*.zip')).name
    pth.write_text('\n'.join([stdlib_zip,'.','Lib','Lib/site-packages','Lib/site-packages/win32',
        'Lib/site-packages/win32/lib','Lib/site-packages/Pythonwin','../resources/src','import site','']),encoding='utf-8')
    checked = subprocess.run([str(python/'python.exe'),'-c',
        'import json,sqlite3,importlib.metadata; import fastapi,uvicorn,numpy,scipy,mcp,PIL.Image,ihm.format_bcif,msgpack,igem_drylab.software.desktop_backend; print(json.dumps({d.metadata["Name"]:d.version for d in importlib.metadata.distributions()}))'],
        cwd=root,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
    (root/'runtime-import-check.log').write_text(checked.stdout+'\n'+checked.stderr,encoding='utf-8')
    if checked.returncode: raise RuntimeError('runtime import check failed; see '+str(root/'runtime-import-check.log'))
    (root/'runtime-dependencies.json').write_text(checked.stdout,encoding='utf-8')
    plugin_check = subprocess.run([str(python/'python.exe'), '-B', '-c', '''
import importlib.util,json,subprocess,tempfile,venv
from pathlib import Path
from igem_drylab.workflow.plugins import configure_embedded_environment
with tempfile.TemporaryDirectory(prefix="fusionlab-plugin-runtime-") as owned:
    environment=Path(owned)/"environment"
    venv.EnvBuilder(with_pip=False).create(environment)
    configure_embedded_environment(environment)
    child=environment/"Scripts/python.exe"
    output=subprocess.check_output([str(child),"-I","-c","import json,sys,importlib.util; print(json.dumps(dict(prefix=sys.prefix,parent_numpy=importlib.util.find_spec('numpy') is not None,parent_app=importlib.util.find_spec('igem_drylab') is not None)))"],text=True)
    result=json.loads(output)
    assert Path(result["prefix"]).resolve()==environment.resolve()
    assert not result["parent_numpy"] and not result["parent_app"]
    subprocess.run([str(child),"-I","-m","ensurepip","--version"],check=True)
    print(json.dumps(dict(isolated_plugin_paths_verified=True,scientific_calculation=False)))
'''], cwd=root, capture_output=True, text=True, env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    (root/'plugin-runtime-check.log').write_text(plugin_check.stdout+'\n'+plugin_check.stderr,encoding='utf-8')
    if plugin_check.returncode: raise RuntimeError('plugin runtime check failed; see '+str(root/'plugin-runtime-check.log'))
    if args.release_inventory:
        inventory = args.release_inventory.resolve()
        for name in ('SBOM.cdx.json', 'OSV-audit.json'):
            source = inventory/name
            if not source.is_file(): raise FileNotFoundError(source)
            report = json.loads(source.read_text(encoding='utf-8'))
            commit = report['metadata']['component']['version'] if name == 'SBOM.cdx.json' else report['commit']
            if commit != args.commit: raise ValueError('release_inventory_commit_mismatch')
            shutil.copy2(source,root/name)
    (root/'使用说明.txt').write_text(
        'FusionLab Windows x64 便携版\n\n解压完整目录后双击 FusionLab.exe；不要单独移动 exe。\n'
        '默认使用随包 Python 后台、本机 SQLite，前端资源内置；不默认连接任何服务器。\n'
        '可选远程模式：Settings 中填写兼容 FusionLab 的 HTTPS API 基地址及访问令牌，保存后重启。\n'
        '本地用户数据与连接设置在 Windows 用户应用数据目录，不在程序源码中。\n'
        '关闭窗口结束本地后台/插件子进程；不管理或关闭任何远程后台。\n'
        '需要 Microsoft WebView2 Runtime。该便携版未做商业代码签名。\n'
        '许可预测器、GPU 模型权重、作者私有数据不随包提供；相关作业缺工具或数据时必须明确阻断。\n'
        '令牌由 Windows 用户级 DPAPI 加密保存，不返回前端；HTTPS 校验证书和主机名，不尝试匿名连接。\n'
        '私有 CA 可在连接设置中指定 PEM 文件；留空使用系统信任。远程模式不迁移本机项目。\n'
        '默认本地可启动不代表全部外部工具已安装或真实项目已实验验证。\n',encoding='utf-8')
    files = [p for p in sorted(root.rglob('*')) if p.is_file()]
    records = [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()} for p in files]
    manifest = dict(commit=args.commit,platform='windows-x86_64',default_mode='local',bundled_frontend=True,
        runtime_dependency_selection='pyproject backend + software extra, transitive wheel RECORD closure',
        selected_runtime_distributions=selected_dependencies,
        omitted_runtime_content=['unselected development distributions', 'numpy/scipy upstream tests', 'bytecode/editable workstation pointers'],
        python_archive_sha256=args.python_archive_sha256,source_archive_sha256=sha256(args.source_tar.read_bytes()).hexdigest(),
        viewer_dependencies={'plotly.js-strict-dist-min':'4.1.2','molstar':'5.13.0','fflate':'0.8.3'},
        viewer_dependency_scope='direct_viewer_manifest_not_complete_SBOM',
        release_inventory_scope='dated_component_inventory_not_binary_reachability_or_license_compliance' if args.release_inventory else 'not_provided',
        scope='portable_software_package_not_scientific_validation',runtime_allowlist=['src/','configs/m1_feature_definitions.yaml','configs/m1_rules_v3.yaml','LICENSE','pyproject.toml','software/dashboard/THIRD_PARTY_NOTICES.txt'], files=records,total_bytes=sum(p['bytes'] for p in records))
    (root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(root.with_suffix('.zip'),'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob('*')):
            if path.is_file(): archive.write(path,root.name+'/'+path.relative_to(root).as_posix())
    print(json.dumps(dict(commit=args.commit,exe_sha256=sha256((root/'FusionLab.exe').read_bytes()).hexdigest(),
        unpacked_bytes=manifest['total_bytes'],zip_bytes=root.with_suffix('.zip').stat().st_size,
        zip_sha256=sha256(root.with_suffix('.zip').read_bytes()).hexdigest()),indent=2))


if __name__ == '__main__': main()
