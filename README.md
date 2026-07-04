v0.0.61: safe rollback of broken overlay move hook. HP bar unchanged; WG timer/LBZ are not moved.

# Custom HPBar Gameface v0.0.61

Source project for WoT Gameface HP bar. Python source is kept as `.py`; builder compiles it to `.pyc` only during packaging.

This version uses SVG/DOM rendering instead of canvas, so the geometry is much closer to the original `HudBarInjector_visualization.html` while staying compatible with Gameface overlay rendering.
