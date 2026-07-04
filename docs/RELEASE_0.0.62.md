# Release 0.0.62

Finalized Gameface custom HP bar release.

## Changed

- The stock `FragCorrelationBar` remains visible to the game layout, but is made transparent with alpha only.
- Full stock layout mask is preserved so personal mission/LBZ widgets do not jump upward.
- Removed the temporary black masking overlay from the custom score area.
- Restored the custom score to the normal HUD position.
- Kept immediate TAB suppression for the custom bar.
- Kept battle-scene loading guard without a fixed delay.

## Build Artifact

```text
build/me.agent.custom_hpbar_gameface_0.0.62.wotmod
```

## Build Command

```bat
python build.py --version 0.0.62 --python C:/Python27/python.exe
```
