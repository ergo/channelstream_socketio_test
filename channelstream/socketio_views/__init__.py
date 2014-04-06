"""View handlers package.
"""
import logging


log = logging.getLogger(__name__)


def includeme(config):
    config.add_route('socketio', 'socket.io/*remaining')
