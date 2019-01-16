# coding: utf-8

import json
import logging

import requests

from pynuki.const import LOCK_ACTIONS, LOCK_STATES


LOGGER = logging.getLogger(__name__)


def _auth_req(method, url, token, json_data=None, expect_response=True):
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.request(method, url, headers=headers, json=json_data)
    resp.raise_for_status()
    print('RESPONSE:', resp.text)
    LOGGER.info('RESPONSE: %s', resp.text)
    try:
        return resp.json()
    except json.decoder.JSONDecodeError:
        if expect_response:
            LOGGER.error("Unable to decode JSON response")


class NukiWeb(object):
    def __init__(self, token):
        self.token = token

    @property
    def locks(self):
        resp = _auth_req(
            'GET', 'https://api.nuki.io/smartlock', token=self.token)
        locks = []
        for lock in resp:
            locks.append(NukiLock(self, lock))
        return locks


class NukiLock(object):
    def __init__(self, client, json):
        self._client = client
        self._json = json

    def __repr__(self):
        return '<NukiLock (web): {}>'.format(self._json)

    @property
    def lock_id(self):
        return self._json.get('smartlockId')

    @property
    def name(self):
        return self._json.get('config', {}).get('name')

    @property
    def is_locked(self):
        state = self._json.get('state', {}).get('state')
        return state == LOCK_STATES['LOCKED']

    def lock(self):
        return _auth_req(
            method='POST',
            token=self._client.token,
            url=f'https://api.nuki.io/smartlock/{self.lock_id}/action',
            json_data={'action': 2, 'option': 0},
            expect_response=False)

    def unlock(self):
        return _auth_req(
            method='POST',
            token=self._client.token,
            url=f'https://api.nuki.io/smartlock/{self.lock_id}/action',
            json_data={'action': 1, 'option': 0},
            expect_response=False)
