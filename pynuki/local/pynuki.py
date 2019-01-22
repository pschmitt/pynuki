#!/usr/bin/python
# coding: utf-8

'''
Based on the Bridge API version 1.7

Documentation:
https://developer.nuki.io/page/nuki-bridge-http-api-170/4/
'''

import requests
import logging

from pynuki.const import LOCK_ACTIONS, LOCK_STATES


logger = logging.getLogger(__name__)


def discover_bridges():
    resp = requests.get('https://api.nuki.io/discover/bridges')
    return resp.json().get('bridges')


class NukiLock(object):
    def __init__(self, bridge, json):
        self._bridge = bridge
        self._json = json

    @property
    def name(self):
        return self._json.get('name', None)

    @property
    def nuki_id(self):
        return self._json.get('nukiId', None)

    @property
    def battery_critical(self):
        return self._json.get('batteryCritical', None)

    @property
    def state(self):
        return self._json.get('state', None)

    @property
    def state_name(self):
        return self._json.get('stateName', None)

    @property
    def is_locked(self):
        return self.state == LOCK_STATES['LOCKED']

    def lock(self, block=False):
        return self._bridge.lock(nuki_id=self.nuki_id, block=block)

    def unlock(self, block=False):
        return self._bridge.unlock(nuki_id=self.nuki_id, block=block)

    def lock_n_go(self, unlatch=False, block=False):
        return self._bridge.lock_n_go(
            nuki_id=self.nuki_id, unlatch=unlatch, block=block)

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
            if not data['success']:
                logger.warning(
                'Failed to update the state of lock {}'.format(self.nuki_id)
            )
            self._json.update({k: v for k, v in data.items() if k != 'success'})
        else:
            data = [l for l in self._bridge.locks if l.nuki_id == self.nuki_id]
            assert data, (
                   'Failed to update data for lock. '
                   'Nuki ID {} volatized.'.format(self.nuki_id))
            self._json.update(data[0]._json)

    def __repr__(self):
        return '<NukiLock: {}>'.format(self._json)


class NukiBridge(object):
    def __init__(self, hostname=None, token=None, port=8080):
        self.hostname = hostname
        self.token = token
        self.port = port
        if not hostname:
            discovery = discover_bridges()
            if discovery:
                self.hostname = discovery[0].get('ip')
        self.__api_url = 'http://{}:{}'.format(self.hostname, port)

    def __rq(self, endpoint, params=None):
        url = '{}/{}'.format(self.__api_url, endpoint)
        get_params = {'token': self.token}
        if params:
            get_params.update(params)
        result = requests.get(url, params=get_params)
        result.raise_for_status()
        return result.json()

    def list(self):
        return self.__rq('list')

    def auth(self):
        logger.info("Please press the button on the bridge to enable the API")
        return self.__rq('auth')

    def retrieve_token(self):
        auth = self.auth()
        if auth.get('success'):
            logger.info("Received token")
            self.token = auth.get('token')
        else:
            logger.warning("Failed to retrieve token")

    def config_auth(self, enable):
        return self.__rq('configAuth', {'enable': 1 if enable else 0})

    def lock_state(self, nuki_id):
        return self.__rq('lockState', {'nukiId': nuki_id})

    def lock_action(self, nuki_id, action, block=False):
        params = {
            'nukiId': nuki_id,
            'action': action,
            'noWait': 0 if block else 1
        }
        return self.__rq('lockAction', params)

    def unpair(self, nuki_id):
        return self.__rq('unpair', {'nukiId': nuki_id})

    def info(self):
        return self.__rq('info')

    # Callback endpoints

    def callback_add(self, callback_url):
        return self.__rq('callback/add', {'url': callback_url})

    def callback_list(self):
        return self.__rq('callback/list')

    def callback_remove(self, callback_url):
        return self.__rq('callback/remove', {'url': callback_url})

    # Maintainance endpoints

    def log(self, offset=0, count=100):
        return self.__rq('log', {'offset': offset, 'count': count})

    def clear_log(self):
        return self.__rq('clearlog')

    def firmware_update(self):
        return self.__rq('fwupdate')

    def reboot(self):
        return self.__rq('reboot')

    def factory_reset(self):
        return self.__rq('factoryReset')

    # Shorthand methods

    @property
    def locks(self):
        locks = []
        for l in self.list():
            # lock_data holds the name and nuki id of the lock
            # eg: {'name': 'Home', 'nukiId': 241563832}
            lock_data = {k: v for k, v in l.items() \
                         if k not in ['lastKnownState']}
            # state_data holds the last known state of the lock
            # eg: {'batteryCritical': False, 'state': 1, 'stateName': 'locked'}
            state_data = {k: v for k, v in l['lastKnownState'].items() \
                          if k not in ['timestamp']}

            # Merge lock_data and state_data
            # data = {**lock_data, **state_data}  # Python 3.5+
            data = lock_data.copy()
            data.update(state_data)

            locks.append(NukiLock(self, data))
        return locks

    def lock(self, nuki_id, block=False):
        return self.lock_action(
            nuki_id, action=LOCK_ACTIONS['LOCK'], block=block
        )

    def unlock(self, nuki_id, block=False):
        return self.lock_action(
            nuki_id, action=LOCK_ACTIONS['UNLOCK'], block=block
        )

    def lock_n_go(self, nuki_id, unlatch=False, block=False):
        action = LOCK_ACTIONS['LOCK_N_GO']
        if unlatch:
            action = LOCK_ACTIONS['LOCK_N_GO_WITH_UNLATCH']
        return self.lock_action(nuki_id, action=action, block=block)

    def unlatch(self, nuki_id, block=False):
        return self.lock_action(
            nuki_id, action=LOCK_ACTIONS['UNLATCH'], block=block
        )
