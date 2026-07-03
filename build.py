# -*- coding: utf-8 -*-
import argparse, json, os, pathlib, shutil, subprocess, sys, xml.etree.ElementTree as ET, zipfile


def copytree(src, dst, ignore=None):
    src=pathlib.Path(src); dst=pathlib.Path(dst); dst.mkdir(parents=True, exist_ok=True)
    ignored=set()
    if ignore: ignored=set(ignore(str(src), os.listdir(str(src))))
    for name in os.listdir(str(src)):
        if name in ignored or '.gitkeep' in name: continue
        s=src/name; d=dst/name
        if s.is_dir(): copytree(s,d,ignore)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(s), str(d))

def zip_folder(source, destination):
    source=pathlib.Path(source)
    with zipfile.ZipFile(str(destination), 'w', zipfile.ZIP_STORED) as z:
        for p in source.rglob('*'):
            arc=str(p.relative_to(source)).replace('\\','/')
            if p.is_dir():
                if not arc.endswith('/'): arc+='/'
                info=zipfile.ZipInfo(arc)
                info.compress_type=zipfile.ZIP_STORED
                z.writestr(info, '')
            else:
                info=zipfile.ZipInfo(arc)
                info.compress_type=zipfile.ZIP_STORED
                info.external_attr=33206 << 16
                z.writestr(info, p.read_bytes())

def compile_python(pyexe):
    src=pathlib.Path('python')
    for p in src.rglob('*.py'):
        print('Compiling {}'.format(p))
        subprocess.check_call([pyexe, '-m', 'py_compile', str(p)])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--version', default=None)
    ap.add_argument('--python', default=None)
    args=ap.parse_args()
    cfg=json.load(open('build.json','r'))
    if args.version: cfg['info']['version']=args.version
    pyexe=args.python or os.environ.get('PYTHON27') or cfg['software'].get('python') or 'python'
    temp=pathlib.Path('temp'); build=pathlib.Path('build')
    if temp.exists(): shutil.rmtree(str(temp))
    if build.exists(): shutil.rmtree(str(build))
    temp.mkdir(); build.mkdir()
    compile_python(pyexe)
    if pathlib.Path('resources/in').is_dir(): copytree('resources/in', temp/'res')
    # copy only compiled python, NOT .py source, like UnderPressurePH7/Sensitivity build.py
    copytree('python', temp/'res/scripts/client', ignore=shutil.ignore_patterns('*.py'))
    root=ET.Element('root')
    for k in ['id','version','name','description']:
        ET.SubElement(root,k).text=cfg['info'].get(k,'')
    try: ET.indent(root, space='    ')
    except Exception: pass
    (temp/'meta.xml').write_text(ET.tostring(root, encoding='unicode'), encoding='utf-8')
    name='{}_{}.wotmod'.format(cfg['info']['id'], cfg['info']['version'])
    zip_folder(temp, build/name)
    print('Created {}'.format(build/name))
    for p in pathlib.Path('python').rglob('*.pyc'):
        try: p.unlink()
        except Exception: pass

if __name__=='__main__': main()
