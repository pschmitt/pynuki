# coding: utf-8

from . import constants as const
from .device import NukiDevice
from .utils import logger


class NukiLock(NukiDevice):
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
