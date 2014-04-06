import datetime

from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import BasicAuthAuthenticationPolicy

from channelstream.ext_json import json
from channelstream.wsgi_views.wsgi_security import APIFactory


def datetime_adapter(obj, request):
    return obj.isoformat()


STATUS_CODES = {
    "offline": 0,
    "online": 1,
    "away": 2,
    "hidden": 3,
    "busy": 4,
}


def make_app(global_config, **settings):
    config = Configurator(settings=settings, root_factory=APIFactory)

    def check_function(username, password, request):
        if password == settings['admin_secret']:
            return 'admin'
        return None

    authn_policy = BasicAuthAuthenticationPolicy(check_function,
                                                 realm='channelstream')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.registry.settings['server_config'] = global_config
    ips = [ip.strip() for ip in
           config.registry.settings['allow_posting_from'].split(',')]
    config.registry.settings['allow_posting_from'] = ips
    config.registry.settings['status_codes'] = STATUS_CODES
    json_renderer = JSON(serializer=json.dumps)
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    config.add_renderer('json', json_renderer)
    config.add_static_view('static', path='channelstream:static/')
    config.include('pyramid_jinja2')
    config.include('channelstream.wsgi_views')
    config.include('channelstream.socketio_views')
    config.scan('channelstream')
    app = config.make_wsgi_app()
    return app