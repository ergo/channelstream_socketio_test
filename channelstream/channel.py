from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)

CHANNELS = {}


class Channel(object):
    """ Represents one of our chat channels - has some config options """

    def __init__(self, name, long_name=None):
        self.name = name
        self.long_name = long_name
        self.last_active = datetime.utcnow()
        self.presence = False
        self.salvagable = False
        self.store_history = False
        self.history_size = 10
        self.history = []
        log.info('%s created' % self)

    def __repr__(self):
        return '<Channel: %s>' % (self.name)