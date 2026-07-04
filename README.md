# Custom HPBar Gameface 

Custom World of Tanks Gameface HP bar with team HP, percentage scale, vehicle-state icons, HP difference box, and custom score rendering.

Python source is stored as `.py` in the repository. The build script compiles it with Python 2.7 and packages only `.pyc` into the `.wotmod`.

## Release 

- Keeps the stock `FragCorrelationBar` present for game layout purposes.
- Makes the stock frag bar transparent with `alpha=0` while keeping `visible=true` and full layout mask.
- Prevents the personal mission/LBZ block from jumping upward.
- Draws the custom Gameface score at the normal HUD position.
- Removes the visual black masking overlay used during testing.
- Keeps the TAB suppression hook so the custom bar disappears immediately on the TAB battle screen.
- Keeps the loading-screen guard so the HP bar waits for the battle scene instead of using a fixed delay.

