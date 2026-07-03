# -*- coding: utf-8 -*-
"""Build Custom HPBar Gameface .wotmod.

Source tree keeps Python as .py for GitHub.
Builder compiles python/**/*.py to Python 2.7 .pyc, copies only .pyc to the package,
and packs .wotmod as ZIP_STORED because WoT mod packages must be uncompressed.

Usage:
  python build.py
  python build.py --version 0.0.18
  python build.py --python C:/Python27/python.exe
  python build.py --no-docker
"""
from __future__ import print_function
import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def rm(path):
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(str(path))
    elif path.exists():
        path.unlink()


def copytree(src, dst, ignore=None):
    src = Path(src)
    dst = Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    ignored = set()
    if ignore:
        ignored = set(ignore(str(src), os.listdir(str(src))))
    for name in os.listdir(str(src)):
        if name in ignored or name == '.gitkeep':
            continue
        s = src / name
        d = dst / name
        if s.is_dir():
            copytree(s, d, ignore)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(s), str(d))


def copy_compiled_python(src, dst):
    src = Path(src)
    dst = Path(dst)
    for p in src.rglob('*.pyc'):
        rel = p.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(p), str(target))


def find_python_files():
    return sorted(Path('python').rglob('*.py'))


def clean_pyc():
    for p in Path('python').rglob('*.pyc'):
        p.unlink()
    for p in Path('python').rglob('__pycache__'):
        if p.is_dir():
            shutil.rmtree(str(p))


def compile_with_executable(pyexe):
    files = [str(p) for p in find_python_files()]
    if not files:
        return
    print('Compiling Python with: {}'.format(pyexe))
    subprocess.check_call([pyexe, '-m', 'py_compile'] + files)


def compile_with_docker(image='python:2.7'):
    files = [str(p).replace('\\', '/') for p in find_python_files()]
    if not files:
        return
    print('Python 2.7 executable not found. Trying Docker image: {}'.format(image))
    cmd = [
        'docker', 'run', '--rm',
        '-v', '{}:/work'.format(str(ROOT).replace('\\', '/')),
        '-w', '/work',
        image, 'python', '-m', 'py_compile'
    ] + files
    subprocess.check_call(cmd)


def compile_python(pyexe=None, allow_docker=True):
    clean_pyc()
    if pyexe:
        compile_with_executable(pyexe)
        return
    env_py = os.environ.get('PYTHON27')
    if env_py:
        compile_with_executable(env_py)
        return
    # Windows default from build.json is handled by caller; only use it if it exists.
    if sys.platform.startswith('win'):
        default = 'C:/Python27/python.exe'
        if Path(default).exists():
            compile_with_executable(default)
            return
    # Common Linux names, if user installed python2 manually.
    for candidate in ('python2.7', 'python2'):
        try:
            subprocess.check_call([candidate, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            compile_with_executable(candidate)
            return
        except Exception:
            pass
    if allow_docker:
        compile_with_docker()
        return
    raise RuntimeError('Python 2.7 not found. Set PYTHON27 or install Docker.')


def write_meta(temp, info):
    root = ET.Element('root')
    for key in ('id', 'version', 'name', 'description'):
        ET.SubElement(root, key).text = str(info.get(key, ''))
    try:
        ET.indent(root, space='    ')
    except Exception:
        pass
    data = ET.tostring(root, encoding='unicode')
    (Path(temp) / 'meta.xml').write_text(data, encoding='utf-8')


def zip_folder_stored(source, destination):
    source = Path(source)
    destination = Path(destination)
    if destination.exists():
        destination.unlink()
    with zipfile.ZipFile(str(destination), 'w', compression=zipfile.ZIP_STORED) as z:
        # no directory entries: avoids resource conflict when testing alongside other packages.
        for p in sorted(source.rglob('*')):
            if p.is_dir():
                continue
            arc = str(p.relative_to(source)).replace('\\', '/')
            info = zipfile.ZipInfo(arc)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            with open(str(p), 'rb') as f:
                z.writestr(info, f.read())


def main():
    os.chdir(str(ROOT))
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', default=None, help='Override package version')
    ap.add_argument('--python', default=None, help='Path to Python 2.7 executable')
    ap.add_argument('--no-docker', action='store_true', help='Do not fallback to Docker python:2.7')
    ap.add_argument('--skip-compile', action='store_true', help='Use existing .pyc files in python/')
    ap.add_argument('--keep-pyc', action='store_true', help='Do not delete generated .pyc after build')
    args = ap.parse_args()

    cfg = json.loads(Path('build.json').read_text(encoding='utf-8'))
    if args.version:
        cfg['info']['version'] = args.version

    temp = Path('temp')
    build = Path('build')
    rm(temp)
    rm(build)
    temp.mkdir(parents=True)
    build.mkdir(parents=True)

    if not args.skip_compile:
        compile_python(args.python, allow_docker=not args.no_docker)

    if Path('resources/in').is_dir():
        copytree('resources/in', temp / 'res')

    copy_compiled_python('python', temp / 'res/scripts/client')
    write_meta(temp, cfg['info'])

    out_name = '{}_{}.wotmod'.format(cfg['info']['id'], cfg['info']['version'])
    out_path = build / out_name
    zip_folder_stored(temp, out_path)
    print('Created {}'.format(out_path))

    if not args.keep_pyc:
        clean_pyc()
    rm(temp)


if __name__ == '__main__':
    main()
