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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--source-tar',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--python-archive',type=Path,required=True)
    parser.add_argument('--python-archive-sha256',required=True)
    parser.add_argument('--site-packages',type=Path,required=True)
    parser.add_argument('--stdlib',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
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
    shutil.copytree(args.site_packages,python/'Lib/site-packages',ignore=shutil.ignore_patterns(
        '__pycache__','__editable__*','direct_url.json','*.pyc','*.pyo'))
    for module in ('venv','ensurepip'):
        shutil.copytree(args.stdlib/module,python/'Lib'/module,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    pth = next(python.glob('python*._pth'))
    stdlib_zip = next(python.glob('python3*.zip')).name
    pth.write_text('\n'.join([stdlib_zip,'.','Lib','Lib/site-packages','Lib/site-packages/win32',
        'Lib/site-packages/win32/lib','Lib/site-packages/Pythonwin','../resources/src','import site','']),encoding='utf-8')
    checked = subprocess.run([str(python/'python.exe'),'-c',
        'import json,sqlite3,importlib.metadata; import fastapi,uvicorn,numpy,scipy,mcp,igem_drylab.software.desktop_backend; print(json.dumps({d.metadata["Name"]:d.version for d in importlib.metadata.distributions()}))'],
        cwd=root,capture_output=True,text=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
    (root/'runtime-import-check.log').write_text(checked.stdout+'\n'+checked.stderr,encoding='utf-8')
    if checked.returncode: raise RuntimeError('runtime import check failed; see '+str(root/'runtime-import-check.log'))
    (root/'runtime-dependencies.json').write_text(checked.stdout,encoding='utf-8')
    (root/'使用说明.txt').write_text(
        'FusionLab Windows x64 便携版\n\n解压完整目录后双击 FusionLab.exe；不要单独移动 exe。\n'
        '默认使用随包 Python 后台、本机 SQLite，前端资源内置；不默认连接任何服务器。\n'
        '在“设置”选择可选 SSH 远程模式，填写用户自行配置的 SSH 别名和后台端口，保存后重新启动。\n'
        '远程模式需要系统 OpenSSH、已信任的 known_hosts、认证配置和已启动的远程后台。\n'
        '本地用户数据与连接设置在 Windows 用户应用数据目录，不在程序源码中。\n'
        '关闭窗口结束本地后台/插件子进程或本窗口 SSH 隧道；不关闭远程后台。\n'
        '需要 Microsoft WebView2 Runtime。该便携版未做商业代码签名。\n'
        '许可预测器、GPU 模型权重、作者私有数据不随包提供；相关作业缺工具或数据时必须明确阻断。\n'
        '默认本地可启动不代表全部外部工具已安装或真实项目已实验验证。\n',encoding='utf-8')
    files = [p for p in sorted(root.rglob('*')) if p.is_file()]
    records = [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256(p.read_bytes()).hexdigest()} for p in files]
    manifest = dict(commit=args.commit,platform='windows-x86_64',default_mode='local',bundled_frontend=True,
        python_archive_sha256=args.python_archive_sha256,source_archive_sha256=sha256(args.source_tar.read_bytes()).hexdigest(),
        scope='portable_software_package_not_scientific_validation',files=records,total_bytes=sum(p['bytes'] for p in records))
    (root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(root.with_suffix('.zip'),'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob('*')):
            if path.is_file(): archive.write(path,root.name+'/'+path.relative_to(root).as_posix())
    print(json.dumps(dict(commit=args.commit,exe_sha256=sha256((root/'FusionLab.exe').read_bytes()).hexdigest(),
        unpacked_bytes=manifest['total_bytes'],zip_bytes=root.with_suffix('.zip').stat().st_size,
        zip_sha256=sha256(root.with_suffix('.zip').read_bytes()).hexdigest()),indent=2))


if __name__ == '__main__': main()
