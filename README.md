# Custom HPBar Gameface - compiled pyc build

Цей варіант зібраний за логікою `UnderPressurePH7/Sensitivity`:

- Python код лежить у `python/gui/mods/mod_custom_hpbar_gameface.py`
- На GitHub Actions ставиться Python 2.7
- `build.py` компілює `.py` у `.pyc`
- У `.wotmod` кладеться тільки `.pyc`, а не `.py`
- Архів `.wotmod` пакується `ZIP_STORED`, тобто без стиснення

Після запуску в `python.log` мають з'явитися маркери:

```text
[CustomHPBarGF] module import started
[CustomHPBarGF] BattleFieldCtrl hooks installed
```

Якщо цих рядків немає — мод не імпортується як Python-мод.
