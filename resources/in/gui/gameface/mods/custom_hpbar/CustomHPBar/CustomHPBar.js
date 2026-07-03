(function () {
    'use strict';

    var BASE_WIDTH = 1052;
    var BASE_HEIGHT = 104;
    var RULER_LEN = 294;
    var root = document.getElementById('hpbar-root');
    var holder = document.getElementById('hpbar-holder');
    var cfg = {};
    var lastPayload = null;
    var lastSize = null;

    function q(sel) { return document.querySelector(sel); }
    function px(n) { return Math.round(n) + 'px'; }
    function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
    function num(v, d) { v = Number(v); return isNaN(v) ? d : v; }

    function pct(current, total) {
        current = Math.max(0, num(current, 0));
        total = Math.max(0, num(total, 0));
        if (total <= 0) return 100;
        return clamp(Math.round(current / total * 100), 0, 100);
    }

    function setText(sel, value) {
        var el = q(sel);
        if (el) el.textContent = value;
    }

    function buildLabels() {
        var ally = q('.ally-labels');
        var enemy = q('.enemy-labels');
        if (!ally || !enemy || ally.children.length) return;
        var allyVals = [100, 80, 60, 40, 20, 0];
        var enemyVals = [0, 20, 40, 60, 80, 100];
        for (var i = 0; i < 6; i++) {
            var a = document.createElement('div');
            a.className = 'label';
            a.textContent = allyVals[i];
            a.style.left = px(RULER_LEN * i / 5);
            ally.appendChild(a);

            var e = document.createElement('div');
            e.className = 'label';
            e.textContent = enemyVals[i];
            e.style.left = px(RULER_LEN * i / 5);
            enemy.appendChild(e);
        }
    }

    function resizeWindow() {
        var scale = num(cfg.scale, 1);
        var width = Math.ceil(BASE_WIDTH * scale);
        var height = Math.ceil(BASE_HEIGHT * scale);
        var size = width + 'x' + height;
        if (size !== lastSize && window.viewEnv && viewEnv.resizeViewPx) {
            lastSize = size;
            viewEnv.resizeViewPx(width, height);
        }
        if (holder) holder.style.setProperty('--hud-scale', String(scale));
    }

    function readPayload() {
        var raw = window.model && window.model.payload ? String(window.model.payload) : '';
        if (raw === lastPayload) return false;
        lastPayload = raw;
        try {
            cfg = JSON.parse(raw || '{}');
        } catch (e) {
            cfg = {};
        }
        return true;
    }

    function render() {
        if (!root) return;
        var visible = cfg.visible !== false;
        root.className = visible ? '' : 'hidden';
        if (!visible) return;

        resizeWindow();

        var alliesHp = Math.max(0, Math.round(num(cfg.alliesHp, 0)));
        var enemiesHp = Math.max(0, Math.round(num(cfg.enemiesHp, 0)));
        var totalAlliesHp = Math.max(alliesHp, Math.round(num(cfg.totalAlliesHp, alliesHp)));
        var totalEnemiesHp = Math.max(enemiesHp, Math.round(num(cfg.totalEnemiesHp, enemiesHp)));
        var allyPct = clamp(Math.round(num(cfg.allyPct, pct(alliesHp, totalAlliesHp))), 0, 100);
        var enemyPct = clamp(Math.round(num(cfg.enemyPct, pct(enemiesHp, totalEnemiesHp))), 0, 100);
        var alliesFrags = Math.round(num(cfg.alliesFrags, 0));
        var enemiesFrags = Math.round(num(cfg.enemiesFrags, 0));
        var diff = Math.round(num(cfg.diff, alliesHp - enemiesHp));

        var allyStart = RULER_LEN * (100 - allyPct) / 100;
        var allyW = RULER_LEN - allyStart;
        var enemyW = RULER_LEN * enemyPct / 100;

        var allyFillClip = q('.ally-fill-clip');
        var allyHatchClip = q('.ally-hatch-clip');
        var allyFill = q('.ally-fill');
        var allyHatch = q('.ally-hatch');
        if (allyFillClip && allyFill) {
            allyFillClip.style.left = px(96 + allyStart);
            allyFillClip.style.width = px(allyW);
            allyFill.style.width = px(allyW);
        }
        if (allyHatchClip && allyHatch) {
            allyHatchClip.style.left = px(96 + allyStart);
            allyHatchClip.style.width = px(allyW);
            allyHatch.style.width = px(allyW);
        }

        var enemyFillClip = q('.enemy-fill-clip');
        var enemyHatchClip = q('.enemy-hatch-clip');
        var enemyFill = q('.enemy-fill');
        var enemyHatch = q('.enemy-hatch');
        if (enemyFillClip && enemyFill) {
            enemyFillClip.style.right = '96px';
            enemyFillClip.style.width = px(enemyW);
            enemyFill.style.width = px(enemyW);
        }
        if (enemyHatchClip && enemyHatch) {
            enemyHatchClip.style.right = '96px';
            enemyHatchClip.style.width = px(enemyW);
            enemyHatch.style.width = px(enemyW);
        }

        setText('.ally-hp', alliesHp);
        setText('.enemy-hp', enemiesHp);
        setText('.ally-pct', allyPct + '%');
        setText('.enemy-pct', enemyPct + '%');
        setText('#score', alliesFrags + ' : ' + enemiesFrags);
        setText('#diff', (diff > 0 ? '+' : '') + diff);

        var allyPctEl = q('.ally-pct');
        if (allyPctEl) allyPctEl.style.left = px(96 + allyStart);
        var enemyPctEl = q('.enemy-pct');
        if (enemyPctEl) enemyPctEl.style.right = px(96 + enemyW);

        var diffBox = q('.diff-box');
        if (diffBox) {
            diffBox.className = 'diff-box ' + (diff < 0 ? 'negative' : 'positive');
        }
    }

    function tick() {
        readPayload();
        render();
    }

    function startMock() {
        var t = 0;
        root.className = '';
        cfg = { visible: true, totalAlliesHp: 15000, totalEnemiesHp: 15000, alliesFrags: 1, enemiesFrags: 2, scale: 1 };
        window.setInterval(function () {
            t += 0.04;
            cfg.alliesHp = Math.round(9800 + Math.sin(t) * 1800);
            cfg.enemiesHp = Math.round(10200 + Math.cos(t * .8) * 2200);
            cfg.allyPct = pct(cfg.alliesHp, cfg.totalAlliesHp);
            cfg.enemyPct = pct(cfg.enemiesHp, cfg.totalEnemiesHp);
            cfg.diff = cfg.alliesHp - cfg.enemiesHp;
            render();
        }, 80);
    }

    function initialize() {
        buildLabels();
        if (!window.engine || !window.model) {
            startMock();
            return;
        }
        tick();
        window.engine.on('viewEnv.onDataChanged', tick);
        if (window.model && typeof window.model.onReady === 'function') {
            window.model.onReady({});
        }
    }

    function afterFrames() {
        requestAnimationFrame(function () {
            requestAnimationFrame(initialize);
        });
    }

    if (window.engine && window.engine.whenReady) {
        var domReady = window.isDomBuilt ? Promise.resolve() : new Promise(function (resolve) {
            window.engine.on('self.onDomBuilt', resolve);
        });
        Promise.all([window.engine.whenReady, domReady]).then(afterFrames);
    } else {
        afterFrames();
    }
}());
