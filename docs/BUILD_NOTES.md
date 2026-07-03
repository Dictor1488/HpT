# Build notes

- Source repo stores Python as `.py` only.
- Builder compiles `python/**/*.py` with Python 2.7 to `.pyc`.
- Packaged `.wotmod` contains `res/scripts/client/gui/mods/mod_custom_hpbar_gameface.pyc`, not `.py`.
- `.wotmod` is packed with `ZIP_STORED`, no compression.
- Directory entries are skipped to reduce conflicts with patch packages.
