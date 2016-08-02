# -*- coding: utf-8 -*-

from . import api


class Result:

    def __init__(self, channel, command):
        """ A Result object contains the execution details of a command.

        Args:
            channel: the libssh's channel instance the result will be attached to
            command: the last command that was run
        """
        self._channel = channel
        self._command = command
        self._buffer_size = 100000
        self._stdout = self._read_stdout_or_stderr(False)
        self._stderr = self._read_stdout_or_stderr(True)
        self._return_code = self._read_return_code()

    def __read(self, is_stderr):
        buffer = api.Api.new_chars(self._buffer_size)
        return (api.Api.ssh_channel_read(self._channel, buffer, self._buffer_size, int(is_stderr)),
                api.Api.to_string(buffer))

    def _read_stdout_or_stderr(self, is_stderr):

        content = b""
        count, buffer = self.__read(is_stderr)
        while count:
            content += buffer
            count, buffer = self.__read(is_stderr)
        return content

    def _read_return_code(self):
        return api.Api.ssh_channel_get_exit_status(self._channel)

    @property
    def command(self):
        """ The command from wich the current results came from.
        """
        return self._command

    @property
    def raw_stdout(self):
        """ The raw content of the standard output, as a list of bytes.
        """
        return self._stdout

    @property
    def stdout(self):
        """ The content of the standard output, as a string. Decoding errors are not caught at this level.
        """
        return self.raw_stdout.decode("utf8", "replace").rstrip("\r\n")

    @property
    def raw_stderr(self):
        """ The raw content of the standard error output, as a list of bytes.
        """
        return self._stderr

    @property
    def stderr(self):
        """ The content of the standard error output, as a string. Decoding errors are not caught at this level.
        """
        return self.raw_stderr.decode("utf8", "replace").rstrip("\r\n")

    @property
    def return_code(self):
        """ The return code of the last command as an int.
        """
        return self._return_code
