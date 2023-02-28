# coding: utf-8

from . import constants as const
from .exceptions import NukiUpdateException
from .utils import logger


class NukiDevice(object):
    def __init__(self, bridge, json):
        self._bridge = bridge
        self._json = json

    @property
    def name(self):
        return self._json.get("name")

    @property
    def nuki_id(self):
        return self._json.get("nukiId")

    @property
    def battery_critical(self):
        return self._json.get("batteryCritical")

    @property
    def firmware_version(self):
        return self._json.get("firmwareVersion")

    @property
    def state(self):
        return self._json.get("state")

    @property
    def state_name(self):
        return self._json.get("stateName")

    @property
    def device_type(self):
        return self._json.get("deviceType")

    @property
    def device_type_str(self):
        dev = self.device_type
        if dev == const.DEVICE_TYPE_LOCK:
            return "lock"
        elif dev == const.DEVICE_TYPE_OPENER:
            return "opener"
        logger.error(f"Unknown device type: {dev}")
        return "UNKNOWN"

    @property
    def device_model_str(self):
        dev = self.device_type
        if dev == const.DEVICE_TYPE_LOCK:
            return "Nuki Smart Lock 1.0/2.0"
        elif dev == const.DEVICE_TYPE_OPENER:
            return "Nuki Opener"
        elif dev == const.DEVICE_TYPE_SMARTDOOR:
            return "Nuki Smart Door"
        elif dev == const.DEVICE_TYPE_SMARTLOCK3:
            return "Nuki Smart Lock 3.0 (Pro)"
        logger.error(f"Unknown device type: {dev}")
        return "UNKNOWN"

    @property
    def mode(self):
        return self._json.get("mode")

    @property
    def mode_str(self):
        dev = self.device_type
        mode = self.mode
        if dev == const.DEVICE_TYPE_LOCK:
            if mode == const.MODE_LOCK_DOOR:
                return "door mode"
        elif dev == const.DEVICE_TYPE_OPENER:
            if mode == const.MODE_OPENER_DOOR:
                return "door mode"
            elif mode == const.MODE_OPENER_CONTINUOUS:
                return "continuous"
        logger.error(f'Unknown mode "{mode}" for device type {dev}')
        return "UNKNOWN"

    def update(self, aggressive=False):
        """
        Update the state of the Nuki device
        :param aggressive: Whether to aggressively poll the Bridge. If set to
        True, this will actively query the Lock, thus using more battery.
        :type aggressive: bool
        """
        if aggressive:
            data = self._bridge.lock_state(self.nuki_id)
            logger.debug(f"Received data: {data}")
            if not data.get("success", False):
                raise NukiUpdateException(
                    f"Failed to update data for Nuki device {self.nuki_id}"
                )
            self._json.update({k: v for k, v in data.items() if k != "success"})
        else:
            data = [
                dev
                for dev in self._bridge._get_devices(self.device_type)
                if dev.nuki_id == self.nuki_id
            ]
            assert data, (
                "Failed to update data for lock. "
                f"Nuki ID {self.nuki_id} volatized."
            )
            self._json.update(data[0]._json)

    def update_from_callback(self, json):
        """
        Update the state of the Nuki device from a callback
        :param json: Callback JSON body
        """
        assert (
            json.get("nukiId") == self.nuki_id
        ), "Failed to update data from callback. Wrong Nuki ID."
        self._json.update(json)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self._json}>"
