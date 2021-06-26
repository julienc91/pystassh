# -*- coding: utf-8 -*-

""" The Session object is the entry point of any command execution via SSH.

Examples:

    Open a SSH connection, run the "ls" command and print the output.

    >>> with Session('localhost', 'foo', 'bar') as ssh_session:
    ...     result = ssh_session.execute('ls')
    ...     print(result.stdout)

"""

from . import api, exceptions
from .channel import Channel


class Session:
    def __init__(
        self,
        hostname="localhost",
        username="",
        password="",
        passphrase="",
        port=22,
        privkey_file="",
    ):

        """A session object correspond to a unique SSH connexion from which commands can be run.

        Args:
            hostname (str): hostname
            username (str): user name
            password (str): user password
            passphrase (str): optional passphrase to be used with a public key authentication
            port (int): SSH remote port
            privkey_file (str): optional file name which has a private key (optionally encrypted with the passphrase)
        """
        # Keep a reference to the Api class so we can access it from __del__().
        # During the deinitialization of the Python VM, the module 'api' may not
        # be available so we have to keep a reference to the Api class.
        self._api = api.Api
        self._hostname = str.encode(hostname)
        self._username = str.encode(username)
        self._password = str.encode(password)
        self._passphrase = str.encode(passphrase)
        self._privkey_file = str.encode(privkey_file)
        self._port = str.encode(str(port))

        self._session = None
        self._channel = None

    def is_connected(self):
        """Check if the connexion is currently active.

        Returns:
            bool: A boolean indicating whether or not the connexion is currently active.
        """
        return bool(self._session and self._api.ssh_is_connected(self._session))

    def connect(self):

        """Initiate the connection and authentication process on the remote server.

        Raises:
            ConnectionException: if an error occurred during the connection process
            AuthenticationException: if an error occurred during the authentication process
        """
        if self.is_connected():
            return

        session = self._api.ssh_new()
        if session is None:
            raise exceptions.ConnectionException(
                "Session cannot be created: {}".format(self.get_error_message())
            )

        try:
            ret = self._api.ssh_options_set(
                session, api.SSH_OPTIONS_HOST, self._hostname
            )
            if ret != api.SSH_OK:
                raise exceptions.ConnectionException(
                    "Hostname '{}' cannot be set (return code: {}): {}".format(
                        self._hostname, ret, self.get_error_message(session)
                    )
                )

            ret = self._api.ssh_options_set(
                session, api.SSH_OPTIONS_PORT_STR, self._port
            )
            if ret != api.SSH_OK:
                raise exceptions.ConnectionException(
                    "Port '{}' cannot be set (return code: {}): {}".format(
                        self._port, ret, self.get_error_message(session)
                    )
                )

            ret = self._api.ssh_options_set(
                session, api.SSH_OPTIONS_USER, self._username
            )
            if ret != api.SSH_OK:
                raise exceptions.ConnectionException(
                    "Username '{}' cannot be set (return code: {}): {}".format(
                        self._username, ret, self.get_error_message(session)
                    )
                )

            ret = self._api.ssh_connect(session)
            if ret != api.SSH_OK:
                raise exceptions.ConnectionException(
                    "Connection cannot be made (return code: {}): {}".format(
                        ret, self.get_error_message(session)
                    )
                )

            if self._password:
                ret = self._api.ssh_userauth_password(
                    session, self._username, self._password
                )
                if ret != api.SSH_AUTH_SUCCESS:
                    raise exceptions.AuthenticationException(
                        "Authentication cannot be made with username and password (return code: {}): {}".format(
                            ret, self.get_error_message(session)
                        )
                    )
            else:
                if self._privkey_file:
                    null = self._api.NULL
                    pkey = self._api.new_key_pointer()

                    ret = self._api.ssh_pki_import_privkey_file(
                        self._privkey_file, self._passphrase, null, null, pkey
                    )

                    if ret != api.SSH_OK:
                        raise exceptions.AuthenticationException(
                            "Private key could not be used (return code: {}): {}".format(
                                ret, self.get_error_message(session)
                            )
                        )

                    key = pkey[0]  # dereference the pointer to get the key
                    ret = self._api.ssh_userauth_publickey(session, null, key)

                    # once authenticated we don't need the key anymore
                    self._api.ssh_key_free(key)
                else:
                    ret = self._api.ssh_userauth_autopubkey(session, self._passphrase)

                # check last userauth call and see if we had been authenticated
                # or not.
                if ret != api.SSH_AUTH_SUCCESS:
                    raise exceptions.AuthenticationException(
                        "Authentication cannot be made with public key (return code: {}): {}".format(
                            ret, self.get_error_message(session)
                        )
                    )

            self._session = session
            self._channel = Channel(self._session)
        except Exception:
            self._api.ssh_free(session)
            self._session = self._channel = None
            raise

    def disconnect(self):
        """Close the current connection."""
        if self.is_connected():
            self._channel and self._channel.close()
            self._api.ssh_disconnect(self._session)
            self._api.ssh_free(self._session)
        self._channel = None
        self._session = None

    def execute(self, command):
        """Execute a command on the remote server.

        Args:
            command (str): the command to run

        Returns:
            Result: the Result object for this command
        """
        if not self.is_connected():
            raise exceptions.PystasshException(
                "The session is not ready, call the connect() method first"
            )
        return self._channel.execute(command)

    @property
    def channel(self):
        return self._channel

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    def __del__(self):
        self.disconnect()
        del self._api

    def get_error_message(self, session=None):
        """Tries to retrieve an error message in case of error.

        Args:
            session: a session object that will be used instead of self._session
        Returns:
            str: An error message
        """
        session = session or self._session
        try:
            return self._api.get_error_message(session)
        except exceptions.UnknownException:
            return "<error message irrecoverable>"
