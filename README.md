# Custom HPBar Gameface — Watch-like structure

This project follows the same resource layout style as `UnderPressurePH7/Watch`:

```text
resources/in/mods/configs/res_map/...
resources/in/gui/gameface/mods/...
resources/in/scripts/client/gui/mods/...
resources/meta.xml
```

The build script packages it as:

```text
meta.xml
res/mods/configs/res_map/...
res/gui/gameface/mods/...
res/scripts/client/gui/mods/...
```

Build locally:

```powershell
./tools/build_wotmod.ps1
```

Or use GitHub Actions: **Build Watch-Structure Gameface HPBar**.

OpenWG.Gameface is required for the `mods/configs/res_map/*.json` layout registration.
