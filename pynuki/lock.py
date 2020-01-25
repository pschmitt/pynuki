# coding: utf-8

from . import constants as const
from .utils import logger


class NukiLock(object):
    def __init__(self, bridge, json):
        self._bridge = bridge
        self._json = json

    @property
    def name(self):
        return self._json.get("name", None)

    @property
    def nuki_id(self):
        return self._json.get("nukiId", None)

    @property
    def battery_critical(self):
        return self._json.get("batteryCritical", None)

    @property
    def state(self):
        return self._json.get("state", None)

    @property
    def state_name(self):
        return self._json.get("stateName", None)

    @property
    def is_locked(self):
        return self.state == const.STATE_LOCK_LOCKED

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

    def update(self, aggressive=False):
        """
        Update the state of the NukiLock
        :param aggressive: Whether to aggressively poll the Bridge. If set to
        True, this will actively query the Lock, thus using more battery.
        :type aggressive: bool
        """
        if aggressive:
            data = self._bridge.lock_state(self.nuki_id)
            if not data["success"]:
                logger.warning(
                    f"Failed to update the state of lock {self.nuki_id}"
                )
            self._json.update({k: v for k, v in data.items() if k != "success"})
        else:
            data = [l for l in self._bridge.locks if l.nuki_id == self.nuki_id]
            assert data, (
                "Failed to update data for lock. "
                f"Nuki ID {self.nuki_id} volatized."
            )
            self._json.update(data[0]._json)

    def __repr__(self):
        return f"<NukiLock: {self._json}>"
