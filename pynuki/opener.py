# coding: utf-8

from . import constants as const
from .device import NukiDevice
from .utils import logger


class NukiOpener(NukiDevice):
    def activate_rto(self, block=False):
        return self._bridge.lock_action(
            nuki_id=self.nuki_id,
            action=const.ACTION_OPENER_ACTIVATE_RTO,
            block=block,
        )

    def deactivate_rto(self, block=False):
        return self._bridge.lock_action(
            nuki_id=self.nuki_id,
            action=const.ACTION_OPENER_DEACTIVATE_RTO,
            block=block,
        )

    def electric_strike_actuation(self, block=False):
        return self._bridge.lock_action(
            nuki_id=self.nuki_id,
            action=const.ACTION_OPENER_ELECTRIC_STRIKE_ACTUATION,
            block=block,
        )

    def activate_continuous_mode(self, block=False):
        return self._bridge.lock_action(
            nuki_id=self.nuki_id,
            action=const.ACTION_OPENER_ACTIVATE_CONTINUOUS,
            block=block,
        )

    def deactivate_continuous_mode(self, block=False):
        return self._bridge.lock_action(
            nuki_id=self.nuki_id,
            action=const.ACTION_OPENER_DEACTIVATE_CONTINUOUS,
            block=block,
        )
