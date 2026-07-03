# -*- coding: utf-8 -*-
# Custom HPBar Gameface mod, Watch-like resource layout. Source version for GitHub build.
# Python 2.7 compatible.

import json
import logging

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags
from gui.impl.pub import ViewImpl, WindowImpl
from gui.battle_control.controllers import battle_field_ctrl
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener

_logger = logging.getLogger('[CustomHPBarGF]')
print '[CustomHPBarGF] module import started v0.0.18-source'

RES_MAP_ITEM_ID = 'mods/custom_hpbar/CustomHPBarBattle/layoutID'

try:
    from openwg_gameface import ModDynAccessor
    _OPENWG_OK = True
except Exception as _err:
    ModDynAccessor = None
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
    """One payload string, same practical pattern as WatchClock.js reads window.model.payload."""

    def __init__(self, properties=1, commands=1):
        super(CustomHPBarModel, self).__init__(properties=properties, commands=commands)

    def _initialize(self):
        super(CustomHPBarModel, self)._initialize()
        self._addStringProperty('payload', '{}')
        self.onReady = self._addCommand('onReady')
        self.onReady += self.__onReady

    def __onReady(self, *args):
        _logger.info('Gameface view ready: %s', args)

    def getPayload(self):
        return self._getString(0)

    def setPayload(self, value):
        self._setString(0, value)


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
        self.__alliesHp = 0
        self.__enemiesHp = 0
        self.__totalAlliesHp = 0
        self.__totalEnemiesHp = 0
        self.__alliesFrags = 0
        self.__enemiesFrags = 0
        self.__visible = True
        self.__scale = 1.0
        self.__allyVehicles = []
        self.__enemyVehicles = []
        self.__colorBlind = False

    @property
    def viewModel(self):
        return super(CustomHPBarView, self).getViewModel()

    def __push(self):
        alliesHp = max(0, _safe_int(self.__alliesHp))
        enemiesHp = max(0, _safe_int(self.__enemiesHp))
        totalAlliesHp = max(alliesHp, _safe_int(self.__totalAlliesHp))
        totalEnemiesHp = max(enemiesHp, _safe_int(self.__totalEnemiesHp))
        payload = {
            'visible': bool(self.__visible),
            'scale': self.__scale,
            'alliesHp': alliesHp,
            'enemiesHp': enemiesHp,
            'totalAlliesHp': totalAlliesHp,
            'totalEnemiesHp': totalEnemiesHp,
            'allyPct': _percent(alliesHp, totalAlliesHp),
            'enemyPct': _percent(enemiesHp, totalEnemiesHp),
            'alliesFrags': _safe_int(self.__alliesFrags),
            'enemiesFrags': _safe_int(self.__enemiesFrags),
            'diff': alliesHp - enemiesHp,
            'colorBlind': bool(self.__colorBlind),
            'allyVehicles': self.__allyVehicles,
            'enemyVehicles': self.__enemyVehicles
        }
        try:
            raw = json.dumps(payload, separators=(',', ':'))
        except Exception:
            raw = '{}'
        with self.viewModel.transaction() as model:
            model.setPayload(raw)

    def updateHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        self.__alliesHp = alliesHP
        self.__enemiesHp = enemiesHP
        self.__totalAlliesHp = totalAlliesHP
        self.__totalEnemiesHp = totalEnemiesHP
        self.__visible = True
        self.__push()

    def updateScore(self, alliesFrags, enemiesFrags):
        self.__alliesFrags = alliesFrags
        self.__enemiesFrags = enemiesFrags
        self.__visible = True
        self.__push()

    _CLASS_TAGS = ('heavyTank', 'mediumTank', 'lightTank', 'SPG', 'AT-SPG')
    _CLASS_MAP = {
        'heavyTank': 'heavy', 'mediumTank': 'medium', 'lightTank': 'light',
        'SPG': 'spg', 'AT-SPG': 'atspg',
    }
    # display order: TT, ST, PT, LT, SAU
    _ORDER = {'heavy': 0, 'medium': 1, 'atspg': 2, 'light': 3, 'spg': 4, 'unknown': 5}

    def updateVehicles(self):
        try:
            import BigWorld
            player = BigWorld.player()
            if player is None:
                return
            arena = getattr(player, 'arena', None)
            if arena is None:
                return
            vehicles = getattr(arena, 'vehicles', None)
            if not vehicles:
                return
            myTeam = getattr(player, 'team', None)
            ally = []
            enemy = []
            for vid, vData in vehicles.iteritems():
                try:
                    team = vData.get('team', None)
                    vType = vData.get('vehicleType', None)
                    cls = self.__classFromType(vType)
                    alive = 1 if vData.get('isAlive', True) else 0
                    entry = (self._ORDER.get(cls, 5), alive, '%s,%d' % (cls, alive))
                    if team == myTeam:
                        ally.append(entry)
                    else:
                        enemy.append(entry)
                except Exception:
                    continue
            ally.sort(key=lambda t: (0 if t[1] else 1, t[0]))
            enemy.sort(key=lambda t: (0 if t[1] else 1, t[0]))
            self.__allyVehicles = [e[2] for e in ally]
            self.__enemyVehicles = [e[2] for e in enemy]
            self.__colorBlind = self.__isColorBlind()
            self.__visible = True
            self.__push()
        except Exception:
            _logger.exception('updateVehicles failed')

    def __classFromType(self, vType):
        try:
            if vType is None:
                return 'unknown'
            typeObj = getattr(vType, 'type', vType)
            tags = getattr(typeObj, 'tags', None)
            if tags:
                for t in self._CLASS_TAGS:
                    if t in tags:
                        return self._CLASS_MAP.get(t, 'unknown')
            ct = getattr(typeObj, 'classTag', None)
            if ct:
                return self._CLASS_MAP.get(ct, 'unknown')
        except Exception:
            pass
        return 'unknown'

    def __isColorBlind(self):
        try:
            from helpers import dependency
            from skeletons.account_helpers.settings_core import ISettingsCore
            core = dependency.instance(ISettingsCore)
            return bool(core.getSetting('isColorBlind'))
        except Exception:
            return False

    def hide(self):
        self.__visible = False
        try:
            self.__push()
        except Exception:
            pass


class CustomHPBarWindow(WindowImpl):
    def __init__(self):
        super(CustomHPBarWindow, self).__init__(wndFlags=WindowFlags.WINDOW, content=CustomHPBarView())


class CustomHPBarBattleListener(IBattleFieldListener):
    def __init__(self):
        self.window = None
        self.view = None
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
            _logger.info('Custom HPBar Gameface window loaded')
        except Exception:
            _logger.exception('Failed to load Custom HPBar Gameface window')
            self.window = None
            self.view = None

    def destroy(self):
        if self.view is not None:
            try:
                self.view.hide()
            except Exception:
                pass
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        self.view = None

    def updateVehicleHealth(self, vehicleID, newHealth, maxHealth):
        pass

    def updateTeamHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        self.loadWindow()
        if self.view is not None:
            try:
                self.view.updateHealth(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP)
                self.view.updateVehicles()
            except Exception:
                _logger.exception('updateTeamHealth failed')

    def updateDeadVehicles(self, aliveAllies, deadAllies, aliveEnemies, deadEnemies):
        # Battle Observer default scoreboard logic: left score = dead enemies, right score = dead allies.
        self.loadWindow()
        if self.view is not None:
            try:
                self.view.updateScore(len(deadEnemies), len(deadAllies))
                self.view.updateVehicles()
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
    print '[CustomHPBarGF] BattleFieldCtrl hooks installed'
    _logger.info('BattleFieldCtrl hooks installed')


_installHook()
