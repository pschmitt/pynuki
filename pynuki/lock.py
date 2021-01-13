# coding: utf-8

from . import constants as const
from .device import NukiDevice


class NukiLock(NukiDevice):
    @property
    def is_locked(self):
        return self.state == const.STATE_LOCK_LOCKED

    @property
    def is_door_sensor_activated(self):
        # Nuki v1 locks don't have a door sensor, therefore the
        # door_sensor_state will is unset for them.
        if (
            not self.door_sensor_state
            or self.door_sensor_state == const.STATE_DOORSENSOR_UNKNOWN
        ):
            return
        return self.door_sensor_state != const.STATE_DOORSENSOR_DEACTIVATED

    @property
    def door_sensor_state(self):
        return self._json.get("doorsensorState")

    @property
    def door_sensor_state_name(self):
        return self._json.get("doorsensorStateName")

    @property
    def battery_charge(self):
        return self._json.get("batteryChargeState")

    @property
    def battery_critical_keypad(self):
        return self._json.get("keypadBatteryCritical")

    def lock(self, block=False):
        return self._bridge.lock(nuki_id=self.nuki_id, block=block)

    def unlock(self, block=False):
        return self._bridge.unlock(nuki_id=self.nuki_id, block=block)

    def lock_n_go(self, unlatch=False, block=False):
        return self._bridge.lock_n_go(
            nuki_id=self.nuki_id, unlatch=unlatch, block=block
        )

    def unlatch(self, block=False):
        return self._bridge.unlatch(nuki_id=self.nuki_id, block=block)
