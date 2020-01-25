#!/usr/bin/python
# coding: utf-8

"""
Based on the Bridge API version 1.10

Documentation:
https://developer.nuki.io/t/bridge-http-api/26
https://developer.nuki.io/uploads/short-url/a8eIacr0ku9zogOyuIuSEyw1PcA.pdf
"""

from datetime import datetime
from random import randint
import hashlib
import logging

import requests


logger = logging.getLogger(__name__)


# Default values
REQUESTS_TIMEOUT = 5

# Constants
ACTION_LOCK_UNLOCK = 1
ACTION_LOCK_LOCK = 2
ACTION_LOCK_UNLATCH = 3
ACTION_LOCK_LOCK_N_GO = 4
ACTION_LOCK_LOCK_N_GO_WITH_UNLATCH = 5

ACTION_OPENER_ACTIVATE_RTO = 1
ACTION_OPENER_DEACTIVATE_RTO = 2
ACTION_OPENER_ELECTRIC_STRIKE_ACTUATION = 3
ACTION_OPENER_ACTIVATE_CONTINUOUS = 4
ACTION_OPENER_DEACTIVATE_CONTINUOUS = 5

BRIDGE_TYPE_HW = 1
BRIDGE_TYPE_SW = 2

DEVICE_TYPE_LOCK = 0
DEVICE_TYPE_OPENER = 2

MODE_LOCK_DOOR = 2
MODE_OPENER_DOOR = 2
MODE_OPENER_CONTINUOUS = 3

STATE_OPENER_UNTRAINED = 0
STATE_OPENER_ONLINE = 1
STATE_OPENER_RTO_ACTIVE = 3
STATE_OPENER_OPENER_OPEN = 5

STATE_LOCK_UNCALIBRATED = 0
STATE_LOCK_LOCKED = 1
STATE_LOCK_UNLOCKING = 2
STATE_LOCK_UNLOCKED = 3
STATE_LOCK_LOCKING = 4
STATE_LOCK_UNLATCHED = 5
STATE_LOCK_UNLOCKED_LOCK_N_GO = 6
STATE_LOCK_UNLATCHING = 7
STATE_LOCK_MOTOR_BLOCKED = 254
STATE_LOCK_UNDEFINED = 255


def __sha256sum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_token(token):
    rnr = randint(0, 65535)
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    hash_256 = __sha256sum(f"{ts},{rnr},{token}")
    return {"ts": ts, "rnr": rnr, "hash": hash_256}


class InvalidCredentialsException(Exception):
    pass


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
        return self.state == STATE_LOCK_LOCKED

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


class NukiBridge(object):
    def __init__(
        self,
        hostname,
        token=None,
        port=8080,
        secure=True,
        timeout=REQUESTS_TIMEOUT,
    ):
        self.hostname = hostname
        self.port = port
        self.__api_url = f"http://{hostname}:{port}"
        self.secure = secure
        self.requests_timeout = timeout
        self._json = None
        self.token = token

    def __repr__(self):
        return f"<NukiBridge: {self.hostname}:{self.port} (token={self.token})>"

    @staticmethod
    def discover():
        res = requests.get("https://api.nuki.io/discover/bridges")
        data = res.json()
        logger.debug(f"Discovery returned {data}")
        error_code = data.get("errorCode", -9999)
        if error_code != 0:
            logger.error(f"Discovery failed with error code {error_code}")
        bridges = data.get("bridges")
        if not bridges:
            logger.warning("No bridge discovered.")
        else:
            return [
                NukiBridge(hostname=x.get("ip"), port=x.get("port"))
                for x in bridges
            ]

    @property
    def token(self):
        return self.__token

    @token.setter
    def token(self, token):
        self.__token = token
        # Try to log in if token has been set
        if self.token:
            try:
                self.info()
                logger.info("Login succeeded.")
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 401:
                    logger.error("Could not login with provided credentials")
                    raise InvalidCredentialsException(
                        "Login error. Provided token is invalid."
                    )

    def __rq(self, endpoint, params=None):
        url = f"{self.__api_url}/{endpoint}"
        if self.secure:
            get_params = hash_token(self.token)
        else:
            get_params = {"token": self.token}
        if params:
            get_params.update(params)
        # Convert list to string to prevent request from encoding the url params
        # https://stackoverflow.com/a/23497912
        get_params_str = "&".join(f"{k}={v}" for k, v in get_params.items())
        result = requests.get(
            url, params=get_params_str, timeout=self.requests_timeout
        )
        result.raise_for_status()
        data = result.json()
        if "success" in data:
            if not data.get("success"):
                logger.warning(f"Call failed: {result}")
        return data

    def auth(self):
        url = f"{self.__api_url}/{auth}"
        result = requests.get(url, timeout=self.requests_timeout)
        result.raise_for_status()
        data = result.json()
        if not data.get("success", False):
            logging.warning(
                "Failed to authenticate against bridge. Have you pressed the button?"
            )
        return data

    def config_auth(self, enable):
        return self.__rq("configAuth", {"enable": 1 if enable else 0})

    def list(self):
        return self.__rq("list")

    def lock_state(self, nuki_id, device_type=DEVICE_TYPE_LOCK):
        return self.__rq(
            "lockState", {"nukiId": nuki_id, "deviceType": device_type}
        )

    def lock_action(
        self, nuki_id, action, device_type=DEVICE_TYPE_LOCK, block=False
    ):
        params = {
            "nukiId": nuki_id,
            "deviceType": device_type,
            "action": action,
            "noWait": 0 if block else 1,
        }
        return self.__rq("lockAction", params)

    def unpair(self, nuki_id, device_type=DEVICE_TYPE_LOCK):
        return self.__rq(
            "unpair", {"nukiId": nuki_id, "deviceType": device_type}
        )

    def info(self, bridge_type=BRIDGE_TYPE_HW):
        data = self.__rq("info", {"bridgeType": bridge_type})
        self._json = data
        return data

    # Callback endpoints

    def callback_add(self, callback_url):
        return self.__rq("callback/add", {"url": callback_url})

    def callback_list(self):
        return self.__rq("callback/list")

    def callback_remove(self, callback_id):
        return self.__rq("callback/remove", {"id": callback_id})

    # Maintainance endpoints

    def log(self, offset=0, count=100):
        return self.__rq("log", {"offset": offset, "count": count})

    def clear_log(self):
        return self.__rq("clearlog")

    def firmware_update(self):
        return self.__rq("fwupdate")

    def reboot(self):
        return self.__rq("reboot")

    def factory_reset(self):
        return self.__rq("factoryReset")

    # Shorthand methods

    @property
    def locks(self):
        locks = []
        for l in self.list():
            # lock_data holds the name and nuki id of the lock
            # eg: {'name': 'Home', 'nukiId': 241563832}
            lock_data = {
                k: v for k, v in l.items() if k not in ["lastKnownState"]
            }
            # state_data holds the last known state of the lock
            # eg: {'batteryCritical': False, 'state': 1, 'stateName': 'locked'}
            state_data = {
                k: v
                for k, v in l["lastKnownState"].items()
                if k not in ["timestamp"]
            }

            # Merge lock_data and state_data
            # data = {**lock_data, **state_data}  # Python 3.5+
            data = lock_data.copy()
            data.update(state_data)

            locks.append(NukiLock(self, data))
        return locks

    def lock(self, nuki_id, block=False):
        return self.lock_action(nuki_id, action=ACTION_LOCK_LOCK, block=block)

    def unlock(self, nuki_id, block=False):
        return self.lock_action(nuki_id, action=ACTION_LOCK_UNLOCK, block=block)

    def lock_n_go(self, nuki_id, unlatch=False, block=False):
        action = ACTION_LOCK_LOCK_N_GO
        if unlatch:
            action = ACTION_LOCK_LOCK_N_GO_WITH_UNLATCH
        return self.lock_action(nuki_id, action=action, block=block)

    def unlatch(self, nuki_id, block=False):
        return self.lock_action(
            nuki_id, action=ACTION_LOCK_UNLATCH, block=block
        )

    def simple_lock(self, nuki_id, device_type=DEVICE_TYPE_LOCK):
        return self.__rq("lock", {"nukiId": nuki_id, "deviceType": device_type})

    def simple_unlock(self, nuki_id, device_type=DEVICE_TYPE_LOCK):
        return self.__rq(
            "unlock", {"nukiId": nuki_id, "deviceType": device_type}
        )
