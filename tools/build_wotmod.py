import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BUILD = os.path.join(ROOT, 'build')
OUT = os.path.join(BUILD, 'custom_hpbar_gameface.wotmod')
INCLUDE_DIRS = ['res']

if not os.path.isdir(BUILD):
    os.makedirs(BUILD)

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for base in INCLUDE_DIRS:
        base_path = os.path.join(ROOT, base)
        for dirpath, _, filenames in os.walk(base_path):
            for name in filenames:
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, ROOT).replace('\\', '/')
                z.write(full, rel)

print('Built:', OUT)
