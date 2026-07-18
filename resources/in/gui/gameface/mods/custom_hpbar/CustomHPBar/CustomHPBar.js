(function () {
    'use strict';

    var BASE_WIDTH = 1052;
    var BASE_HEIGHT = 118;
    var RULER_LEN = 360;
    var GAP_CENTER = 95;
    var BAR_Y = 36;
    var TOP_Y = 0;
    var FILL_H = 4;
    var HATCH_GAP = 3.3;
    var HATCH_H = 10.4;
    var SEGMENTS = 5;
    var SEG_GAP = 2.5;
    var HATCH_STEP = 3.05;
    var HATCH_SLANT = 5.8;
    // Base scale tuned for 1080p (1920x1080). The stock game HUD scales its
    // panels with screen height, so to keep the custom bar the same physical
    // size on higher resolutions (1440p/2K, 4K) we scale this value by the
    // ratio of the current screen height to the 1080p reference height.
    var GAMEFACE_SCALE_BASE = 0.82;
    var REFERENCE_HEIGHT = 1080;
    var GAMEFACE_SCALE_FIX = GAMEFACE_SCALE_BASE; // recomputed per-frame in resizeWindow()
    var SHOW_CUSTOM_SCORE = true;
    var SHOW_CUSTOM_ICONS = true;
    var ICON_SIZE = 22;
    var ICON_GAP = 0;
    var ICON_SLOT = 20;

    var C_GREEN = '#95EB59';
    var C_RED = '#EE2528';
    var C_WHITE = '#F3F5F7';
    var C_RULER = '#A8B5BF';
    var C_LABEL = '#8FA0AD';
    var C_HATCH = '#C6D0DA';
    var C_CONNECT = '#A9B6C0';
    var C_BOXLINE = '#92A0AC';

    var NS = 'http://www.w3.org/2000/svg';
    var root = document.getElementById('hpbar-root');
    var holder = document.getElementById('hpbar-holder');
    var svg = document.getElementById('hud');
    var lastPayload = null;
    var lastSize = null;
    var renderId = 0;
    var pollTimer = null;

    var state = {
        visible: false,
        alliesHp: 0,
        enemiesHp: 0,
        totalAlliesHp: 0,
        totalEnemiesHp: 0,
        allyPct: 100,
        enemyPct: 100,
        alliesFrags: 0,
        enemiesFrags: 0,
        diff: 0,
        alliesIcons: [],
        enemiesIcons: []
    };

    function num(v, d) { v = Number(v); return isNaN(v) ? d : v; }
    function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
    function lerp(a, b, t) { return a + (b - a) * t; }
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
    function rgba(hex, alpha) {
        var n = parseInt(hex.replace('#', ''), 16);
        return 'rgba(' + ((n >> 16) & 255) + ', ' + ((n >> 8) & 255) + ', ' + (n & 255) + ', ' + alpha + ')';
    }
    function el(name, attrs, parent) {
        var e = document.createElementNS(NS, name);
        if (attrs) {
            for (var k in attrs) if (attrs.hasOwnProperty(k)) e.setAttribute(k, attrs[k]);
        }
        if (parent) parent.appendChild(e);
        return e;
    }
    function clearSvg() {
        while (svg && svg.firstChild) svg.removeChild(svg.firstChild);
    }
    function glyphWidth(ch, size) {
        if (ch === ' ') return size * 0.28;
        if (ch === ':') return size * 0.22;
        if (ch === '%') return size * 0.66;
        if (ch === '+' || ch === '-') return size * 0.48;
        if (ch === 'Х' || ch === 'X' || ch === 'П' || ch === 'P') return size * 0.62;
        return size * 0.62;
    }
    function vectorTextWidth(value, size) {
        value = String(value);
        var w = 0;
        for (var i = 0; i < value.length; i++) w += glyphWidth(value.charAt(i), size) + size * 0.08;
        return Math.max(0, w - size * 0.08);
    }
    function drawSeg(parent, x1, y1, x2, y2, size, color, alpha) {
        return line(x1, y1, x2, y2, color || C_WHITE, Math.max(1.1, size * 0.075), alpha === undefined ? 1 : alpha, parent, { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', filter: 'url(#vecShadow)' });
    }
    function drawDot(parent, cx, cy, r, color, alpha) {
        return el('circle', { cx: cx, cy: cy, r: r, fill: color || C_WHITE, opacity: alpha === undefined ? 1 : alpha, filter: 'url(#vecShadow)' }, parent || svg);
    }
    function drawGlyph(parent, ch, x, y, size, color, alpha) {
        var w = glyphWidth(ch, size);
        var h = size;
        var l = x + w * 0.10, r = x + w * 0.90;
        var t = y + h * 0.10, m = y + h * 0.50, b = y + h * 0.90;
        var seg = {
            A: [l, t, r, t], B: [r, t, r, m], C: [r, m, r, b], D: [l, b, r, b],
            E: [l, m, l, b], F: [l, t, l, m], G: [l, m, r, m]
        };
        var map = {
            '0': 'ABCDEF', '1': 'BC', '2': 'ABGED', '3': 'ABGCD', '4': 'FBGC',
            '5': 'AFGCD', '6': 'AFGECD', '7': 'ABC', '8': 'ABCDEFG', '9': 'ABFGCD'
        };
        function s(name) { var a = seg[name]; drawSeg(parent, a[0], a[1], a[2], a[3], size, color, alpha); }
        if (map[ch]) { for (var i = 0; i < map[ch].length; i++) s(map[ch].charAt(i)); return w; }
        if (ch === ':') { drawDot(parent, x + w * .5, y + h * .35, size * .055, color, alpha); drawDot(parent, x + w * .5, y + h * .68, size * .055, color, alpha); return w; }
        if (ch === '+') { drawSeg(parent, x + w*.20, y + h*.50, x + w*.80, y + h*.50, size, color, alpha); drawSeg(parent, x + w*.50, y + h*.22, x + w*.50, y + h*.78, size, color, alpha); return w; }
        if (ch === '-') { drawSeg(parent, x + w*.20, y + h*.50, x + w*.80, y + h*.50, size, color, alpha); return w; }
        if (ch === '%') { drawDot(parent, x + w*.28, y + h*.30, size*.10, color, alpha); drawDot(parent, x + w*.72, y + h*.72, size*.10, color, alpha); drawSeg(parent, x + w*.75, y + h*.18, x + w*.24, y + h*.88, size, color, alpha); return w; }
        if (ch === 'Х' || ch === 'X') { drawSeg(parent, x+w*.15, y+h*.15, x+w*.85, y+h*.85, size, color, alpha); drawSeg(parent, x+w*.85, y+h*.15, x+w*.15, y+h*.85, size, color, alpha); return w; }
        if (ch === 'П') { drawSeg(parent, x+w*.16, y+h*.85, x+w*.16, y+h*.15, size, color, alpha); drawSeg(parent, x+w*.16, y+h*.15, x+w*.84, y+h*.15, size, color, alpha); drawSeg(parent, x+w*.84, y+h*.15, x+w*.84, y+h*.85, size, color, alpha); return w; }
        if (ch === 'P') { drawSeg(parent, x+w*.16, y+h*.85, x+w*.16, y+h*.15, size, color, alpha); drawSeg(parent, x+w*.16, y+h*.15, x+w*.75, y+h*.15, size, color, alpha); drawSeg(parent, x+w*.75, y+h*.15, x+w*.75, y+h*.50, size, color, alpha); drawSeg(parent, x+w*.16, y+h*.50, x+w*.75, y+h*.50, size, color, alpha); return w; }
        return w;
    }
    function vectorText(value, x, y, size, anchor, alpha, color, parent) {
        value = String(value);
        var width = vectorTextWidth(value, size);
        var startX = x;
        if (anchor === 'middle') startX = x - width / 2;
        else if (anchor === 'end') startX = x - width;
        var cx = startX;
        for (var i = 0; i < value.length; i++) {
            var ch = value.charAt(i);
            drawGlyph(parent || svg, ch, cx, y, size, color || C_WHITE, alpha === undefined ? 1 : alpha);
            cx += glyphWidth(ch, size) + size * 0.08;
        }
    }
    function scoreGlyphWidth(ch, size) {
        if (ch === ':') return size * 0.22;
        return size * 0.58;
    }
    function scoreTextWidth(value, size) {
        value = String(value);
        var w = 0;
        for (var i = 0; i < value.length; i++) w += scoreGlyphWidth(value.charAt(i), size) + size * 0.11;
        return Math.max(0, w - size * 0.11);
    }
    function scorePath(parent, d, x, y, size, color, alpha) {
        return el('path', {
            d: d,
            transform: 'translate(' + x + ',' + y + ') scale(' + size + ')',
            fill: 'none',
            stroke: color || C_WHITE,
            'stroke-width': 0.118,
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            opacity: alpha === undefined ? 1 : alpha,
            filter: 'url(#vecShadow)'
        }, parent || svg);
    }
    function drawScoreGlyph(parent, ch, x, y, size, color, alpha) {
        var paths = {
            '0': 'M.29 .13 C.13 .24 .11 .73 .30 .87 C.42 .96 .64 .96 .76 .84 C.91 .69 .90 .29 .73 .15 C.60 .05 .41 .05 .29 .13',
            '1': 'M.34 .30 L.55 .12 L.55 .88 M.36 .88 L.74 .88',
            '2': 'M.20 .29 C.28 .09 .70 .07 .80 .28 C.91 .52 .31 .60 .21 .88 L.82 .88',
            '3': 'M.22 .16 C.74 .03 .91 .36 .54 .50 C.94 .58 .80 .98 .22 .84',
            '4': 'M.78 .88 L.78 .12 M.78 .62 L.20 .62 L.66 .13',
            '5': 'M.80 .13 L.30 .13 L.24 .45 C.64 .34 .91 .53 .80 .77 C.69 .98 .34 .95 .20 .78',
            '6': 'M.78 .19 C.49 .03 .17 .28 .16 .61 C.15 .89 .39 .98 .61 .88 C.86 .77 .78 .48 .54 .47 C.35 .46 .18 .58 .17 .70',
            '7': 'M.19 .13 L.84 .13 L.45 .88',
            '8': 'M.50 .50 C.28 .48 .20 .35 .26 .21 C.34 .04 .67 .04 .76 .21 C.83 .35 .72 .48 .50 .50 C.24 .53 .16 .72 .28 .86 C.39 .99 .63 .99 .75 .86 C.88 .71 .76 .53 .50 .50',
            '9': 'M.24 .81 C.53 .98 .84 .73 .84 .40 C.85 .13 .61 .04 .39 .14 C.15 .25 .22 .54 .46 .55 C.65 .56 .82 .44 .83 .32'
        };
        if (ch === ':') {
            drawDot(parent, x + size * 0.11, y + size * 0.34, size * 0.048, color, alpha);
            drawDot(parent, x + size * 0.11, y + size * 0.66, size * 0.048, color, alpha);
            return scoreGlyphWidth(ch, size);
        }
        if (paths[ch]) scorePath(parent, paths[ch], x, y, size, color, alpha);
        return scoreGlyphWidth(ch, size);
    }
    function scoreText(value, x, y, size, anchor, alpha, color, parent) {
        value = String(value);
        var width = scoreTextWidth(value, size);
        var startX = x;
        if (anchor === 'middle') startX = x - width / 2;
        else if (anchor === 'end') startX = x - width;
        var cx = startX;
        for (var i = 0; i < value.length; i++) {
            var ch = value.charAt(i);
            cx += drawScoreGlyph(parent || svg, ch, cx, y, size, color || C_WHITE, alpha === undefined ? 1 : alpha) + size * 0.11;
        }
    }

    function text(value, x, y, size, anchor, alpha, color, parent) {
        value = String(value);
        var baseline = y + size * 0.82;
        var txt = el('text', {
            x: x,
            y: baseline,
            fill: color || C_WHITE,
            opacity: alpha === undefined ? 1 : alpha,
            'font-size': size,
            'font-family': 'Inter, Segoe UI, Roboto, Arial, sans-serif',
            'font-weight': size >= 24 ? 800 : 700,
            'text-anchor': (anchor === 'end' ? 'end' : (anchor === 'middle' ? 'middle' : 'start')),
            'letter-spacing': '0',
            filter: 'url(#vecShadow)'
        }, parent || svg);
        txt.textContent = value;
        return txt;
    }
    function rect(x, y, w, h, fill, opacity, parent) {
        return el('rect', {
            x: x, y: y, width: Math.max(0, w), height: Math.max(0, h),
            fill: fill, opacity: opacity === undefined ? 1 : opacity
        }, parent || svg);
    }
    function line(x1, y1, x2, y2, stroke, width, opacity, parent, extra) {
        var attrs = {
            x1: x1, y1: y1, x2: x2, y2: y2,
            stroke: stroke, 'stroke-width': width || 1, opacity: opacity === undefined ? 1 : opacity,
            'stroke-linecap': 'square'
        };
        if (extra) {
            for (var k in extra) if (extra.hasOwnProperty(k)) attrs[k] = extra[k];
        }
        return el('line', attrs, parent || svg);
    }

    function resizeWindow() {
        // NOTE: clientWidth/clientHeight below describe the *screen* and are only
        // used to derive the adaptive scale (bigger screens -> bigger bar). They
        // must NOT be used as the native Gameface surface size: in Gameface the
        // native surface itself is the hit-test surface, and transparent pixels
        // inside it are NOT click-through to the Scaleform battle HUD underneath.
        // A full-screen surface here silently blocks mouse input everywhere in
        // battle, which is why we size the surface to the bar itself below.
        var clientWidth = BASE_WIDTH;
        var clientHeight = REFERENCE_HEIGHT;
        if (window.viewEnv && viewEnv.getClientSizePx) {
            try {
                var c = viewEnv.getClientSizePx();
                clientWidth = Math.max(clientWidth, Math.round(num(c.width, BASE_WIDTH)));
                clientHeight = Math.max(1, Math.round(num(c.height, REFERENCE_HEIGHT)));
            } catch (e) {}
        }
        if (typeof window.innerWidth === 'number' && window.innerWidth > 0) {
            clientWidth = Math.max(clientWidth, Math.round(window.innerWidth));
        }
        if (typeof window.innerHeight === 'number' && window.innerHeight > 0) {
            clientHeight = Math.max(clientHeight, Math.round(window.innerHeight));
        }

        // Adaptive scale: keep the bar the same physical size as on 1080p by
        // scaling with screen height. At 1080p ratio = 1 -> 0.82 (unchanged).
        // At 1440p ratio ~= 1.333 -> ~1.09. At 2160p -> ~1.64.
        var ratio = clientHeight / REFERENCE_HEIGHT;
        // Clamp to a sane range so odd reported sizes can't blow up the bar.
        if (ratio < 0.75) ratio = 0.75;
        if (ratio > 2.5) ratio = 2.5;
        GAMEFACE_SCALE_FIX = GAMEFACE_SCALE_BASE * ratio;

        // Size the *native surface* to the bar's own scaled footprint, not the
        // screen, so the hit-test surface is tightly fitted to the visible panel
        // and can no longer block clicks elsewhere in the battle HUD.
        var surfaceWidth = Math.ceil(BASE_WIDTH * GAMEFACE_SCALE_FIX);
        var height = Math.ceil(BASE_HEIGHT * GAMEFACE_SCALE_FIX) + 18;
        var size = surfaceWidth + 'x' + height;
        if (size !== lastSize && window.viewEnv && viewEnv.resizeViewPx) {
            lastSize = size;
            viewEnv.resizeViewPx(surfaceWidth, height);
            // Tell Python the new surface size so it can re-center the window.
            // The window can't center itself from CSS anymore now that the
            // surface is sized to the bar instead of the full screen.
            try {
                if (window.model && typeof window.model.onResized === 'function') {
                    window.model.onResized(surfaceWidth, height);
                }
            } catch (e) {}
        }
        // No horizontal centering transform needed anymore: once the native
        // surface is exactly the bar's width, the surface itself should be
        // centered on screen (via the window's own position), not the content
        // inside an oversized surface.
        if (holder) holder.style.transform = 'scale(' + GAMEFACE_SCALE_FIX + ')';
    }

    function defs() {
        var d = el('defs', {}, svg);
        var filter = el('filter', { id: 'txtShadow', x: '-30%', y: '-30%', width: '160%', height: '160%' }, d);
        el('feDropShadow', { dx: '0', dy: '0', stdDeviation: '2.0', 'flood-color': 'rgba(0,0,0,.95)' }, filter);
        var soft = el('filter', { id: 'softGlow', x: '-25%', y: '-60%', width: '150%', height: '220%' }, d);
        el('feDropShadow', { dx: '0', dy: '0', stdDeviation: '1.4', 'flood-color': 'currentColor', 'flood-opacity': '.45' }, soft);
        var vec = el('filter', { id: 'vecShadow', x: '-40%', y: '-40%', width: '180%', height: '180%' }, d);
        el('feDropShadow', { dx: '0', dy: '0', stdDeviation: '1.7', 'flood-color': 'black', 'flood-opacity': '.95' }, vec);
        return d;
    }

    function drawRuler(x0, x1, y, group) {
        var segLen = (x1 - x0) / SEGMENTS;
        for (var i = 0; i < SEGMENTS; i++) {
            var sx = x0 + segLen * i;
            var ex = sx + segLen;
            var a = Math.min(sx, ex) + SEG_GAP / 2;
            var b = Math.max(sx, ex) - SEG_GAP / 2;
            rect(a, y - 1.3, b - a, 1.5, C_RULER, .42, group);
        }
    }

    function drawFill(xFrom, xTo, outer, inner, y, color, ally, group, defsNode) {
        var lo = Math.min(xFrom, xTo);
        var hi = Math.max(xFrom, xTo);
        if (hi <= lo) return;

        var segLen = (outer - inner) / SEGMENTS;
        for (var i = 0; i < SEGMENTS; i++) {
            var sx = inner + segLen * i;
            var ex = sx + segLen;
            var a = Math.min(sx, ex) + SEG_GAP / 2;
            var b = Math.max(sx, ex) - SEG_GAP / 2;
            var fa = Math.max(a, lo);
            var fb = Math.min(b, hi);
            if (fb > fa) {
                rect(fa, y - FILL_H / 2, fb - fa, FILL_H, color, 1, group)
                    .setAttribute('filter', 'url(#softGlow)');
            }
        }

        var hy = y + FILL_H / 2 + HATCH_GAP;
        for (i = 0; i < SEGMENTS; i++) {
            sx = inner + segLen * i;
            ex = sx + segLen;
            a = Math.min(sx, ex) + SEG_GAP / 2;
            b = Math.max(sx, ex) - SEG_GAP / 2;
            fa = Math.max(a, lo);
            fb = Math.min(b, hi);
            if (fb <= fa) continue;

            var clipId = 'clip_' + renderId + '_' + (ally ? 'a' : 'e') + '_' + i;
            var cp = el('clipPath', { id: clipId, clipPathUnits: 'userSpaceOnUse' }, defsNode);
            rect(fa, hy - 1, fb - fa, HATCH_H + 2, '#fff', 1, cp);

            var hx = fa - HATCH_SLANT * 1.15;
            while (hx < fb + HATCH_SLANT) {
                var x1 = Math.max(hx, fa - HATCH_SLANT);
                var x2 = hx + HATCH_SLANT;
                if (ally) {
                    line(x1, hy, x2, hy + HATCH_H, C_HATCH, 1.05, .46, group, { 'clip-path': 'url(#' + clipId + ')' });
                } else {
                    line(x1, hy + HATCH_H, x2, hy, C_HATCH, 1.05, .46, group, { 'clip-path': 'url(#' + clipId + ')' });
                }
                hx += HATCH_STEP;
            }
        }
    }

    function drawDiffBox(midX, yy, connFromX, connFromY, group) {
        var bw = 76, bh = 25, rad = 6;
        var bx = midX - Math.floor(bw / 2);
        var by = yy + 32;
        var diffColor = state.diff >= 0 ? C_GREEN : C_RED;
        var midY = by + bh / 2;

        var run = midY - connFromY;
        var diagEndX = connFromX + run;
        if (diagEndX > bx) diagEndX = bx;
        var elbowR = 4;
        var diagPreX = diagEndX - elbowR * .707;
        var diagPreY = midY - elbowR * .707;
        var pathData = 'M ' + connFromX + ' ' + connFromY + ' L ' + diagPreX + ' ' + diagPreY + ' Q ' + diagEndX + ' ' + midY + ' ' + (diagEndX + elbowR) + ' ' + midY + ' L ' + bx + ' ' + midY;
        el('path', { d: pathData, fill: 'none', stroke: C_CONNECT, 'stroke-width': 1.25, opacity: .58 }, group);

        el('rect', { x: bx, y: by, width: bw, height: bh, rx: rad, ry: rad, fill: 'rgba(0,0,0,.34)', stroke: C_BOXLINE, 'stroke-width': 1, opacity: 1 }, group);

        // Corner brackets aligned to the box outline.
        var inset = 0.8;
        var len = 8.5;
        var sw = 2.35;
        function seg(x1, y1, x2, y2) {
            el('line', {
                x1: x1, y1: y1, x2: x2, y2: y2,
                stroke: diffColor,
                'stroke-width': sw,
                opacity: 1,
                'stroke-linecap': 'round'
            }, group);
        }
        // TL
        seg(bx + inset, by + len, bx + inset, by + 2.2);
        seg(bx + 2.2, by + inset, bx + len, by + inset);
        // TR
        seg(bx + bw - inset, by + len, bx + bw - inset, by + 2.2);
        seg(bx + bw - len, by + inset, bx + bw - 2.2, by + inset);
        // BL
        seg(bx + inset, by + bh - len, bx + inset, by + bh - 2.2);
        seg(bx + 2.2, by + bh - inset, bx + len, by + bh - inset);
        // BR
        seg(bx + bw - inset, by + bh - len, bx + bw - inset, by + bh - 2.2);
        seg(bx + bw - len, by + bh - inset, bx + bw - 2.2, by + bh - inset);

        var sign = state.diff >= 0 ? '+ ' : '- ';
        text(sign + fmt(Math.abs(state.diff)), midX, midY - 8.5, 14, 'middle', 1, C_WHITE, group);
    }


    function iconFile(name) {
        if (!name) name = 'alive_unknown';
        return 'icons/' + name + '.png';
    }

    function iconVisualScale(name) {
        name = String(name || '');
        if (name.indexOf('_atspg') !== -1) return 0.80;
        if (name.indexOf('_light') !== -1) return 0.84;
        if (name.indexOf('_spg') !== -1) return 0.64;
        if (name.indexOf('_medium') !== -1) return 1.00;
        if (name.indexOf('_heavy') !== -1) return 1.00;
        return 0.94;
    }

    function drawTeamIcons(list, xStart, xEnd, y, isEnemy, group) {
        list = list || [];
        var maxCount = Math.min(15, list.length || 0);
        if (maxCount <= 0) return;

        var step = ICON_SLOT + ICON_GAP;
        var totalW = maxCount * ICON_SLOT + (maxCount - 1) * ICON_GAP;
        var x = isEnemy ? xStart : (xEnd - totalW);
        var yy = y + 1;

        // Mirror the ally row so both teams read from the center outward.
        var renderList = list.slice(0, maxCount);
        if (!isEnemy) renderList.reverse();

        for (var i = 0; i < maxCount; i++) {
            var name = renderList[i] || 'alive_unknown';
            var isDead = name.indexOf('dead_') === 0 || name.indexOf('cb_dead') === 0;
            var scale = iconVisualScale(name);
            var drawSize = Math.round(ICON_SIZE * scale);
            var imgX = Math.round(x + i * step + (ICON_SLOT - drawSize) / 2);
            var imgY = Math.round(yy + (ICON_SLOT - drawSize) / 2);
            var img = el('image', {
                x: imgX,
                y: imgY,
                width: drawSize,
                height: drawSize,
                opacity: isDead ? 0.38 : 1,
                preserveAspectRatio: 'xMidYMid meet'
            }, group);
            var href = iconFile(name);
            img.setAttributeNS('http://www.w3.org/1999/xlink', 'href', href);
            img.setAttribute('href', href);
        }
    }

    function draw() {
        if (!svg || !root) return;
        root.className = state.visible ? '' : 'hidden';
        if (!state.visible) return;
        resizeWindow();
        renderId += 1;
        clearSvg();
        var d = defs();
        var g = el('g', { transform: 'translate(0,' + TOP_Y + ')' }, svg);

        var midX = Math.floor(BASE_WIDTH / 2);
        var yy = BAR_Y;
        var allyInner = midX - GAP_CENTER;
        var allyOuter = allyInner - RULER_LEN;
        var enInner = midX + GAP_CENTER;
        var enOuter = enInner + RULER_LEN;
        var allyPct = clamp(Math.round(num(state.allyPct, 0)), 0, 100);
        var enemyPct = clamp(Math.round(num(state.enemyPct, 0)), 0, 100);

        drawRuler(allyOuter, allyInner, yy, g);
        drawRuler(enInner, enOuter, yy, g);

        var allyPctX = lerp(allyOuter, allyInner, (100 - allyPct) / 100);
        var enPctX = lerp(enInner, enOuter, enemyPct / 100);
        drawFill(allyPctX, allyInner, allyOuter, allyInner, yy, C_GREEN, true, g, d);
        drawFill(enInner, enPctX, enOuter, enInner, yy, C_RED, false, g, d);
        if (SHOW_CUSTOM_ICONS) {
            drawTeamIcons(state.alliesIcons, allyOuter, allyInner, yy + 15, false, g);
            drawTeamIcons(state.enemiesIcons, enInner, enOuter, yy + 15, true, g);
        }

        var allyVals = [100, 80, 60, 40, 20, 0];
        var enVals = [0, 20, 40, 60, 80, 100];
        for (var i = 0; i < 6; i++) {
            text(String(allyVals[i]), lerp(allyOuter, allyInner, i / 5), yy - 22, 12, 'middle', .28, C_LABEL, g);
            text(String(enVals[i]), lerp(enInner, enOuter, i / 5), yy - 22, 12, 'middle', .28, C_LABEL, g);
        }

        text(allyPct + '%', allyPctX, yy - 24, 14, 'middle', 1, C_WHITE, g);
        text(enemyPct + '%', enPctX, yy - 24, 14, 'middle', 1, C_WHITE, g);

        var allyHpText = fmt(state.alliesHp);
        var enemyHpText = fmt(state.enemiesHp);
        var allyHpX = allyOuter - 12;
        var enemyHpX = enOuter + 12;
        text(allyHpText, allyHpX, yy - 6, 22, 'end', 1, C_WHITE, g);
        text(enemyHpText, enemyHpX, yy - 6, 22, 'start', 1, C_WHITE, g);

        var allyW = vectorTextWidth(allyHpText, 22);
        var enemyW = vectorTextWidth(enemyHpText, 22);
        text('ХП', allyHpX - allyW / 2, yy - 22, 15, 'middle', 1, C_WHITE, g);
        text('ХП', enemyHpX + enemyW / 2, yy - 22, 15, 'middle', 1, C_WHITE, g);

        if (SHOW_CUSTOM_SCORE) {
            var scoreG = el('g', { transform: 'translate(' + midX + ',' + (yy - 12) + ') scale(1.35)' }, g);
            text(String(state.alliesFrags), -24, 0, 22, 'middle', 1, C_WHITE, scoreG);
            text(':', 0, 0, 22, 'middle', 1, C_WHITE, scoreG);
            text(String(state.enemiesFrags), 24, 0, 22, 'middle', 1, C_WHITE, scoreG);
        }

        var hatchAnchorX = allyInner;
        var hatchBottomY = yy + FILL_H / 2 + HATCH_GAP + HATCH_H;
        drawDiffBox(midX, yy, hatchAnchorX, hatchBottomY, g);
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
        state.alliesIcons = cfg.alliesIcons || [];
        state.enemiesIcons = cfg.enemiesIcons || [];
        return true;
    }

    function tick() {
        readPayload();
        draw();
    }

    function initialize() {
        tick();
        window.setTimeout(tick, 100);
        window.setTimeout(tick, 500);
        // Gameface/WULF data-change event is not always fired for a string payload,
        // so poll the ViewModel too. This makes HP/diff update during battle/replay.
        if (!pollTimer) pollTimer = window.setInterval(tick, 150);
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
        // Browser preview fallback.
        state.visible = true;
        state.alliesHp = 7420;
        state.enemiesHp = 6380;
        state.allyPct = 72;
        state.enemyPct = 58;
        state.alliesFrags = 1;
        state.enemiesFrags = 2;
        state.diff = 1040;
        state.alliesIcons = ['alive_ally_heavy','alive_ally_medium','alive_ally_light','dead_ally_atspg','alive_ally_spg'];
        state.enemiesIcons = ['alive_enemy_heavy','alive_enemy_medium','dead_enemy_light','alive_enemy_atspg','alive_enemy_spg'];
        initialize();
    }
}());
