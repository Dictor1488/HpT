# Structure notes

`under_pressure.watch.json` uses item IDs like:

```json
"mods/under_pressure/WatchBattle/layoutID"
```

This mod uses:

```json
"mods/custom_hpbar/CustomHPBarBattle/layoutID"
```

`WatchClock.js` reads configuration from `window.model.payload`, parses JSON, and resizes the Gameface view with `viewEnv.resizeViewPx`. This HP bar uses the same payload-string pattern.
