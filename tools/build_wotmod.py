# -*- coding: utf-8 -*-
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESOURCES = os.path.join(ROOT, 'resources')
INPUT = os.path.join(RESOURCES, 'in')
META = os.path.join(RESOURCES, 'meta.xml')
BUILD = os.path.join(ROOT, 'build')
OUT = os.path.join(BUILD, 'custom_hpbar_gameface_watch_structure.wotmod')


def main():
    if not os.path.isdir(BUILD):
        os.makedirs(BUILD)
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(META, 'meta.xml')
        for dirpath, _, filenames in os.walk(INPUT):
            for name in filenames:
                full = os.path.join(dirpath, name)
                rel_inside_res = os.path.relpath(full, INPUT).replace('\\', '/')
                z.write(full, 'res/' + rel_inside_res)
    print('Built:', OUT)
    with zipfile.ZipFile(OUT, 'r') as z:
        for item in z.namelist():
            print(' -', item)


if __name__ == '__main__':
    main()
