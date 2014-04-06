import logging
from datetime import datetime

import itsdangerous
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget
from pyramid.response import Response

import gevent
from channelstream import total_messages, started_on, total_unique_messages, \
    lock
from channelstream.user import User, USERS
from channelstream.socketio_views.chat import CONNECTIONS
from channelstream.channel import Channel, CHANNELS
from channelstream.ext_json import json
from gevent.queue import Queue, Empty

log = logging.getLogger(__name__)


def pass_message(msg):
    global total_messages
    global total_unique_messages
    if msg.get('timestamp'):
        # if present lets use timestamp provided in the message
        if '.' in msg['timestamp']:
            timestmp = datetime.strptime(msg['timestamp'],
                                         '%Y-%m-%dT%H:%M:%S.%f')
        else:
            timestmp = datetime.strptime(msg['timestamp'],
                                         '%Y-%m-%dT%H:%M:%S')
    else:
        timestmp = datetime.utcnow()
    message = {'user': msg.get('username'),
               'message': msg['message'],
               'type': 'message',
               'timestamp': timestmp
    }
    pm_users = msg.get('pm_users') or []
    total_sent = 0
    global total_unique_messages
    total_unique_messages += 1
    if msg.get('channel'):
        for conn in CONNECTIONS.values():
            if msg['channel'] in conn.session['channels']:
                if not pm_users or conn.session['username'] in pm_users:
                    conn.emit('message', msg)
                    total_messages += total_sent
    elif pm_users:
        # if pm then iterate over all users and notify about new message hiyoo!!
        for conn in CONNECTIONS.values():
            if conn.session['username'] in pm_users:
                conn.emit('message', msg)
                total_messages += total_sent


class ServerViews(object):
    def __init__(self, request):
        self.request = request

    @view_config(route_name='action', match_param='action=connect',
                 renderer='json', permission='access')
    def connect(self):
        """return the id of connected users - will be secured with password string
        for webapp to internally call the server - we combine conn string with user id,
        and we tell which channels the user is allowed to subscribe to"""
        username = self.request.json_body.get('username')
        def_status = self.request.registry.settings['status_codes']['online']
        user_status = int(self.request.json_body.get('status', def_status))
        conn_id = self.request.json_body.get('conn_id')
        subscribe_to_channels = self.request.json_body.get('channels')
        if username is None:
            self.request.response.status = 400
            return {'error': "No username specified"}
        if not subscribe_to_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}

        # everything is ok so lets add new connection to channel and connection list
        with lock:
            if not username in USERS:
                user = User(username, def_status)
                USERS[username] = user
            else:
                user = USERS[username]
            for channel_name in subscribe_to_channels:
                if channel_name not in CHANNELS:
                    channel = Channel(channel_name)
                    CHANNELS[channel_name] = channel
            user.allowed_channels.extend(subscribe_to_channels)
            log.info('connecting %s' % username)
        return {'status': user.status}

    @view_config(route_name='action', match_param='action=subscribe',
                 renderer='json', permission='access')
    def subscribe(self, *args):
        """ call this to subscribe specific connection to new channels """
        username = self.request.json_body.get('username')
        subscribe_to_channels = self.request.json_body.get('channels')
        if not subscribe_to_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}
        with lock:
            for chan in subscribe_to_channels:
                if chan not in USERS['username'].allowed_channels:
                    USERS['username'].allowed_channels.append(chan)
                    # create channels that didnt exist
                    if chan not in CHANNELS:
                        channel = Channel(chan)
                        CHANNELS[chan] = channel
        return subscribe_to_channels


    @view_config(route_name='action', match_param='action=listen',
                 request_method="OPTIONS", renderer='string')
    def handle_CORS(self):
        self.request.response.headers.add('Access-Control-Allow-Origin', '*')
        self.request.response.headers.add('XDomainRequestAllowed', '1')
        self.request.response.headers.add('Access-Control-Allow-Methods',
                                          'GET, POST, OPTIONS, PUT')
        self.request.response.headers.add('Access-Control-Allow-Headers',
                                          'Content-Type, Depth, User-Agent, '
                                          'X-File-Size, X-Requested-With, '
                                          'If-Modified-Since, X-File-Name, '
                                          'Cache-Control, Pragma, Origin, '
                                          'Connection, Referer, Cookie')
        self.request.response.headers.add('Access-Control-Max-Age', '86400')
        # self.request.response.headers.add('Access-Control-Allow-Credentials', 'true')
        return ''

    @view_config(route_name='action', match_param='action=user_status',
                 renderer='json', permission='access')
    def user_status(self):
        """ set the status of specific user """
        username = self.request.json_body.get('user')
        def_status = self.request.registry.settings['status_codes']['online']
        user_status = int(self.request.json_body.get('status', def_status))
        if not username:
            self.request.response.status = 400
            return {'error': "No username specified"}

        if username in USERS:
            USERS[username].status = user_status
        return {}


    @view_config(route_name='action', match_param='action=message',
                 renderer='json', permission='access')
    def message(self):
        msg_list = self.request.json_body
        for msg in msg_list:
            if not msg.get('channel') and not msg.get('pm_users', []):
                continue
            gevent.spawn(pass_message, msg)

    #
    # @view_config(route_name='action', match_param='action=channel_config',
    #              renderer='json', permission='access')
    # def channel_config(self):
    #     """ call this to subscribe specific connection to new channels """
    #     channel_data = self.request.json_body
    #     if not channel_data:
    #         self.request.response.status = 400
    #         return {'error': "No channels specified"}
    #
    #     json_data = []
    #     with lock:
    #         for channel_name, config in channel_data:
    #             if not channel_inst:
    #                 channel = Channel(channel_name)
    #                 channels[channel_name] = channel
    #             channel_inst = channels[channel_name]
    #             for k, v in config.iteritems():
    #                 setattr(channel_inst, k, v)
    #             json_data.append({'name': channel_inst.name,
    #                               'long_name': channel_inst.long_name,
    #                               'presence': channel_inst.presence,
    #                               'salvagable': channel_inst.salvagable,
    #                               'store_history': channel_inst.store_history,
    #                               'history_size': channel_inst.history_size
    #             })
    #     return json_data
    #
    @view_config(
        context='channelstream.wsgi_views.wsgi_security:RequestBasicChannenge')
    def admin_challenge(self):
        response = HTTPUnauthorized()
        response.headers.update(forget(self.request))
        return response

    @view_config(route_name='admin',
                 renderer='templates/admin.jinja2', permission='access')
    def admin(self):
        uptime = datetime.utcnow() - started_on
        remembered_user_count = len(
            [user for user in USERS.iteritems()])
        uq_u_dict = {}
        channel_conns = {}
        for conn in CONNECTIONS.values():
            if not conn.session['username'] in uq_u_dict:
                uq_u_dict[conn.session['username']] = 0
            uq_u_dict[conn.session['username']] += 1
            for chan in conn.session['channels']:
                if chan not in channel_conns:
                    channel_conns[chan] = {}
                if conn.session['username'] not in channel_conns[chan]:
                    channel_conns[chan][conn.session['username']] = 0
                channel_conns[chan][conn.session['username']] = +1
        unique_user_count = 0
        total_connections = len(CONNECTIONS)
        return {
            "remembered_user_count": remembered_user_count,
            "unique_user_count": unique_user_count,
            "total_connections": total_connections,
            "total_messages": total_messages,
            "total_unique_messages": total_unique_messages,
            "channels": CHANNELS,
            "channel_conns":channel_conns,
            "users": USERS, "uptime": uptime
        }


    @view_config(route_name='action', match_param='action=info',
                 renderer='json', permission='access')
    def info(self):
        start_time = datetime.now()

        json_data = {"channels": {}, "unique_users": len(USERS)}

        # select everything for empty list
        if not self.request.body or not self.request.json_body.get('channels'):
            req_channels = CHANNELS.keys()
        else:
            req_channels = self.request.json_body['channels']
        # return requested channel info
        for channel_inst in [chan for chan in CHANNELS.values() if
                             chan.name in req_channels]:
            json_data["channels"][channel_inst.name] = {}
            json_data["channels"][channel_inst.name]['total_users'] = len(
                channel_inst.connections)
            json_data["channels"][channel_inst.name]['total_connections'] = sum(
                [len(conns) for conns in channel_inst.connections.values()])
            json_data["channels"][channel_inst.name]['users'] = []
            for username in channel_inst.connections.keys():
                user_inst = users.get(username)
                udata = {'user': user_inst.username,
                         'status': user_inst.status,
                         "connections": [conn.id for conn in
                                         channel_inst.connections[username]]}
                json_data["channels"][channel_inst.name]['users'].append(udata)
            json_data["channels"][channel_inst.name][
                'last_active'] = channel_inst.last_active
        log.info('info time: %s' % (datetime.now() - start_time))
        return json_data