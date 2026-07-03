(function () {
    'use strict';

    var BASE_WIDTH = 1052;
    var BASE_HEIGHT = 118;
    var RULER_LEN = 294;
    var GAP_CENTER = 95;
    var BAR_Y = 36;
    var FILL_H = 4;
    var HATCH_GAP = 3.3;
    var HATCH_H = 10.4;
    var SEGMENTS = 5;
    var SEG_GAP = 2.5;
    var HATCH_STEP = 3.05;
    var HATCH_SLANT = 5.8;
    var GAMEFACE_SCALE_FIX = 0.74;

    // ---- tank marker geometry (ported from Flash HudBarComponent) ----
    var MARKER_START = 100;   // first icon, distance from center
    var MARKER_SHIFT = 19;    // step between icons
    var MARKER_ROW_Y = 66;    // row Y
    var MARKER_SCALE = 1.10;  // 32px * scale
    var MARKER_MAX = 15;

    var MID_X = Math.floor(BASE_WIDTH / 2);
    var ALLY_INNER = MID_X - GAP_CENTER;
    var ALLY_OUTER = ALLY_INNER - RULER_LEN;
    var ENEMY_INNER = MID_X + GAP_CENTER;
    var ENEMY_OUTER = ENEMY_INNER + RULER_LEN;

    var lastPayload = null;
    var lastSize = null;
    var root = document.getElementById('hpbar-root');
    var holder = document.getElementById('hpbar-holder');

    var state = {
        visible: true,
        alliesHp: 0, enemiesHp: 0,
        totalAlliesHp: 0, totalEnemiesHp: 0,
        allyPct: 100, enemyPct: 100,
        alliesFrags: 0, enemiesFrags: 0,
        diff: 0,
        allyVehicles: [],   // each: {cls, alive}
        enemyVehicles: [],
        colorBlind: false
    };

    var lastMarkerKey = null;   // to avoid rebuilding rows every frame

    function num(v, d) { v = Number(v); return isNaN(v) ? d : v; }
    function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function px(n) { return Math.round(n) + 'px'; }
    function pct(current, total) {
        current = Math.max(0, num(current, 0));
        total = Math.max(0, num(total, 0));
        if (total <= 0) return 100;
        return clamp(Math.round(current / total * 100), 0, 100);
    }
    function fmt(v) {
        var sign = v < 0 ? '-' : '';
        return sign + Math.abs(Math.round(v)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    }
    function makeDiv(cls, parent) {
        var d = document.createElement('div');
        d.className = cls;
        if (parent) parent.appendChild(d);
        return d;
    }
    function clear(el) { while (el && el.firstChild) el.removeChild(el.firstChild); }

    function resizeWindow() {
        var clientWidth = BASE_WIDTH;
        if (window.viewEnv && viewEnv.getClientSizePx) {
            try {
                var c = viewEnv.getClientSizePx();
                clientWidth = Math.max(clientWidth, Math.round(num(c.width, BASE_WIDTH)));
            } catch (e) {}
        }
        if (typeof window.innerWidth === 'number' && window.innerWidth > 0) {
            clientWidth = Math.max(clientWidth, Math.round(window.innerWidth));
        }
        var height = Math.ceil(BASE_HEIGHT * GAMEFACE_SCALE_FIX) + 18;
        var size = clientWidth + 'x' + height;
        if (size !== lastSize && window.viewEnv && viewEnv.resizeViewPx) {
            lastSize = size;
            viewEnv.resizeViewPx(clientWidth, height);
        }
        if (holder) holder.style.transform = 'translateX(-50%) scale(' + GAMEFACE_SCALE_FIX + ')';
    }

    function buildTeam(layerId, isAlly) {
        var layer = document.getElementById(layerId);
        if (!layer || layer.getAttribute('data-built') === '1') return;
        layer.setAttribute('data-built', '1');

        var x0 = isAlly ? ALLY_OUTER : ENEMY_INNER;
        var x1 = isAlly ? ALLY_INNER : ENEMY_OUTER;
        var left = Math.min(x0, x1);
        var values = isAlly ? [100,80,60,40,20,0] : [0,20,40,60,80,100];

        var labels = makeDiv('labels', layer);
        labels.style.left = px(left);
        labels.style.top = px(BAR_Y - 22);
        labels.style.width = px(RULER_LEN);
        for (var i = 0; i < 6; i++) {
            var lab = makeDiv('label', labels);
            lab.textContent = values[i];
            lab.style.left = px(RULER_LEN * i / 5);
        }

        var ruler = makeDiv('ruler', layer);
        ruler.style.left = px(left);
        ruler.style.top = px(BAR_Y - 1);
        ruler.style.width = px(RULER_LEN);
        var segLen = RULER_LEN / SEGMENTS;
        for (i = 0; i < SEGMENTS; i++) {
            var a = segLen * i + SEG_GAP / 2;
            var b = segLen * (i + 1) - SEG_GAP / 2;
            var r = makeDiv('ruler-seg', ruler);
            r.style.left = px(a);
            r.style.width = px(b - a);
        }

        var fill = makeDiv(isAlly ? 'fill-line ally-fill-line' : 'fill-line enemy-fill-line', layer);
        fill.style.top = px(BAR_Y - FILL_H / 2);
        var hatch = makeDiv(isAlly ? 'hatch-row ally-hatch-row' : 'hatch-row enemy-hatch-row', layer);
        hatch.style.top = px(BAR_Y + FILL_H / 2 + HATCH_GAP);
    }

    function drawFill(layerId, percent, isAlly) {
        var layer = document.getElementById(layerId);
        if (!layer) return;
        var fill = layer.querySelector('.fill-line');
        var hatch = layer.querySelector('.hatch-row');
        if (!fill || !hatch) return;
        clear(fill); clear(hatch);

        var p = clamp(percent, 0, 100);
        var start = isAlly ? lerp(ALLY_OUTER, ALLY_INNER, (100 - p) / 100) : ENEMY_INNER;
        var end = isAlly ? ALLY_INNER : lerp(ENEMY_INNER, ENEMY_OUTER, p / 100);
        var lo = Math.min(start, end);
        var hi = Math.max(start, end);
        var width = Math.max(0, hi - lo);

        fill.style.left = px(lo);
        fill.style.width = px(width);
        hatch.style.left = px(lo);
        hatch.style.width = px(width);

        var segLen = RULER_LEN / SEGMENTS;
        var baseX = isAlly ? ALLY_OUTER : ENEMY_INNER;
        for (var i = 0; i < SEGMENTS; i++) {
            var sx = baseX + segLen * i + SEG_GAP / 2;
            var ex = baseX + segLen * (i + 1) - SEG_GAP / 2;
            var a = Math.max(sx, lo);
            var b = Math.min(ex, hi);
            if (b <= a) continue;

            var seg = makeDiv(isAlly ? 'fill-seg ally-fill' : 'fill-seg enemy-fill', fill);
            seg.style.left = px(a - lo);
            seg.style.width = px(b - a);

            var hseg = makeDiv('hatch-seg', hatch);
            hseg.style.left = px(a - lo);
            hseg.style.width = px(b - a);

            var hx = -HATCH_SLANT;
            while (hx < (b - a) + HATCH_SLANT) {
                var h = makeDiv(isAlly ? 'hatch-line ally-hatch' : 'hatch-line enemy-hatch', hseg);
                h.style.left = px(hx);
                hx += HATCH_STEP;
            }
        }

        var pctEl = document.getElementById(isAlly ? 'allyPct' : 'enemyPct');
        if (pctEl) {
            pctEl.textContent = p + '%';
            pctEl.style.left = px(isAlly ? start : end);
            pctEl.style.top = px(BAR_Y - 29);
        }
    }

    function updateHpCaptions() {
        var allyHp = document.getElementById('allyHp');
        var enemyHp = document.getElementById('enemyHp');
        var allyCap = document.getElementById('allyCaption');
        var enemyCap = document.getElementById('enemyCaption');
        if (allyHp) allyHp.textContent = fmt(state.alliesHp);
        if (enemyHp) enemyHp.textContent = fmt(state.enemiesHp);
        if (allyCap && allyHp) {
            allyCap.style.left = px(110 - Math.max(38, allyHp.offsetWidth / 2) - allyCap.offsetWidth / 2);
        }
        if (enemyCap && enemyHp) {
            enemyCap.style.left = px(942 + Math.max(38, enemyHp.offsetWidth / 2) - enemyCap.offsetWidth / 2);
        }
    }

    function readPayload() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw === lastPayload) return false;
        lastPayload = raw;
        var cfg = {};
        try { cfg = JSON.parse(raw || '{}'); } catch (e) { cfg = {}; }
        var alliesHp = Math.max(0, Math.round(num(cfg.alliesHp, 0)));
        var enemiesHp = Math.max(0, Math.round(num(cfg.enemiesHp, 0)));
        var totalAlliesHp = Math.max(alliesHp, Math.round(num(cfg.totalAlliesHp, alliesHp)));
        var totalEnemiesHp = Math.max(enemiesHp, Math.round(num(cfg.totalEnemiesHp, enemiesHp)));
        state.visible = cfg.visible !== false;
        state.alliesHp = alliesHp;
        state.enemiesHp = enemiesHp;
        state.totalAlliesHp = totalAlliesHp;
        state.totalEnemiesHp = totalEnemiesHp;
        state.allyPct = clamp(Math.round(num(cfg.allyPct, pct(alliesHp, totalAlliesHp))), 0, 100);
        state.enemyPct = clamp(Math.round(num(cfg.enemyPct, pct(enemiesHp, totalEnemiesHp))), 0, 100);
        state.alliesFrags = Math.round(num(cfg.alliesFrags, 0));
        state.enemiesFrags = Math.round(num(cfg.enemiesFrags, 0));
        state.diff = Math.round(num(cfg.diff, alliesHp - enemiesHp));
        // tank marker lists: array of "cls,alive" strings, or array of {cls,alive}
        state.colorBlind = cfg.colorBlind === true || cfg.colorBlind === 1;
        state.allyVehicles = parseVehicles(cfg.allyVehicles);
        state.enemyVehicles = parseVehicles(cfg.enemyVehicles);
        return true;
    }

    function parseVehicles(list) {
        var out = [];
        if (!list) return out;
        for (var i = 0; i < list.length; i++) {
            var item = list[i];
            if (typeof item === 'string') {
                var parts = item.split(',');
                out.push({ cls: parts[0] || 'unknown', alive: parts[1] !== '0' });
            } else if (item && typeof item === 'object') {
                out.push({ cls: item.cls || 'unknown', alive: item.alive !== false && item.alive !== 0 });
            }
        }
        return out;
    }

    function iconUrl(team, cls, alive, colorBlind) {
        var state = alive ? 'alive' : 'dead';
        var name;
        if (colorBlind) {
            // colorblind set is team-agnostic
            name = 'cb_' + state + '_' + cls;
        } else if (cls === 'unknown') {
            name = state + '_unknown';
        } else {
            name = state + '_' + team + '_' + cls;
        }
        return 'coui://gui/gameface/mods/custom_hpbar/CustomHPBar/icons/' + name + '.png';
    }

    function markerKey() {
        // signature to detect when rows actually change (avoid rebuild per frame)
        function sig(list) {
            var s = '';
            for (var i = 0; i < list.length; i++) s += list[i].cls + (list[i].alive ? '1' : '0') + '|';
            return s;
        }
        return (state.colorBlind ? 'cb:' : '') + sig(state.allyVehicles) + '#' + sig(state.enemyVehicles);
    }

    function fillMarkerRow(rowId, vehicles, isAlly) {
        var row = document.getElementById(rowId);
        if (!row) return;
        clear(row);
        var startX = isAlly ? -MARKER_START : MARKER_START;
        var shift = isAlly ? -MARKER_SHIFT : MARKER_SHIFT;
        var n = Math.min(vehicles.length, MARKER_MAX);
        var size = 32 * MARKER_SCALE;
        var half = size / 2;
        for (var i = 0; i < n; i++) {
            var v = vehicles[i];
            var team = isAlly ? 'ally' : 'enemy';
            var m = makeDiv('marker', row);
            m.style.backgroundImage = 'url(' + iconUrl(team, v.cls, v.alive, state.colorBlind) + ')';
            m.style.width = px(size);
            m.style.height = px(size);
            m.style.backgroundSize = px(size) + ' ' + px(size);
            // center on slot x (MID_X + startX + i*shift), row centered on MARKER_ROW_Y
            var cx = MID_X + startX + i * shift;
            m.style.left = px(cx - half);
            m.style.top = px(MARKER_ROW_Y - half - 66); // row div already at top:66
        }
    }

    function renderMarkers() {
        var key = markerKey();
        if (key === lastMarkerKey) return;   // nothing changed
        lastMarkerKey = key;
        fillMarkerRow('allyMarkers', state.allyVehicles, true);
        fillMarkerRow('enemyMarkers', state.enemyVehicles, false);
    }

    function render() {
        if (!root) return;
        root.className = state.visible ? '' : 'hidden';
        if (!state.visible) return;
        resizeWindow();
        updateHpCaptions();
        drawFill('allyLayer', state.allyPct, true);
        drawFill('enemyLayer', state.enemyPct, false);
        renderMarkers();
        var score = document.getElementById('score');
        if (score) score.textContent = state.alliesFrags + ' : ' + state.enemiesFrags;
        var diff = document.getElementById('diff');
        var box = document.getElementById('diffBox');
        if (diff) diff.textContent = (state.diff >= 0 ? '+ ' : '- ') + fmt(Math.abs(state.diff));
        if (box) box.className = 'diff-box ' + (state.diff < 0 ? 'negative' : 'positive');
    }

    function tick() { readPayload(); render(); }

    function initialize() {
        buildTeam('allyLayer', true);
        buildTeam('enemyLayer', false);
        tick();
        window.setTimeout(tick, 100);
        window.setTimeout(tick, 500);
        if (window.engine) window.engine.on('viewEnv.onDataChanged', tick);
    }

    if (window.engine && window.engine.whenReady) {
        var domReady = window.isDomBuilt ? Promise.resolve() : new Promise(function (resolve) {
            window.engine.on('self.onDomBuilt', resolve);
        });
        Promise.all([window.engine.whenReady, domReady]).then(function () {
            requestAnimationFrame(function () { requestAnimationFrame(initialize); });
        });
    } else {
        initialize();
    }
}());
