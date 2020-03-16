# coding: utf-8

from datetime import datetime
from random import randint
import hashlib
import logging


logger = logging.getLogger("pynuki")


def sha256sum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_token(token):
    rnr = randint(0, 65535)
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    hash_256 = sha256sum(f"{ts},{rnr},{token}")
    return {"ts": ts, "rnr": rnr, "hash": hash_256}
