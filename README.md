# Custom HP Bar — Gameface test project for WoT/Mir Tankov

This is a **test Gameface/WULF version** of the custom top team HP bar. It is not Scaleform/SWF.

The project contains:

- `res/gui/gameface/mods/custom_hpbar/index.html` — Gameface layout
- `res/gui/gameface/mods/custom_hpbar/index.css` — visual style converted from the AS3 bar
- `res/gui/gameface/mods/custom_hpbar/index.js` — Gameface logic, model updates and mock preview
- `res/scripts/client/gui/mods/mod_custom_hpbar_gameface.py` — Python/WULF bridge and battle HP listener
- `res/mods/configs/res_map/custom_hpbar_gameface.json` — layout registration for OpenWG.Gameface
- `.github/workflows/build-wotmod.yml` — packs everything into `.wotmod`

## Important dependency

This test uses `OpenWG.Gameface` helpers, especially `ModDynAccessor` / `res_id_by_key`, because WoT needs a `res_map` resource registration for custom Gameface layouts.

Install/load `OpenWG.Gameface` together with this mod. Without it, the Python script will log an error and the window will not load.

## How to build on GitHub

1. Create a new GitHub repo.
2. Upload this project.
3. Open **Actions → Build Gameface HPBar wotmod → Run workflow**.
4. Download artifact `custom-hpbar-gameface-wotmod`.
5. Put the `.wotmod` into your WoT `mods/<game_version>/` folder.

## Local build

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_wotmod.ps1
```

Linux/macOS:

```bash
python3 tools/build_wotmod.py
```

Output:

```text
build/custom_hpbar_gameface.wotmod
```

## What is implemented

The frontend receives these model fields:

```text
alliesHp, enemiesHp, totalAlliesHp, totalEnemiesHp,
allyPct, enemyPct, alliesFrags, enemiesFrags, diff,
visible, ready
```

The visual bar is drawn with HTML/CSS/JS and uses the same logic as the AS3 version:

- left ally HP fill from current percent to center;
- right enemy HP fill from center to current percent;
- percent labels;
- HP numbers;
- central score;
- diff box below;
- `TOP_Y = 8px` equivalent via CSS variable `--top-y`.

## How to test only UI

Open this in a normal browser:

```text
res/gui/gameface/mods/custom_hpbar/index.html?mock=1
```

The JS will animate mock HP values. In the game, it uses `window.model` and `viewEnv.onDataChanged`.

## Notes

This is a first Gameface/WULF test build. If the `.wotmod` loads but nothing appears, check `python.log` for lines containing:

```text
[CustomHPBarGF]
```

If the window loads but does not receive HP updates, the hook point is the battle field controller patch in `mod_custom_hpbar_gameface.py`.
