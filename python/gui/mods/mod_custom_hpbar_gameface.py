# -*- coding: utf-8 -*-
# Custom HPBar Gameface mod, Watch-like resource layout. Source version for GitHub build.
# Python 2.7 compatible.

import json
import logging

import BigWorld

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags
from gui.impl.pub import ViewImpl, WindowImpl
from gui.battle_control.controllers import battle_field_ctrl
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener
from gui.battle_control.arena_info import vos_collections
from gui.Scaleform.daapi.view.battle.shared import frag_correlation_bar

_logger = logging.getLogger('[CustomHPBarGF]')
print '[CustomHPBarGF] module import started v0.0.61-source'

RES_MAP_ITEM_ID = 'mods/custom_hpbar/CustomHPBarBattle/layoutID'
POLL_INTERVAL = 0.20
HIDE_STOCK_TEAM_HP = True
FORCE_ONLY_CUSTOM_LISTENER = False
ARENA_SHOW_MIN_PERIOD = 1
_last_arena_gate_log = None


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


def _getArenaVehicle(player):
    """Best-effort loading-screen guard for period 1.

    The loading screen may already have arena.period == 1, so do not use a fixed
    timer. Only allow the bar once the player's vehicle is attached to the 3D
    scene. Python 2.7 compatible.
    """
    try:
        vehicle = None
        if hasattr(player, 'getVehicleAttached'):
            try:
                vehicle = player.getVehicleAttached()
            except Exception:
                vehicle = None
        if vehicle is None:
            try:
                vehicle = getattr(player, 'vehicle', None)
            except Exception:
                vehicle = None
        return vehicle
    except Exception:
        pass

    return None


def _hasArenaVehicleAttached(player):
    return _getArenaVehicle(player) is not None


def _vehicleLooksBattleReady(vehicle):
    if vehicle is None:
        return False
    for name in ('isStarted', 'isAlive'):
        try:
            attr = getattr(vehicle, name, None)
            if callable(attr):
                if attr() is False:
                    return False
            elif attr is False:
                return False
        except Exception:
            pass
    try:
        health = getattr(vehicle, 'health', None)
        if health is not None and int(health) <= 0:
            return False
    except Exception:
        pass
    return True


def _hasBattleInputActive(player):
    try:
        inputHandler = getattr(player, 'inputHandler', None)
    except Exception:
        inputHandler = None
    if inputHandler is None:
        return False

    try:
        ctrl = getattr(inputHandler, 'ctrl', None)
    except Exception:
        ctrl = None
    if ctrl is None:
        return False

    for attr in ('curVehicleID', 'vehicleID', 'controlledVehicleID'):
        try:
            value = getattr(ctrl, attr, None)
            if value:
                return True
        except Exception:
            pass

    for method in ('getCameraType', 'getControlModeName', 'getModeName'):
        try:
            fn = getattr(ctrl, method, None)
            if callable(fn):
                value = fn()
                if value:
                    return True
        except Exception:
            pass

    try:
        camera = getattr(inputHandler, 'camera', None)
        if camera is not None and ctrl.__class__.__name__.lower() not in ('', 'none'):
            return True
    except Exception:
        pass
    return False


def _arenaGateState():
    """Return (ready, reason). Start from period 1 only after the battle scene exists."""
    try:
        player = BigWorld.player()
    except Exception:
        return (False, 'no_player')
    try:
        arena = getattr(player, 'arena', None)
    except Exception:
        arena = None
    if arena is None:
        return (False, 'no_arena')
    try:
        period = int(getattr(arena, 'period', -1))
    except Exception:
        period = -1
    if period < ARENA_SHOW_MIN_PERIOD:
        return (False, 'arena_period_%s' % period)
    if period >= 2:
        return (True, 'arena_period_%s' % period)

    vehicle = _getArenaVehicle(player)
    if vehicle is None:
        return (False, 'arena_period_1_no_vehicle')
    if not _vehicleLooksBattleReady(vehicle):
        return (False, 'arena_period_1_vehicle_not_ready')
    if not _hasBattleInputActive(player):
        return (False, 'arena_period_1_loading_screen')
    return (True, 'arena_period_1_battle_ready')

def _isArenaReadyToShow():
    global _last_arena_gate_log
    ready, reason = _arenaGateState()
    key = '%s:%s' % (ready, reason)
    if key != _last_arena_gate_log:
        _last_arena_gate_log = key
        try:
            _logger.info('Arena show gate v0.0.61: ready=%s reason=%s', ready, reason)
        except Exception:
            pass
    return ready


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
        self.__alliesIcons = []
        self.__enemiesIcons = []
        self.__visible = False
        self.__scale = 1.0

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
            'alliesIcons': self.__alliesIcons,
            'enemiesIcons': self.__enemiesIcons
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

    def updateIcons(self, alliesIcons, enemiesIcons):
        self.__alliesIcons = alliesIcons or []
        self.__enemiesIcons = enemiesIcons or []
        self.__visible = True
        self.__push()

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
        if not _isArenaReadyToShow():
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
        if not _isArenaReadyToShow():
            if self.view is not None:
                try:
                    self.view.hide()
                except Exception:
                    pass
            return
        self.loadWindow()
        if self.view is not None:
            try:
                self.view.updateHealth(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP)
            except Exception:
                _logger.exception('updateTeamHealth failed')

    def updateDeadVehicles(self, aliveAllies, deadAllies, aliveEnemies, deadEnemies):
        # Battle Observer default scoreboard logic: left score = dead enemies, right score = dead allies.
        if not _isArenaReadyToShow():
            if self.view is not None:
                try:
                    self.view.hide()
                except Exception:
                    pass
            return
        self.loadWindow()
        if self.view is not None:
            try:
                self.view.updateScore(len(deadEnemies), len(deadAllies))
            except Exception:
                _logger.exception('updateDeadVehicles failed')


_listener = None
_orig_setViewComponents = None
_orig_stopControl = None
_orig_updateVehiclesHealth = None
_orig_updateDeadVehicles = None
_current_ctrl = None
_poll_callback = None
_orig_frag_updateTeamHealth = None
_orig_frag_populate = None
_orig_frag_initializeSettings = None
_orig_frag_onSettingsChanged = None


def _readTeamHealth(ctrl):
    try:
        alliesHP = getattr(ctrl, '_BattleFieldCtrl__alliesHealth', 0)
        enemiesHP = getattr(ctrl, '_BattleFieldCtrl__enemiesHealth', 0)
        totalAlliesHP = getattr(ctrl, '_BattleFieldCtrl__totalAlliesHealth', 0)
        totalEnemiesHP = getattr(ctrl, '_BattleFieldCtrl__totalEnemiesHealth', 0)
        return (_safe_int(alliesHP), _safe_int(enemiesHP), _safe_int(totalAlliesHP), _safe_int(totalEnemiesHP))
    except Exception:
        _logger.exception('Failed to read team health from BattleFieldCtrl')
        return (0, 0, 0, 0)


def _readScore(ctrl):
    try:
        deadAllies = getattr(ctrl, '_BattleFieldCtrl__deadAllies', set())
        deadEnemies = getattr(ctrl, '_BattleFieldCtrl__deadEnemies', set())
        return (len(deadEnemies), len(deadAllies))
    except Exception:
        _logger.exception('Failed to read score from BattleFieldCtrl')
        return (0, 0)



def _vehicleClassKey(vInfoVO):
    try:
        className = vInfoVO.vehicleType.getClassName()
    except Exception:
        try:
            className = vInfoVO.vehicleType.classTag
        except Exception:
            className = None
    className = (className or 'unknown').lower().replace('-', '').replace('_', '')
    if 'light' in className:
        return 'light'
    if 'medium' in className:
        return 'medium'
    if 'heavy' in className:
        return 'heavy'
    if 'spg' in className and ('at' in className or 'tankdestroyer' in className):
        return 'atspg'
    if 'atspg' in className or 'td' == className or 'tankdestroyer' in className:
        return 'atspg'
    if 'spg' in className:
        return 'spg'
    return 'unknown'


def _iconName(isEnemy, isAlive, classKey):
    team = 'enemy' if isEnemy else 'ally'
    state = 'alive' if isAlive else 'dead'
    classKey = classKey or 'unknown'
    return '%s_%s_%s' % (state, team, classKey)


def _readTeamIcons(ctrl):
    allies = []
    enemies = []
    classOrder = {'heavy': 0, 'medium': 1, 'atspg': 2, 'light': 3, 'spg': 4, 'unknown': 5}
    try:
        battleCtx = getattr(ctrl, '_BattleFieldCtrl__battleCtx', None)
        if battleCtx is None:
            return ([], [])
        arenaDP = battleCtx.getArenaDP()
        collection = vos_collections.VehiclesInfoCollection()
        for vInfoVO in collection.iterator(arenaDP):
            try:
                if vInfoVO.vehicleType.isObserver:
                    continue
            except Exception:
                pass
            try:
                isEnemy = arenaDP.isEnemyTeam(vInfoVO.team)
            except Exception:
                isEnemy = False
            try:
                isAlive = bool(vInfoVO.isAlive())
            except Exception:
                vid = getattr(vInfoVO, 'vehicleID', None)
                if isEnemy:
                    isAlive = vid not in getattr(ctrl, '_BattleFieldCtrl__deadEnemies', set())
                else:
                    isAlive = vid not in getattr(ctrl, '_BattleFieldCtrl__deadAllies', set())
            classKey = _vehicleClassKey(vInfoVO)
            icon = _iconName(isEnemy, isAlive, classKey)
            try:
                level = int(getattr(vInfoVO.vehicleType, 'level', 0) or 0)
            except Exception:
                level = 0
            sortKey = (0 if isAlive else 1, classOrder.get(classKey, 5), -level, getattr(vInfoVO.vehicleType, 'shortName', ''))
            if isEnemy:
                enemies.append((sortKey, icon))
            else:
                allies.append((sortKey, icon))
        allies.sort(key=lambda x: x[0])
        enemies.sort(key=lambda x: x[0])
        return ([x[1] for x in allies[:15]], [x[1] for x in enemies[:15]])
    except Exception:
        _logger.exception('Failed to read team icons from BattleFieldCtrl')
    return ([], [])


def _forcePushTeamHealth(ctrl):
    try:
        if not _isArenaReadyToShow():
            try:
                if _listener is not None and _listener.view is not None:
                    _listener.view.hide()
            except Exception:
                pass
            return
        listener = _getListener()
        listener.loadWindow()
        if listener.view is not None:
            alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP = _readTeamHealth(ctrl)
            listener.view.updateHealth(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP)
    except Exception:
        _logger.exception('Forced team health push failed')


def _forcePushScore(ctrl):
    try:
        if not _isArenaReadyToShow():
            try:
                if _listener is not None and _listener.view is not None:
                    _listener.view.hide()
            except Exception:
                pass
            return
        listener = _getListener()
        listener.loadWindow()
        if listener.view is not None:
            alliesFrags, enemiesFrags = _readScore(ctrl)
            listener.view.updateScore(alliesFrags, enemiesFrags)
    except Exception:
        _logger.exception('Forced score push failed')


def _forcePushIcons(ctrl):
    try:
        if not _isArenaReadyToShow():
            try:
                if _listener is not None and _listener.view is not None:
                    _listener.view.hide()
            except Exception:
                pass
            return
        listener = _getListener()
        listener.loadWindow()
        if listener.view is not None:
            alliesIcons, enemiesIcons = _readTeamIcons(ctrl)
            listener.view.updateIcons(alliesIcons, enemiesIcons)
    except Exception:
        _logger.exception('Forced icons push failed')



def _pollTick():
    global _poll_callback
    _poll_callback = None
    try:
        if _current_ctrl is not None:
            _forcePushTeamHealth(_current_ctrl)
            _forcePushScore(_current_ctrl)
            _forcePushIcons(_current_ctrl)
    except Exception:
        _logger.exception('Polling update failed')
    _schedulePoll()


def _schedulePoll():
    global _poll_callback
    try:
        if _poll_callback is None and _current_ctrl is not None:
            _poll_callback = BigWorld.callback(POLL_INTERVAL, _pollTick)
    except Exception:
        _logger.exception('Failed to schedule polling')


def _stopPoll():
    global _poll_callback
    try:
        if _poll_callback is not None:
            BigWorld.cancelCallback(_poll_callback)
    except Exception:
        pass
    _poll_callback = None

def _getListener():
    global _listener
    if _listener is None:
        _listener = CustomHPBarBattleListener()
    return _listener




def _componentDebugName(component):
    try:
        return '%s.%s' % (component.__class__.__module__, component.__class__.__name__)
    except Exception:
        return repr(component)


def _isStockTeamHPComponent(component):
    try:
        if component is _listener:
            return False
        cls_name = component.__class__.__name__.lower()
        mod_name = component.__class__.__module__.lower()
        full = mod_name + '.' + cls_name
        keywords = (
            'teamhealth', 'teamshealth', 'team_health', 'teamhp',
            'teams_hp', 'totalhealth', 'teampanelhealth', 'teambar'
        )
        if any(k in full for k in keywords):
            return True
        if hasattr(component, 'updateTeamHealth') and hasattr(component, 'updateDeadVehicles'):
            # Secondary heuristic: listeners whose naming contains battle page/ui/health.
            broad = ('health', 'battlepage', 'battlege', 'uibattle', 'team')
            if any(k in full for k in broad):
                return True
    except Exception:
        _logger.exception('Failed to inspect view component')
    return False


def _tryHideStockTeamHPComponent(component):
    dbg = _componentDebugName(component)
    try:
        if hasattr(component, 'as_setVisible'):
            try:
                component.as_setVisible(False)
                _logger.info('Hid stock HP component via as_setVisible: %s', dbg)
                return True
            except Exception:
                pass
        if hasattr(component, 'setVisible'):
            try:
                component.setVisible(False)
                _logger.info('Hid stock HP component via setVisible: %s', dbg)
                return True
            except Exception:
                pass
        if hasattr(component, 'as_setPosition'):
            try:
                component.as_setPosition(-5000, -5000)
                _logger.info('Moved stock HP component offscreen via as_setPosition: %s', dbg)
                return True
            except Exception:
                pass
        if hasattr(component, 'setPosition'):
            try:
                component.setPosition(-5000, -5000)
                _logger.info('Moved stock HP component offscreen via setPosition: %s', dbg)
                return True
            except Exception:
                pass
        flash = getattr(component, 'flashObject', None)
        if flash is not None:
            for method_name in ('as_setVisible', 'setVisible', 'as_setPosition', 'setPosition'):
                if hasattr(flash, method_name):
                    try:
                        method = getattr(flash, method_name)
                        if 'Visible' in method_name:
                            method(False)
                        else:
                            method(-5000, -5000)
                        _logger.info('Hid stock HP component via flashObject.%s: %s', method_name, dbg)
                        return True
                    except Exception:
                        pass
    except Exception:
        _logger.exception('Failed to hide stock HP component: %s', dbg)
    return False




def _patched_setViewComponents(self, *components):
    global _current_ctrl
    _current_ctrl = self
    listener = _getListener()
    try:
        _logger.info('BattleFieldCtrl.setViewComponents received %d components', len(components))
        for component in components:
            _logger.info('Original view component: %s', _componentDebugName(component))
    except Exception:
        pass

    if HIDE_STOCK_TEAM_HP and FORCE_ONLY_CUSTOM_LISTENER:
        # Aggressive test mode: only our listener receives BattleFieldCtrl team HP/dead updates.
        # This is used to verify whether the WG stock top HP bar is fed through BattleFieldCtrl.
        result = _orig_setViewComponents(self, listener)
        try:
            _logger.info('FORCE_ONLY_CUSTOM_LISTENER enabled; stock BattleFieldCtrl listeners suppressed')
        except Exception:
            pass
    else:
        filtered = []
        hidden = []
        for component in components:
            try:
                dbg = _componentDebugName(component)
                _logger.info('View component: %s', dbg)
            except Exception:
                dbg = 'unknown'
            if HIDE_STOCK_TEAM_HP and _isStockTeamHPComponent(component):
                hidden.append(dbg)
                try:
                    _tryHideStockTeamHPComponent(component)
                except Exception:
                    pass
                continue
            filtered.append(component)
        if listener not in filtered:
            filtered.append(listener)
        result = _orig_setViewComponents(self, *tuple(filtered))
        if hidden:
            try:
                _logger.info('Suppressed stock HP components: %s', ', '.join(hidden))
            except Exception:
                pass

    _logger.info('BattleFieldCtrl.setViewComponents gate check v0.0.61: %s', _arenaGateState())
    _forcePushTeamHealth(self)
    _forcePushScore(self)
    _forcePushIcons(self)
    _schedulePoll()
    return result


def _patched_stopControl(self):
    global _listener, _current_ctrl
    _stopPoll()
    _current_ctrl = None
    try:
        if _listener is not None:
            _listener.destroy()
            _listener = None
    except Exception:
        _logger.exception('Failed to destroy listener')
    return _orig_stopControl(self)


def _patched_updateVehiclesHealth(self):
    # If HIDE_STOCK_TEAM_HP is enabled, do not forward the team HP update to WG's stock
    # view components. We still read BattleFieldCtrl private values and push our own payload.
    result = None
    try:
        if not HIDE_STOCK_TEAM_HP and _orig_updateVehiclesHealth is not None:
            result = _orig_updateVehiclesHealth(self)
    finally:
        _forcePushTeamHealth(self)
        _forcePushIcons(self)
        _schedulePoll()
    return result


def _patched_updateDeadVehicles(self):
    result = None
    try:
        if _orig_updateDeadVehicles is not None:
            result = _orig_updateDeadVehicles(self)
    finally:
        _forcePushScore(self)
        _forcePushIcons(self)
        _schedulePoll()
    return result



_frag_instances = []
_frag_hide_callback = None
_frag_hide_ticks_left = 0


def _tryFlashCall(obj, method_name, *args):
    try:
        if obj is not None and hasattr(obj, method_name):
            getattr(obj, method_name)(*args)
            return True
    except Exception:
        pass
    return False


def _hideFlashObject(obj):
    if obj is None:
        return
    # Scaleform MovieClip-like properties.
    for attr, value in (('_visible', False), ('visible', False), ('_alpha', 0), ('alpha', 0), ('_x', -5000), ('x', -5000), ('_y', -5000), ('y', -5000)):
        try:
            setattr(obj, attr, value)
        except Exception:
            pass
    _tryFlashCall(obj, 'as_setVisible', False)
    _tryFlashCall(obj, 'setVisible', False)
    _tryFlashCall(obj, 'as_setAlpha', 0)
    _tryFlashCall(obj, 'setAlpha', 0)
    _tryFlashCall(obj, 'as_setPosition', -5000, -5000)
    _tryFlashCall(obj, 'setPosition', -5000, -5000)
    _tryFlashCall(obj, 'gotoAndStop', 0)


def _keepFragCorrelationVehicleIconsOnly(instance):
    """Hide WG FragCorrelationBar completely; custom Gameface draws HP, score and icons."""
    try:
        if instance is None:
            return
        if instance not in _frag_instances:
            _frag_instances.append(instance)
        # Flags from _FragBarViewState:
        # 1 HP values, 2 HP difference, 4 tier grouping, 8 vehicle counter, 16 HP bar.
        # Mask 0 alone does not remove the advantage chevron on some clients,
        # so also hide/move the Scaleform component itself.
        mask = 0
        try:
            setattr(instance, '_FragCorrelationBar__viewSettings', mask)
        except Exception:
            pass
        try:
            instance.as_updateViewSettingS(mask)
        except Exception:
            pass
        try:
            _hideFlashObject(instance)
        except Exception:
            pass
        try:
            flash = getattr(instance, 'flashObject', None)
            _hideFlashObject(flash)
        except Exception:
            pass
    except Exception:
        _logger.exception('Failed to hide FragCorrelationBar')


def _hideFragTick():
    global _frag_hide_callback, _frag_hide_ticks_left
    _frag_hide_callback = None
    try:
        for inst in list(_frag_instances):
            _keepFragCorrelationVehicleIconsOnly(inst)
    except Exception:
        _logger.exception('FragCorrelationBar repeated hide failed')
    _frag_hide_ticks_left -= 1
    if _frag_hide_ticks_left > 0:
        try:
            _frag_hide_callback = BigWorld.callback(0.10, _hideFragTick)
        except Exception:
            pass


def _scheduleFragHideRepeater():
    global _frag_hide_callback, _frag_hide_ticks_left
    _frag_hide_ticks_left = 50
    if _frag_hide_callback is None:
        try:
            _frag_hide_callback = BigWorld.callback(0.05, _hideFragTick)
        except Exception:
            pass


def _patched_frag_updateTeamHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
    # Do not call original as_updateHPS: this removes stock HP bars, 0 leftovers and advantage animation.
    # Do not call original as_updateHPS and keep stock FragCorrelationBar hidden.
    _keepFragCorrelationVehicleIconsOnly(self)
    _scheduleFragHideRepeater()
    return None


def _patched_frag_populate(self):
    result = None
    try:
        if _orig_frag_populate is not None:
            result = _orig_frag_populate(self)
    finally:
        _keepFragCorrelationVehicleIconsOnly(self)
        _scheduleFragHideRepeater()
    return result


def _patched_frag_initializeSettings(self):
    _keepFragCorrelationVehicleIconsOnly(self)
    _scheduleFragHideRepeater()
    return None


def _patched_frag_onSettingsChanged(self, diff):
    _keepFragCorrelationVehicleIconsOnly(self)
    _scheduleFragHideRepeater()
    return None


def _installFragCorrelationHook():
    global _orig_frag_updateTeamHealth, _orig_frag_populate, _orig_frag_initializeSettings, _orig_frag_onSettingsChanged
    try:
        cls = frag_correlation_bar.FragCorrelationBar
        if _orig_frag_updateTeamHealth is not None:
            return
        _orig_frag_updateTeamHealth = cls.updateTeamHealth
        _orig_frag_populate = getattr(cls, '_populate', None)
        _orig_frag_initializeSettings = getattr(cls, '_FragCorrelationBar__initializeSettings', None)
        _orig_frag_onSettingsChanged = getattr(cls, '_FragCorrelationBar__onSettingsChanged', None)

        cls.updateTeamHealth = _patched_frag_updateTeamHealth
        if _orig_frag_populate is not None:
            cls._populate = _patched_frag_populate
        if _orig_frag_initializeSettings is not None:
            setattr(cls, '_FragCorrelationBar__initializeSettings', _patched_frag_initializeSettings)
        if _orig_frag_onSettingsChanged is not None:
            setattr(cls, '_FragCorrelationBar__onSettingsChanged', _patched_frag_onSettingsChanged)

        print '[CustomHPBarGF] FragCorrelationBar hooks installed v0.0.61'
        _logger.info('FragCorrelationBar hooks installed v0.0.61')
    except Exception:
        _logger.exception('Failed to install FragCorrelationBar hook')


def _installHook():
    global _orig_setViewComponents, _orig_stopControl, _orig_updateVehiclesHealth, _orig_updateDeadVehicles
    if _orig_setViewComponents is not None:
        return
    _orig_setViewComponents = battle_field_ctrl.BattleFieldCtrl.setViewComponents
    _orig_stopControl = battle_field_ctrl.BattleFieldCtrl.stopControl
    _orig_updateVehiclesHealth = getattr(battle_field_ctrl.BattleFieldCtrl, '_BattleFieldCtrl__updateVehiclesHealth', None)
    _orig_updateDeadVehicles = getattr(battle_field_ctrl.BattleFieldCtrl, '_BattleFieldCtrl__updateDeadVehicles', None)

    battle_field_ctrl.BattleFieldCtrl.setViewComponents = _patched_setViewComponents
    battle_field_ctrl.BattleFieldCtrl.stopControl = _patched_stopControl

    if _orig_updateVehiclesHealth is not None:
        setattr(battle_field_ctrl.BattleFieldCtrl, '_BattleFieldCtrl__updateVehiclesHealth', _patched_updateVehiclesHealth)
    else:
        _logger.warning('BattleFieldCtrl.__updateVehiclesHealth not found; using listener callbacks only')

    if _orig_updateDeadVehicles is not None:
        setattr(battle_field_ctrl.BattleFieldCtrl, '_BattleFieldCtrl__updateDeadVehicles', _patched_updateDeadVehicles)
    else:
        _logger.warning('BattleFieldCtrl.__updateDeadVehicles not found; using listener callbacks only')

    print '[CustomHPBarGF] BattleFieldCtrl hooks installed v0.0.61'
    _logger.info('BattleFieldCtrl hooks installed v0.0.61')


_installFragCorrelationHook()
_installHook()
