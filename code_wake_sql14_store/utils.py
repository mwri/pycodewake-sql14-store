"""Utils module."""


import hashlib

import bencodepy  # type: ignore


def data_digest(data):
    return hashlib.sha256(bencodepy.encode(data)).digest()
