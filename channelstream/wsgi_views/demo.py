import json
import random
import uuid

import requests
from pyramid.view import view_config
from channelstream.util import base64_decode, base64_encode, hmac_encode
import gevent

POSSIBLE_CHANNELS = ['pub_chan', 'pub_chan2', 'notify']


def make_request(request, payload, endpoint):
    server_port = request.registry.settings['port']
    sig_for_server = hmac_encode(request.registry.settings['secret'],
                                 endpoint)
    secret_headers = {'x-channelstream-secret': sig_for_server,
                      'x-channelstream-endpoint': endpoint,
                      'Content-Type': 'application/json'}
    url = 'http://127.0.0.1:%s%s' % (server_port, endpoint)
    response = requests.post(url, data=json.dumps(payload),
                             headers=secret_headers).json()
    return response


def enable_demo(context, request):
    if request.registry.settings['demo']:
        return True
    return False


class DemoViews(object):
    def __init__(self, request):
        self.request = request
        self.request.response.headers.add('Cache-Control', 'no-cache, no-store')


    @view_config(route_name='section_action', renderer='string',
                 request_method="OPTIONS",
                 custom_predicates=[enable_demo])
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
        return {}

    @view_config(route_name='demo', renderer='templates/demo.jinja2',
                 custom_predicates=[enable_demo])
    def demo(self):
        return {}


    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=connect'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def connect(self):
        """handle authorization of users trying to connect"""
        random_name = 'anon_%s' % random.randint(1, 999999)
        payload = {"username": random_name}
        sig_for_user = hmac_encode(self.request.registry.settings['secret'],
                                   random_name)
        payload['channels'] = POSSIBLE_CHANNELS
        result = make_request(self.request, payload, '/connect')
        return {"username": random_name, "signature": sig_for_user}

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=subscribe'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def subscribe(self):
        """"can be used to subscribe specific connection to other channels"""
        self.request_data = self.request.json_body
        channels = self.request_data['channels']
        POSSIBLE_CHANNELS.intersection(channels)
        payload = {"username": self.request_data.get('username', ''),
                   "channels": self.request_data.get('channels', [])
        }
        result = make_request(self.request, payload, '/subscribe')
        return result

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=message'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def message(self):
        """send message to channel/users"""
        self.request_data = self.request.json_body
        payload = {
            'type': 'message',
            "user": self.request_data.get('username', 'system'),
            "channel": self.request_data.get('channel', 'unknown_channel'),
            'message': self.request_data.get('message')
        }
        result = make_request(self.request, [payload], '/message')
        return result

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=channel_config'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def channel_config(self):
        """configure channel defaults"""
        payload = [
            ('pub_chan', {
                "presence": True,
                "store_history": True,
                "history_size": 20
            }),
            ('pub_chan2', {
                "presence": True,
                "salvagable": True,
                "store_history": True,
                "history_size": 30
            })
        ]
        return "Not used for now"
        result = make_request(self.request, payload, '/channel_config')
        return response