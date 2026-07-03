# -*- coding: utf-8 -*-
# Custom HP Bar Gameface / WULF test mod
# Python 2.7 compatible.

import logging
import BigWorld

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags
from gui.impl.pub import ViewImpl, WindowImpl

from gui.battle_control.controllers import battle_field_ctrl
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener

_logger = logging.getLogger('[CustomHPBarGF]')

RES_MAP_ITEM_ID = 'CUSTOM_HPBAR_GAMEFACE_LAYOUT'

try:
    from openwg_gameface import ModDynAccessor, res_id_by_key
    _OPENWG_OK = True
except Exception as _err:
    ModDynAccessor = None
    res_id_by_key = None
    _OPENWG_OK = False
    _logger.error('OpenWG.Gameface is not available: %s', _err)


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _percent(current, total):
    current = max(0, _safe_int(current))
    total = max(0, _safe_int(total))
    if total <= 0:
        return 100
    return max(0, min(100, int(round(float(current) / float(total) * 100.0))))


class CustomHPBarModel(ViewModel):
    def __init__(self, properties=12, commands=1):
        super(CustomHPBarModel, self).__init__(properties=properties, commands=commands)

    def _initialize(self):
        super(CustomHPBarModel, self)._initialize()
        self._addNumberProperty('alliesHp', 0)
        self._addNumberProperty('enemiesHp', 0)
        self._addNumberProperty('totalAlliesHp', 0)
        self._addNumberProperty('totalEnemiesHp', 0)
        self._addNumberProperty('allyPct', 100)
        self._addNumberProperty('enemyPct', 100)
        self._addNumberProperty('alliesFrags', 0)
        self._addNumberProperty('enemiesFrags', 0)
        self._addNumberProperty('diff', 0)
        self._addBoolProperty('visible', True)
        self._addBoolProperty('ready', False)
        self._addStringProperty('debugText', '')
        self.onReady = self._addCommand('onReady')
        self.onReady += self.__onReady

    def __onReady(self, args):
        self.setReady(True)
        _logger.info('Gameface view reported ready: %s', args)

    def getAlliesHp(self): return self._getNumber(0)
    def setAlliesHp(self, value): self._setNumber(0, _safe_int(value))

    def getEnemiesHp(self): return self._getNumber(1)
    def setEnemiesHp(self, value): self._setNumber(1, _safe_int(value))

    def getTotalAlliesHp(self): return self._getNumber(2)
    def setTotalAlliesHp(self, value): self._setNumber(2, _safe_int(value))

    def getTotalEnemiesHp(self): return self._getNumber(3)
    def setTotalEnemiesHp(self, value): self._setNumber(3, _safe_int(value))

    def getAllyPct(self): return self._getNumber(4)
    def setAllyPct(self, value): self._setNumber(4, _safe_int(value))

    def getEnemyPct(self): return self._getNumber(5)
    def setEnemyPct(self, value): self._setNumber(5, _safe_int(value))

    def getAlliesFrags(self): return self._getNumber(6)
    def setAlliesFrags(self, value): self._setNumber(6, _safe_int(value))

    def getEnemiesFrags(self): return self._getNumber(7)
    def setEnemiesFrags(self, value): self._setNumber(7, _safe_int(value))

    def getDiff(self): return self._getNumber(8)
    def setDiff(self, value): self._setNumber(8, _safe_int(value))

    def getVisible(self): return self._getBool(9)
    def setVisible(self, value): self._setBool(9, bool(value))

    def getReady(self): return self._getBool(10)
    def setReady(self, value): self._setBool(10, bool(value))

    def getDebugText(self): return self._getString(11)
    def setDebugText(self, value): self._setString(11, str(value))


class CustomHPBarView(ViewImpl):
    if _OPENWG_OK:
        viewLayoutID = ModDynAccessor(RES_MAP_ITEM_ID)
    else:
        viewLayoutID = None

    def __init__(self):
        if not _OPENWG_OK:
            raise RuntimeError('OpenWG.Gameface is required')
        settings = ViewSettings(CustomHPBarView.viewLayoutID(), flags=ViewFlags.VIEW, model=CustomHPBarModel())
        super(CustomHPBarView, self).__init__(settings)

    @property
    def viewModel(self):
        return super(CustomHPBarView, self).getViewModel()

    def updateHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        with self.viewModel.transaction() as model:
            alliesHP = max(0, _safe_int(alliesHP))
            enemiesHP = max(0, _safe_int(enemiesHP))
            totalAlliesHP = max(alliesHP, _safe_int(totalAlliesHP))
            totalEnemiesHP = max(enemiesHP, _safe_int(totalEnemiesHP))
            model.setAlliesHp(alliesHP)
            model.setEnemiesHp(enemiesHP)
            model.setTotalAlliesHp(totalAlliesHP)
            model.setTotalEnemiesHp(totalEnemiesHP)
            model.setAllyPct(_percent(alliesHP, totalAlliesHP))
            model.setEnemyPct(_percent(enemiesHP, totalEnemiesHP))
            model.setDiff(alliesHP - enemiesHP)
            model.setVisible(True)

    def updateScore(self, alliesFrags, enemiesFrags):
        with self.viewModel.transaction() as model:
            model.setAlliesFrags(_safe_int(alliesFrags))
            model.setEnemiesFrags(_safe_int(enemiesFrags))
            model.setVisible(True)

    def hide(self):
        try:
            with self.viewModel.transaction() as model:
                model.setVisible(False)
        except Exception:
            pass


class CustomHPBarWindow(WindowImpl):
    def __init__(self):
        super(CustomHPBarWindow, self).__init__(wndFlags=WindowFlags.WINDOW, content=CustomHPBarView())


class CustomHPBarBattleListener(IBattleFieldListener):
    def __init__(self):
        self.window = None
        self.view = None
        self.lastHealth = (0, 0, 0, 0)
        self.lastScore = (0, 0)
        self.loadWindow()

    def loadWindow(self):
        if not _OPENWG_OK:
            return
        if self.window is not None:
            return
        try:
            self.window = CustomHPBarWindow()
            self.window.load()
            self.view = self.window.content
            _logger.info('Gameface window loaded')
        except Exception:
            _logger.exception('Failed to load Gameface window')
            self.window = None
            self.view = None

    def destroy(self):
        if self.view is not None:
            self.view.hide()
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        self.view = None

    def updateVehicleHealth(self, vehicleID, newHealth, maxHealth):
        # Not needed for top team bar; team totals are delivered through updateTeamHealth.
        pass

    def updateTeamHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        self.lastHealth = (alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP)
        self.loadWindow()
        if self.view is not None:
            try:
                self.view.updateHealth(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP)
            except Exception:
                _logger.exception('updateTeamHealth failed')

    def updateDeadVehicles(self, aliveAllies, deadAllies, aliveEnemies, deadEnemies):
        # Same logic as Battle Observer default mode: score is dead enemies : dead allies.
        alliesScore = len(deadEnemies)
        enemiesScore = len(deadAllies)
        self.lastScore = (alliesScore, enemiesScore)
        self.loadWindow()
        if self.view is not None:
            try:
                self.view.updateScore(alliesScore, enemiesScore)
            except Exception:
                _logger.exception('updateDeadVehicles failed')


_listener = None
_orig_setViewComponents = None
_orig_stopControl = None


def _getListener():
    global _listener
    if _listener is None:
        _listener = CustomHPBarBattleListener()
    return _listener


def _patched_setViewComponents(self, *components):
    # BattleFieldCtrl forwards HP/team updates to every object in _viewComponents.
    # We append our own IBattleFieldListener-compatible object without replacing WG components.
    listener = _getListener()
    if listener not in components:
        components = components + (listener,)
    return _orig_setViewComponents(self, *components)


def _patched_stopControl(self):
    global _listener
    try:
        if _listener is not None:
            _listener.destroy()
            _listener = None
    except Exception:
        _logger.exception('Failed to destroy listener')
    return _orig_stopControl(self)


def _installHook():
    global _orig_setViewComponents, _orig_stopControl
    if _orig_setViewComponents is not None:
        return
    _orig_setViewComponents = battle_field_ctrl.BattleFieldCtrl.setViewComponents
    _orig_stopControl = battle_field_ctrl.BattleFieldCtrl.stopControl
    battle_field_ctrl.BattleFieldCtrl.setViewComponents = _patched_setViewComponents
    battle_field_ctrl.BattleFieldCtrl.stopControl = _patched_stopControl
    _logger.info('BattleFieldCtrl hooks installed')


_installHook()
