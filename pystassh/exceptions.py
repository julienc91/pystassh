# -*- coding: utf-8 -*-


class PystasshException(Exception):
    """ A base exception for all other Pystassh exceptions.
    """
    pass


class ConnectionException(PystasshException):
    """ Raised when something went wrong during the connection process.
    """
    pass


class AuthenticationException(PystasshException):
    """ Raised when something went wrong during the authentication process.
    """
    pass


class ChannelException(PystasshException):
    """ Raised when an error occurred in the context of a channel.
    """
    pass


class UnknownException(PystasshException):
    """ Sometimes we just don't know what happened...
    """
    pass
