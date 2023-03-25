#!/usr/bin/python
# coding: utf-8

"""
Based on the Bridge API version 1.13.2

Documentation:
https://developer.nuki.io/t/bridge-http-api/26
https://developer.nuki.io/uploads/short-url/a8eIacr0ku9zogOyuIuSEyw1PcA.pdf
"""

import logging

import requests

from . import constants as const
from .device import NukiDevice
from .lock import NukiLock
from .opener import NukiOpener
from .utils import encrypt_token, logger, sha256sum

# Default values
REQUESTS_TIMEOUT = 5


class InvalidCredentialsException(Exception):
    pass


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

    @property
    def tokendigest(self):
        return self.__tokendigest

    @token.setter
    def token(self, token):
        self.__token = token
        self.__tokendigest = sha256sum(token) if token else None
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

    @property
    def is_hardware_bridge(self):
        info = self.info()
        return info.get("bridgeType") == const.BRIDGE_TYPE_HW

    def __rq(self, endpoint, params=None):
        url = f"{self.__api_url}/{endpoint}"
        if self.secure:
            get_params = encrypt_token(self.tokendigest)
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
        url = f"{self.__api_url}/auth"
        result = requests.get(url, timeout=self.requests_timeout)
        result.raise_for_status()
        data = result.json()
        if not data.get("success", False):
            logging.warning(
                "Failed to authenticate against bridge. "
                "Have you pressed the button?"
            )
        return data

    def config_auth(self, enable):
        return self.__rq("configAuth", {"enable": 1 if enable else 0})

    def list(self, device_type=None):
        data = self.__rq("list")
        if device_type is not None:
            return [x for x in data if x.get("deviceType") == device_type]
        return data

    def lock_state(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK):
        return self.__rq(
            "lockState", {"nukiId": nuki_id, "deviceType": device_type}
        )

    def lock_action(
        self, nuki_id, action, device_type=const.DEVICE_TYPE_LOCK, block=False
    ):
        params = {
            "nukiId": nuki_id,
            "deviceType": device_type,
            "action": action,
            "noWait": 0 if block else 1,
        }
        return self.__rq("lockAction", params)

    def unpair(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK):
        return self.__rq(
            "unpair", {"nukiId": nuki_id, "deviceType": device_type}
        )

    def info(self):
        # Return cached value
        if self._json:
            return self._json
        data = self.__rq("info")
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

    def update(self):
        # Invalidate cache
        self._json = None
        return self.info()

    def _get_devices(self, device_type=None):
        devices = []
        for dev in self.list(device_type=device_type):
            # lock_data holds the name and nuki id of the lock
            # eg: {'name': 'Home', 'nukiId': 241563832}
            device_data = {
                k: v for k, v in dev.items() if k not in ["lastKnownState"]
            }
            # state_data holds the last known state of the lock
            # eg: {'batteryCritical': False, 'state': 1, 'stateName': 'locked'}
            try:
                state_data = {
                    k: v
                    for k, v in dev["lastKnownState"].items()
                    if k not in ["timestamp"]
                }
            except KeyError:
                state_data = {}

            # Merge lock_data and state_data
            data = {**device_data, **state_data}

            dev_type = device_data.get("deviceType")
            if dev_type == const.DEVICE_TYPE_LOCK:
                dev = NukiLock(self, data)
            elif dev_type == const.DEVICE_TYPE_SMARTDOOR:
                dev = NukiLock(self, data)
            elif dev_type == const.DEVICE_TYPE_SMARTLOCK3:
                dev = NukiLock(self, data)
            elif dev_type == const.DEVICE_TYPE_OPENER:
                dev = NukiOpener(self, data)
            else:
                logger.warning(f"Unknown device type: {dev_type}")
                dev = NukiDevice(self, data)

            devices.append(dev)
        return devices

    @property
    def devices(self):
        return self._get_devices()

    @property
    def locks(self):
        locks = []
        for device in self._get_devices():
            if isinstance(device, NukiLock):
                locks.append(device)
        return locks

    @property
    def openers(self):
        return self._get_devices(device_type=const.DEVICE_TYPE_OPENER)

    def lock(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK, block=False):
        return self.lock_action(
            nuki_id,
            action=const.ACTION_LOCK_LOCK,
            device_type=device_type,
            block=block,
        )

    def unlock(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK, block=False):
        return self.lock_action(
            nuki_id,
            action=const.ACTION_LOCK_UNLOCK,
            device_type=device_type,
            block=block,
        )

    def lock_n_go(
        self,
        nuki_id,
        device_type=const.DEVICE_TYPE_LOCK,
        unlatch=False,
        block=False,
    ):
        action = const.ACTION_LOCK_LOCK_N_GO
        if unlatch:
            action = const.ACTION_LOCK_LOCK_N_GO_WITH_UNLATCH
        return self.lock_action(
            nuki_id,
            action=action,
            device_type=device_type,
            block=block,
        )

    def unlatch(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK, block=False):
        return self.lock_action(
            nuki_id,
            action=const.ACTION_LOCK_UNLATCH,
            device_type=device_type,
            block=block,
        )

    def simple_lock(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK):
        return self.__rq("lock", {"nukiId": nuki_id, "deviceType": device_type})

    def simple_unlock(self, nuki_id, device_type=const.DEVICE_TYPE_LOCK):
        return self.__rq(
            "unlock", {"nukiId": nuki_id, "deviceType": device_type}
        )
