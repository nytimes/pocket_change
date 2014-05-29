from datetime import timedelta
from functools import partial
from pocket_change.auth.utils import AuthedUserCreator


class AuthenticationSettings(object):

    def __init__(self, browser_token_ttl=timedelta(days=30),
                 api_token_ttl=timedelta(minutes=5)):

        self.creator_classes = {}
        self.browser_token_ttl = browser_token_ttl
        self.api_token_ttl = api_token_ttl
        self.UserCreator('Browser', lambda self, settings=self: settings.browser_token_ttl)
        self.UserCreator('API', lambda self, settings=self: settings.api_token_ttl)

    def UserCreator(self, *args, **kwargs):

        len_args = len(args)
        if not len_args:
            raise TypeError('Creator requires at least 1 argument (name).')
        else:
            name = args[0]
        if len_args == 1:
            if kwargs:
                ttl = property(lambda self, td=timedelta(**kwargs): td)
            else:
                try:
                    return self.creator_classes[args[0]]
                except KeyError:
                    raise ValueError('No known %s AuthedUserCreator.' % args[0])
        elif len_args > 1:
            if callable(args[1]):
                if len_args > 2 or kwargs:
                    ttl = property(partial(args[1], *args[2:], **kwargs))
                else:
                    ttl = property(args[1])
            elif not kwargs and isinstance(args[1], timedelta):
                ttl = property(lambda self, td=args[1]: td)
            else:
                raise TypeError('Creator takes a name, and a ttl (timedelta or callable) or kwargs for a timedelta.')
        else:
            raise TypeError('Creator takes a name, and a ttl (timedelta or callable) or kwargs for a timedelta.')
        NewCreator = type('%sAuthedUserCreator' % name, (AuthedUserCreator,), {'ttl':ttl})
        self.creator_classes[name] = NewCreator
        return NewCreator


authentication_settings = Authed = AuthenticationSettings()