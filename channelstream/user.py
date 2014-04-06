from datetime import datetime, timedelta
from channelstream import lock
import logging

import gevent


log = logging.getLogger(__name__)

USERS ={}

class User(object):
    """ represents a unique user of the system """

    def __init__(self, username, status):
        self.username = username
        self.status = status
        self.allowed_channels = []
        self.last_active = datetime.utcnow()

    def __repr__(self):
        return '<User:%s, status:%s>' % (
        self.username, self.status)


def gc_users():
    with lock:
        start_time = datetime.utcnow()
        threshold = datetime.utcnow() - timedelta(days=1)
        for user in USERS.values():
            if user.last_active < threshold:
                USERS.pop(user.username)
        log.info('gc_users() time %s' % (datetime.utcnow() - start_time))
    gevent.spawn_later(60, gc_users)

gevent.spawn_later(60, gc_users)