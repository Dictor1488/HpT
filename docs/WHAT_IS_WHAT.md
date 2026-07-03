# Що за що відповідає

## Gameface frontend

- `index.html` — каркас вікна Gameface.
- `index.css` — весь вигляд HP bar: ширина, верхній відступ, шкали, hatch-лінії, HP цифри, рахунок і diff box.
- `index.js` — читає `window.model`, підписується на `viewEnv.onDataChanged`, рахує ширину fill bar і оновлює DOM.

## Python/WULF backend

- `CustomHPBarModel` — поля, які доступні в JS через `window.model`.
- `CustomHPBarView` — створює `ViewSettings(... model=CustomHPBarModel())` і змінює model через `transaction()`.
- `CustomHPBarWindow` — вікно `WindowImpl`, яке завантажує Gameface layout.
- `CustomHPBarBattleListener` — приймає `updateTeamHealth` / `updateDeadVehicles` від `BattleFieldCtrl`.
- `_patched_setViewComponents` — додає наш listener у список `_viewComponents`, через який WG вже розсилає HP updates.

## Resource map

- `res/mods/configs/res_map/custom_hpbar_gameface.json` — реєструє Layout `CUSTOM_HPBAR_GAMEFACE_LAYOUT`.
- `openwg_gameface.ModDynAccessor` — дає Python доступ до цього layout ID.

## Основні налаштування розміру

У CSS:

```css
--base-width: 1052px;
--top-y: 8px;
--ruler-len: 294px;
--gap-center: 95px;
--bar-y: 36px;
```

`--top-y` — головне, що відповідає за вертикальну позицію. Масштаб під маленькі екрани — у `applyScale()` в `index.js`.
