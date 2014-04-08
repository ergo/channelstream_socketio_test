from pyramid.security import Allow, Everyone, ALL_PERMISSIONS, \
    authenticated_userid
from channelstream.util import hmac_validate


class RequestBasicChannenge(Exception):
    pass


class APIFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        config = request.registry.settings
        req_url_secret = request.params.get('secret')
        req_secret = request.headers.get('x-channelstream-secret',
                                         req_url_secret)
        if request.environ['REMOTE_ADDR'] not in config[
            'allow_posting_from'] or not req_secret:
            return
        if req_secret:
            hmac_validate(config['secret'], request.path, req_secret)
        else:
            return
        self.__acl__ = [(Allow, Everyone, ALL_PERMISSIONS)]


class BasicAuthFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        user = authenticated_userid(request)
        if user != 'admin':
            raise RequestBasicChannenge()
        self.__acl__ = [(Allow, Everyone, ALL_PERMISSIONS)]