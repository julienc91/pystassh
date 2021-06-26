# -*- coding: utf-8 -*-

from . import api, exceptions
from .result import Result


class Channel:
    def __init__(self, session):
        """A channel is an environment bound to a session in which commands can be run.

        Args:
            session: the libssh's session instance the channel will be bound to
        """
        self._session = session
        self._channel = None
        self._stdout = None
        self._stderr = None
        self._shell_requested = False

    def _is_open(self):
        return bool(self._channel and api.Api.ssh_channel_is_open(self._channel))

    def open(self):
        """Open a new channel.

        Raises:
            ChannelException: if the channel could not be correctly initialized
        """
        if self._is_open():
            return

        channel = api.Api.ssh_channel_new(self._session)
        if channel is None:
            raise exceptions.ChannelException(
                "Channel cannot be created: {}".format(self.get_error_message())
            )

        ret = api.Api.ssh_channel_open_session(channel)
        if ret != api.SSH_OK:
            api.Api.ssh_channel_free(channel)
            raise exceptions.ChannelException(
                "Channel cannot be opened: {}".format(self.get_error_message())
            )

        self._shell_requested = False
        self._channel = channel

    def close(self):
        """Close the current channel."""
        if self._is_open():
            api.Api.ssh_channel_send_eof(self._channel)
            api.Api.ssh_channel_free(self._channel)
        self._shell_requested = False
        self._channel = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def request_shell(self, request_pty=False):
        """Request a shell and optionally a PTY."""
        if not self._is_open():
            raise exceptions.ChannelException("The channel is not open.")

        if request_pty:
            ret = api.Api.ssh_channel_request_pty(self._channel)
            if ret != api.SSH_OK:
                raise exceptions.ChannelException(
                    "Request a pseudo-TTY failed: {}".format(self.get_error_message())
                )

        ret = api.Api.ssh_channel_request_shell(self._channel)
        if ret != api.SSH_OK:
            raise exceptions.ChannelException(
                "Request a shell failed: {}".format(self.get_error_message())
            )
        self._shell_requested = True

    def read_nonblocking(self, size=2048, from_stderr=False):
        """Do a nonblocking read on the channel.

        Args:
            size (int): bytes to try to read atomically and without blocking.
            from_stderr (bool): read from standard error instead from stdout.

        Returns:
            string (str): the string read. It may be shorter than the expected size.
                          An empty string does not imply an EOF: you still have to check it.
        """
        if size <= 0:
            raise ValueError("Size must be positive but received '{}'".format(size))
        if not self._is_open():
            raise exceptions.ChannelException("The channel is not open.")
        if not self._shell_requested:
            raise exceptions.ChannelException(
                "No shell was requested for this channel."
            )

        buf = api.Api.new_chars(size)
        from_stderr = int(from_stderr)
        ret = api.Api.ssh_channel_read_nonblocking(
            self._channel, buf, size, from_stderr
        )
        if ret == api.SSH_ERROR:
            raise exceptions.ChannelException(
                "Read failed: {}".format(self.get_error_message())
            )

        return api.Api.to_string(buf)

    def read(self, size=2048, from_stderr=False):
        """Reads data from a channel. The read will block.

        Args:
            size (int): bytes to read.
            from_stderr (bool): read from standard error instead from stdout.

        Returns:
            string (str): the string read. Returns an empty string on EOF.
        """
        if size <= 0:
            raise ValueError("Size must be positive but received '{}'".format(size))
        if not self._is_open():
            raise exceptions.ChannelException("The channel is not open.")
        if not self._shell_requested:
            raise exceptions.ChannelException(
                "No shell was requested for this channel."
            )

        buf = api.Api.new_chars(size)
        from_stderr = int(from_stderr)
        ret = api.Api.ssh_channel_read(self._channel, buf, size, from_stderr)
        if ret == api.SSH_ERROR or ret < 0:
            raise exceptions.ChannelException(
                "Read failed: {}".format(self.get_error_message())
            )

        return api.Api.to_string(buf)

    def write(self, data):
        """Blocking write on a channel.

        Args:
            data (str): data to encode (to bytes) and write (not binary safe).

        Results:
            The number of bytes written.
        """
        if not self._is_open():
            raise exceptions.ChannelException("The channel is not open.")
        if not self._shell_requested:
            raise exceptions.ChannelException(
                "No shell was requested for this channel."
            )

        data = str.encode(data)
        sz = len(data)

        ret = api.Api.ssh_channel_write(self._channel, data, sz)
        if ret == api.SSH_ERROR:
            raise exceptions.ChannelException(
                "Write failed: {}".format(self.get_error_message())
            )

        return ret

    def is_eof(self):
        """Check if remote has sent an EOF."""
        if not self._is_open():
            raise exceptions.ChannelException("The channel is not open.")
        ret = api.Api.ssh_channel_is_eof(self._channel)
        return bool(ret)

    def execute(self, command):
        """Execute a command.

        Args:
            command (str): the command to run

        Returns:
            Result: the Result object for this command
        """
        with self:
            ret = api.Api.ssh_channel_request_exec(self._channel, str.encode(command))
            if ret != api.SSH_OK:
                raise exceptions.ChannelException(
                    "Command cannot be executed (return code: {}): {}".format(
                        command, self.get_error_message()
                    )
                )
            return Result(self._channel, command)

    def get_error_message(self):
        """Tries to retrieve an error message in case of error.

        Returns:
            str: An error message
        """
        try:
            return api.Api.get_error_message(self._session)
        except exceptions.UnknownException:
            return "<error message irrecoverable>"
