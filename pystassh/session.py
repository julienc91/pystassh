# -*- coding: utf-8 -*-

""" The Session object is the entry point of any command execution via SSH.

Examples:

    Open a SSH connection, run the "ls" command and print the output.

    >>> with Session('localhost', 'foo', 'bar') as ssh_session:
    ...     result = ssh_session.execute('ls')
    ...     print(result.stdout)

"""

from . import api, exceptions
from . channel import Channel


class Session:

    def __init__(self, hostname="localhost", username="", password="", passphrase="", port=22):

        """ A session object correspond to a unique SSH connexion from which commands can be run.

        Args:
            hostname (str): hostname
            username (str): user name
            password (str): user password
            passphrase (str): optionnal passphrase to be used with a public key authentication
            port (int): SSH remote port
        """
        self._hostname = str.encode(hostname)
        self._username = str.encode(username)
        self._password = str.encode(password)
        self._passphrase = str.encode(passphrase)
        self._port = str.encode(str(port))

        self._session = None
        self._channel = None

    def is_connected(self):
        """ Check if the connexion is currently active.

        Returns:
            bool: A boolean indicating whether or not the connexion is currently active.
        """
        return bool(self._session and api.Api.ssh_is_connected(self._session))

    def connect(self):

        """ Initiate the connection and authentication process on the remote server.

        Raises:
            ConnectionException: if an error occurred during the connection process
            AuthenticationException: if an error occurred during the authentication process
        """
        if self.is_connected():
            return

        session = api.Api.ssh_new()
        if session is None:
            raise exceptions.ConnectionException("Session cannot be created: {}".format(self.get_error_message()))

        ret = api.Api.ssh_options_set(session, api.SSH_OPTIONS_HOST, self._hostname)
        if ret != api.SSH_OK:
            raise exceptions.ConnectionException("Hostname '{}' cannot be set (return code: {}): {}".format(
                self._hostname, ret, self.get_error_message(session)))

        ret = api.Api.ssh_options_set(session, api.SSH_OPTIONS_PORT_STR, self._port)
        if ret != api.SSH_OK:
            raise exceptions.ConnectionException("Port '{}' cannot be set (return code: {}): {}".format(
                self._port, ret, self.get_error_message(session)))

        ret = api.Api.ssh_options_set(session, api.SSH_OPTIONS_USER, self._username)
        if ret != api.SSH_OK:
            raise exceptions.ConnectionException("Username '{}' cannot be set (return code: {}): {}".format(
                self._username, ret, self.get_error_message(session)))

        ret = api.Api.ssh_connect(session)
        if ret != api.SSH_OK:
            raise exceptions.ConnectionException("Connection cannot be made (return code: {}): {}".format(
                ret, self.get_error_message(session)))

        if self._password:
            ret = api.Api.ssh_userauth_password(session, self._username, self._password)
            if ret != api.SSH_AUTH_SUCCESS:
                raise exceptions.AuthenticationException(
                    "Authentication cannot be made with username and password (return code: {}): {}".format(
                        ret, self.get_error_message(session)))
        else:
            ret = api.Api.ssh_userauth_autopubkey(session, self._passphrase)
            if ret != api.SSH_AUTH_SUCCESS:
                raise exceptions.AuthenticationException(
                    "Authentication cannot be made with public key (return code: {}): {}".format(
                        ret, self.get_error_message(session)))

        self._session = session
        self._channel = Channel(self._session)

    def disconnect(self):
        """ Close the current connection.
        """
        if self.is_connected():
            api.Api.ssh_disconnect(self._session)
        self._session = None

    def execute(self, command):
        """ Execute a command on the remote server.

        Args:
            command (str): the command to run

        Returns:
            Result: the Result object for this command
        """
        if not self.is_connected():
            raise exceptions.PystasshException("The session is not ready, call the connect() method first")
        return self._channel.execute(command)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    def get_error_message(self, session=None):
        """ Tries to retrieve an error message in case of error.

        Args:
            session: a session object that will be used instead of self._session
        Returns:
            str: An error message
        """
        session = session or self._session
        try:
            return api.Api.get_error_message(session)
        except exceptions.UnknownException:
            return "<error message irrecoverable>"
