from uuid import uuid4
from datetime import datetime


def uuid4_str():
    return str(uuid4())


def timestamp_str():
    return datetime.isoformat(datetime.utcnow())
