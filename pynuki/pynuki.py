#!/usr/bin/python
# coding: utf-8

'''
Based on the Bridge API version 1.5

Documentation:
https://nuki.io/wp-content/uploads/2016/04/Bridge-API-v1.5.pdf
'''

import requests
import logging
import time
from threading import Lock


logger = logging.getLogger(__name__)

RQ_LOCK = Lock()
REQUESTS_TIMEOUT = 5
REQUEST_GAP_SECONDS = 2
RQ_TIMEOUT = 5
LOCK_STATES = {
    'UNCALIBRATED': 0,
    'LOCKED': 1,
    'UNLOCKING': 2,
    'UNLOCKED': 3,
    'LOCKING': 4,
    'UNLATCHED': 5,
    'UNLOCKED_LOCK_N_GO': 6,
    'UNLATCHING': 7,
    'MOTOR BLOCKED': 254,
    'UNDEFINED': 255
}

LOCK_ACTIONS = {
    'UNLOCK': 1,
    'LOCK': 2,
    'UNLATCH': 3,
    'LOCK_N_GO': 4,
    'LOCK_N_GO_WITH_UNLATCH': 5
}


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

    def updated_lock_result(self, result, lock_state, block):
        if block and result is not None and result["success"]:
          result.update({'state': lock_state})
          self._json.update({k: v for k, v in result.items() if k != 'success'})
        return result

    def lock(self, block=False):
        return self.updated_lock_result(
             self._bridge.lock(nuki_id=self.nuki_id, block=block),
             LOCK_STATES['LOCKED'],
             block
        )

    def unlock(self, block=False):
        return self.updated_lock_result(
             self._bridge.unlock(nuki_id=self.nuki_id, block=block),
             LOCK_STATES['UNLOCKED'],
             block
        )

    def lock_n_go(self, unlatch=False, block=False):
        return  self.update_self_with_lock_result(
             self._bridge.lock_n_go(
                nuki_id=self.nuki_id, unlatch=unlatch, block=block),
             LOCK_STATES['UNLOCKED_LOCK_N_GO']
        ) 

    def unlatch(self, block=False):
        return  self.updated_ock_result(
             self._bridge.unlatch(nuki_id=self.nuki_id, block=block),
             LOCK_STATES['UNLATCHED'],
             block
        )

    def update(self, aggressive=False):
        """
        Update the state of the NukiLock
        :param aggressive: Whether to aggressively poll the Bridge. If set to
        True, this will actively query the Lock, thus using more battery.
        :type aggressive: bool
        """
        if aggressive:
            data = self._bridge.lock_state(self.nuki_id)
            if data is None or not data['success']:
               logger.warning('Failed to update the state of lock {}'.format(self.nuki_id))
               raise ValueError('Update not completed')
            else:
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
    def __init__(self, hostname, token, port=8080, timeout=REQUESTS_TIMEOUT, should_queue=True):
        self.hostname = hostname
        self.token = token
        self.port = port
        self.requests_timeout = timeout
        self.__api_url = 'http://{}:{}'.format(hostname, port)
        self.should_queue = should_queue

    @staticmethod
    def __make_request(url,token, endpoint, requests_timeout, should_queue, params=None):
        if should_queue:
           RQ_LOCK.acquire()
           time.sleep(REQUEST_GAP_SECONDS)
        try:
           url = '{}/{}'.format(url, endpoint)
           get_params = {'token': token}
           if params:
             get_params.update(params)
           return_result = None
           try:
             logger.debug('Nuki request {} {} '.format(url,get_params))
             result = requests.get(url, params=get_params, timeout=requests_timeout)
             result.raise_for_status()
             return_result = result.json()
             logger.debug('Nuki response {} '.format(return_result))
           except Exception as e:
             logger.warning('Nuki bridge request failed {}'.format(e))
        finally:
           if should_queue:
             RQ_LOCK.release()
           return return_result

    def __rq(self, endpoint, params=None):
        return self.__make_request(self.__api_url, self.token, endpoint, self.requests_timeout, self.should_queue, params)

    def auth(self):
        result = self.__rq('auth')
        return result.json()

    def config_auth(self, enable):
        return self.__rq('configAuth', {'enable': 1 if enable else 0})

    def list(self):
        return self.__rq('list')

    def lock_state(self, nuki_id):
      return self.__rq('lockState', {'nukiId': nuki_id})

    def lock_action(self, nuki_id, action, block=True):
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

    def lock(self, nuki_id, block=True):
        return self.lock_action(
            nuki_id, action=LOCK_ACTIONS['LOCK'], block=block
        )

    def unlock(self, nuki_id, block=True):
        return self.lock_action(
            nuki_id, action=LOCK_ACTIONS['UNLOCK'], block=block
        )

    def lock_n_go(self, nuki_id, unlatch=False, block=True):
        action = LOCK_ACTIONS['LOCK_N_GO']
        if unlatch:
            action = LOCK_ACTIONS['LOCK_N_GO_WITH_UNLATCH']
        return self.lock_action(nuki_id, action=action, block=block)

    def unlatch(self, nuki_id, block=True):
        return self.lock_action(
            nuki_id, action=LOCK_ACTIONS['UNLATCH'], block=block
        )

