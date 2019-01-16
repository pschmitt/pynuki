# coding: utf-8

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
