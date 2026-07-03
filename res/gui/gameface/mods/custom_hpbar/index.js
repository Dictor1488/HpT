(function () {
  'use strict';

  const BASE_WIDTH = 1052;
  const RULER_LEN = 294;
  const $ = (sel) => document.querySelector(sel);

  const state = {
    alliesHp: 0,
    enemiesHp: 0,
    totalAlliesHp: 0,
    totalEnemiesHp: 0,
    allyPct: 0,
    enemyPct: 0,
    alliesFrags: 0,
    enemiesFrags: 0,
    diff: 0,
    visible: true,
    ready: false
  };

  function clamp(v, min, max) {
    return Math.max(min, Math.min(max, v));
  }

  function pct(current, total) {
    if (!total || total <= 0) return 100;
    return clamp(Math.round(current / total * 100), 0, 100);
  }

  function px(n) { return n + 'px'; }

  function setText(sel, value) {
    const el = $(sel);
    if (el) el.textContent = value;
  }

  function createRulerLabels() {
    const ally = $('.ally-ruler-labels');
    const enemy = $('.enemy-ruler-labels');
    if (!ally || !enemy || ally.children.length) return;

    const allyVals = [100, 80, 60, 40, 20, 0];
    const enemyVals = [0, 20, 40, 60, 80, 100];
    for (let i = 0; i < 6; i++) {
      const a = document.createElement('div');
      a.className = 'ruler-label';
      a.textContent = allyVals[i];
      a.style.left = px(RULER_LEN * i / 5);
      ally.appendChild(a);

      const e = document.createElement('div');
      e.className = 'ruler-label';
      e.textContent = enemyVals[i];
      e.style.left = px(RULER_LEN * i / 5);
      enemy.appendChild(e);
    }
  }

  function applyScale() {
    const holder = $('.hpbar-holder');
    if (!holder) return;
    const width = window.innerWidth || BASE_WIDTH;
    // Keep original size on normal 1920+ widths; shrink gently only on smaller screens.
    const scale = clamp(width / 1920, 0.82, 1.0);
    holder.style.setProperty('--hud-scale', scale.toFixed(3));
  }

  function updateFromModel() {
    if (window.model) {
      state.alliesHp = Number(window.model.alliesHp || 0);
      state.enemiesHp = Number(window.model.enemiesHp || 0);
      state.totalAlliesHp = Number(window.model.totalAlliesHp || 0);
      state.totalEnemiesHp = Number(window.model.totalEnemiesHp || 0);
      state.alliesFrags = Number(window.model.alliesFrags || 0);
      state.enemiesFrags = Number(window.model.enemiesFrags || 0);
      state.visible = window.model.visible !== false;
      state.ready = Boolean(window.model.ready);
      state.allyPct = Number(window.model.allyPct || pct(state.alliesHp, state.totalAlliesHp));
      state.enemyPct = Number(window.model.enemyPct || pct(state.enemiesHp, state.totalEnemiesHp));
      state.diff = Number(window.model.diff || (state.alliesHp - state.enemiesHp));
    }
    render();
  }

  function render() {
    const root = $('#custom-hpbar-root');
    if (!root) return;

    root.classList.toggle('hpbar-hidden', !state.visible);

    const allyPct = clamp(state.allyPct, 0, 100);
    const enemyPct = clamp(state.enemyPct, 0, 100);

    const allyStart = RULER_LEN * (100 - allyPct) / 100;
    const allyW = RULER_LEN - allyStart;
    const enemyW = RULER_LEN * enemyPct / 100;

    const allyFillWrap = $('.ally-fill-wrap');
    const allyHatchWrap = $('.ally-hatch-wrap');
    if (allyFillWrap) {
      allyFillWrap.style.left = px(allyStart);
      allyFillWrap.style.width = px(allyW);
      $('.ally-fill').style.width = px(allyW);
    }
    if (allyHatchWrap) {
      allyHatchWrap.style.left = px(allyStart);
      allyHatchWrap.style.width = px(allyW);
      $('.ally-hatch').style.width = px(allyW);
    }

    const enemyFillWrap = $('.enemy-fill-wrap');
    const enemyHatchWrap = $('.enemy-hatch-wrap');
    if (enemyFillWrap) {
      enemyFillWrap.style.left = '0px';
      enemyFillWrap.style.width = px(enemyW);
      $('.enemy-fill').style.width = px(enemyW);
    }
    if (enemyHatchWrap) {
      enemyHatchWrap.style.left = '0px';
      enemyHatchWrap.style.width = px(enemyW);
      $('.enemy-hatch').style.width = px(enemyW);
    }

    setText('.ally-hp', Math.max(0, state.alliesHp));
    setText('.enemy-hp', Math.max(0, state.enemiesHp));
    setText('.ally-pct', allyPct + '%');
    setText('.enemy-pct', enemyPct + '%');
    setText('.center-score', state.alliesFrags + ' : ' + state.enemiesFrags);
    setText('.diff-text', (state.diff > 0 ? '+' : '') + state.diff);

    const allyPctEl = $('.ally-pct');
    if (allyPctEl) allyPctEl.style.left = px(allyStart);
    const enemyPctEl = $('.enemy-pct');
    if (enemyPctEl) enemyPctEl.style.left = px(enemyW);

    const diff = $('.diff-box');
    if (diff) {
      diff.classList.toggle('diff-negative', state.diff < 0);
      diff.classList.toggle('diff-positive', state.diff >= 0);
    }
  }

  function startMock() {
    let t = 0;
    state.totalAlliesHp = 15000;
    state.totalEnemiesHp = 15000;
    state.alliesFrags = 1;
    state.enemiesFrags = 2;
    state.visible = true;
    setInterval(() => {
      t += 0.04;
      state.alliesHp = Math.round(9800 + Math.sin(t) * 1800);
      state.enemiesHp = Math.round(10200 + Math.cos(t * 0.8) * 2200);
      state.allyPct = pct(state.alliesHp, state.totalAlliesHp);
      state.enemyPct = pct(state.enemiesHp, state.totalEnemiesHp);
      state.diff = state.alliesHp - state.enemiesHp;
      if (Math.floor(t) % 8 === 0) {
        state.alliesFrags = 1 + (Math.floor(t / 8) % 5);
        state.enemiesFrags = 2 + (Math.floor(t / 10) % 5);
      }
      render();
    }, 80);
  }

  function init() {
    createRulerLabels();
    applyScale();
    window.addEventListener('resize', applyScale);

    const params = new URLSearchParams(window.location.search);
    if (params.get('mock') === '1' || typeof engine === 'undefined') {
      startMock();
      return;
    }

    engine.whenReady.then(() => {
      engine.on('viewEnv.onDataChanged', updateFromModel);
      engine.on('clientResized', applyScale);
      engine.on('self.onScaleUpdated', applyScale);
      updateFromModel();
      if (window.model && window.model.onReady) {
        window.model.onReady({ ready: true });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
