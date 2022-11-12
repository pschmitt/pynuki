# coding: utf-8

import hashlib
import logging
from datetime import datetime
from random import randint

import nacl.secret
import nacl.utils

logger = logging.getLogger("pynuki")


def sha256sum(text):
    return hashlib.sha256(text.encode("utf-8")).digest()


def encrypt_token(digest):
    nonce = nacl.utils.random(24)
    rnr = randint(0, 65535)
    ts = datetime.utcnow().strftime(f"%Y-%m-%dT%H:%M:%SZ,{rnr}")
    box = nacl.secret.SecretBox(digest)
    ctoken = box.encrypt(ts.encode("utf-8"), nonce)
    return {"ctoken": str(ctoken.ciphertext.hex()), "nonce": str(nonce.hex())}
