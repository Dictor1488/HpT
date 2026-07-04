v0.0.52: safe rollback of broken overlay move hook. HP bar unchanged from v0.0.41; WG timer/LBZ are not moved.

# Custom HPBar Gameface v0.0.52

Source project for WoT Gameface HP bar. Python source is kept as `.py`; builder compiles it to `.pyc` only during packaging.

This version uses SVG/DOM rendering instead of canvas, so the geometry is much closer to the original `HudBarInjector_visualization.html` while staying compatible with Gameface overlay rendering.

## Build

```bat
python build.py --version 0.0.52
```

Or run GitHub Actions: **Build Custom HPBar Gameface wotmod**.

Output:

```text
build/me.agent.custom_hpbar_gameface_0.0.52.wotmod
```


## v0.0.52 event bindings

Python now patches BattleFieldCtrl private update methods too: `__updateVehiclesHealth` and `__updateDeadVehicles`. This forces payload refresh whenever WoT recalculates team HP or score, even if the listener is not called through `_viewComponents`.


## v0.0.52

Adds direct hook for `gui.Scaleform.daapi.view.battle.shared.frag_correlation_bar.FragCorrelationBar` to suppress the stock WG top HP/frag correlation bar.


## FIXED archive
Default build scripts now use `0.0.52`, and Python contains the direct `FragCorrelationBar` hook.


## v0.0.52
- Stock FragCorrelationBar is kept only for vehicle icons/counter (mask=8).
- Stock HP/diff/advantage animation suppressed by not forwarding as_updateHPS.
- Custom 0:0 score restored.
- Custom PNG icon row disabled for now to avoid chaotic duplicate icons.


## v0.0.52 notes
- Stock FragCorrelationBar mask is now 0, so stock score/HP/advantage animation should be hidden.
- Custom score and custom ordered icons are drawn by Gameface.
- PlayersPanel is not suppressed.
