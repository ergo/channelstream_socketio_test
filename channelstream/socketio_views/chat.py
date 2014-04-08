from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from socketio.mixins import BroadcastMixin
from pyramid.response import Response
from pyramid.view import view_config
import gevent
from datetime import datetime, timedelta
from channelstream.channel import Channel, CHANNELS
from channelstream.user import User, USERS
from channelstream.util import hmac_validate
from channelstream import total_messages, started_on, total_unique_messages, \
    lock

CONNECTIONS = {}


class StreamNamespace(BaseNamespace):
    def initialize(self):
        # print 'initialize'
        sig = self.request.GET.get('signature')
        user_name = self.request.GET.get('username')
        if not sig or not user_name:
            self.disconnect(silent=True)
            return
        hmac_validate(self.request.registry.settings['secret'],
                      user_name, sig)
        def_status = self.request.registry.settings['status_codes']['online']
        CONNECTIONS[id(self)] = self

        self.last_active = datetime.utcnow()
        if 'channels' not in self.session:
            self.session['channels'] = set()  # a set of simple strings
            self.session['username'] = user_name
            # self.spawn(self.heartbeat)


    def recv_connect(self):
        if self.session['username'] not in USERS:
            self.socket.disconnect()

    def recv_disconnect(self):
        self.disconnect(silent=True)

    def disconnect(self, silent=False):
        if id(self) in CONNECTIONS:
            del CONNECTIONS[id(self)]
        super(StreamNamespace, self).disconnect(silent)


    def on_join(self, channels):
        # print 'on_join', channels
        matched_channels = []
        presence_info = []
        for channel in channels:
            if channel in USERS[self.session['username']].allowed_channels:
                self.session['channels'].add(channel)
                matched_channels.append(channel)
                if CHANNELS[channel].presence:
                    presence_info.append(channel)
        self.emit('join', matched_channels)
        if presence_info:
            for conn in CONNECTIONS.values():
                common = conn.session['channels'] & set(presence_info)
                conn.emit('presence_join', self.session['username'],
                          list(common))


    def on_leave(self, channels):
        # print 'on_join', channels
        matched_channels = []
        presence_info = []
        for channel in channels:
            if channel in self.session['channels']:
                self.session['channels'].remove(channel)
                matched_channels.append(channel)
                if CHANNELS[channel].presence:
                    presence_info.append(channel)
        self.emit('leave', matched_channels)
        if presence_info:
            for conn in CONNECTIONS.values():
                common = conn.session['channels'] & set(presence_info)
                conn.emit('presence_leave', self.session['username'],
                          list(common))


    def heartbeat(self):
        # print 'heartbeat', self.session['username'], id(self)
        if id(self) in CONNECTIONS:
            try:
                self.emit('heartbeat', '')
                gevent.sleep(5)
                self.spawn(self.heartbeat)
            except Exception as e:
                self.mark_for_gc()
                self.disconnect()

    def mark_for_gc(self):
        # set last active time for connection 1 hour in past for GC
        self.last_active -= timedelta(minutes=60)


@view_config(route_name='socketio', renderer='string')
def socketio_service(request):
    socketio_manage(request.environ,
                    {'/stream': StreamNamespace},
                    request=request
    )

    return Response('')