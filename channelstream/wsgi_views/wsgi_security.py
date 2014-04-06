from pyramid.security import Allow, Everyone, ALL_PERMISSIONS, authenticated_userid

class RequestBasicChannenge(Exception):
    pass

class APIFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        config = request.registry.settings
        if request.environ['REMOTE_ADDR'] not in config['allow_posting_from']:
            return
        self.__acl__ = [(Allow, Everyone, ALL_PERMISSIONS)]

class BasicAuthFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        user = authenticated_userid(request)
        if user != 'admin':
            raise RequestBasicChannenge()
        self.__acl__ = [(Allow, Everyone, ALL_PERMISSIONS)]