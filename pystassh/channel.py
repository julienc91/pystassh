# -*- coding: utf-8 -*-

from . import api, exceptions
from . result import Result


class Channel:

    def __init__(self, session):
        """ A channel is an environment bound to a session in which commands can be run.

        Args:
            session: the libssh's session instance the channel will be bound to
        """
        self._session = session
        self._channel = None
        self._stdout = None
        self._stderr = None

    def _is_open(self):
        return bool(self._channel and api.Api.ssh_channel_is_open(self._channel))

    def open(self):
        """ Open a new channel.

        Raises:
            ChannelException: if the channel could not be correctly initialized
        """
        if self._is_open():
            return

        channel = api.Api.ssh_channel_new(self._session)
        if channel is None:
            raise exceptions.ChannelException("Channel cannot be created: {}".format(self.get_error_message()))

        ret = api.Api.ssh_channel_open_session(channel)
        if ret != api.SSH_OK:
            raise exceptions.ChannelException("Channel cannot be opened: {}".format(self.get_error_message()))

        self._channel = channel

    def close(self):
        """ Close the current channel.
        """
        if self._is_open():
            api.Api.ssh_channel_send_eof(self._channel)
            api.Api.ssh_channel_free(self._channel)
        self._channel = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def execute(self, command):
        """ Execute a command.

        Args:
            command (str): the command to run

        Returns:
            Result: the Result object for this command
        """
        with self:
            ret = api.Api.ssh_channel_request_exec(self._channel, str.encode(command))
            if ret != api.SSH_OK:
                raise exceptions.ChannelException("Command cannot be executed (return code: {}): {}".format(
                    command, self.get_error_message()))
            return Result(self._channel, command)

    def get_error_message(self):
        """ Tries to retrieve an error message in case of error.

        Returns:
            str: An error message
        """
        try:
            return api.Api.get_error_message(self._session)
        except exceptions.UnknownException:
            return "<error message irrecoverable>"
