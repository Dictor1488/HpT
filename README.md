# Custom HPBar Gameface — source project v0.0.18

Це структурований GitHub-проєкт без готових `.pyc` у вихідному коді.
Python лежить як звичайний `.py`, щоб ти не втратив код. Builder сам компілює `.py` у Python 2.7 `.pyc` і пакує `.wotmod`.

## Структура

```text
python/gui/mods/mod_custom_hpbar_gameface.py
resources/in/gui/gameface/mods/custom_hpbar/CustomHPBar/CustomHPBarBattle.html
resources/in/gui/gameface/mods/custom_hpbar/CustomHPBar/CustomHPBar.css
resources/in/gui/gameface/mods/custom_hpbar/CustomHPBar/CustomHPBar.js
resources/in/mods/configs/res_map/custom_hpbar_gameface.json
build.py
build.json
.github/workflows/build-wotmod.yml
```

## Локальна збірка

Варіант 1 — якщо є `C:/Python27/python.exe` або змінна `PYTHON27`:

```bat
python build.py --version 0.0.18
```

Варіант 2 — PowerShell з явним Python 2.7:

```powershell
.uild_local.ps1 -Version 0.0.18 -Python27 "C:/Python27/python.exe"
```

Варіант 3 — Docker fallback. Якщо Python 2.7 не знайдений, `build.py` сам спробує Docker image `python:2.7`.

```bash
python build.py --version 0.0.18
```

Готовий файл буде тут:

```text
build/me.agent.custom_hpbar_gameface_0.0.18.wotmod
```

## GitHub Actions

Після push відкрий:

```text
Actions → Build Custom HPBar Gameface wotmod → Run workflow
```

Workflow використовує Python 3 для builder і Docker `python:2.7` для компіляції `.py` у `.pyc`.

## Важливо для тесту

У `World_of_Tanks/mods/2.3.0.1/` залишай тільки один файл нашого моду, наприклад:

```text
me.agent.custom_hpbar_gameface_0.0.18.wotmod
```

Старі `me.agent.custom_hpbar_gameface_0.0.*.wotmod` краще видаляти, щоб ресурси не перекривались.
