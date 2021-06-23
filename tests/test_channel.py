# -*- coding: utf-8 -*-

from unittest.mock import MagicMock

import pytest

import pystassh.api
import pystassh.exceptions
import pystassh.result
from pystassh.channel import Channel


@pytest.fixture
def patched_channel(monkeypatch):

    monkeypatch.setattr("ctypes.util.find_library", lambda _: "libssh.so.42")
    monkeypatch.setattr("cffi.FFI.dlopen", lambda *_: MagicMock())
    monkeypatch.setattr("pystassh.api.Api.to_string", lambda chars: chars)
    monkeypatch.setattr("pystassh.api.Api.ssh_get_error", lambda *_: "<error message>")
    return Channel


def test_channel_init(patched_channel):
    channel = patched_channel("<session object>")
    assert channel._session == "<session object>"


def test_channel_is_open(monkeypatch, patched_channel):

    channel = patched_channel("<session object>")
    assert channel._is_open() is False

    channel._channel = "<channel object>"
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_is_open", lambda *_: 0)
    assert channel._is_open() is False

    monkeypatch.setattr("pystassh.api.Api.ssh_channel_is_open", lambda *_: 1)
    assert channel._is_open() is True

    channel._channel = None
    assert channel._is_open() is False


def test_channel_open(monkeypatch, patched_channel):

    fake_ssh_channel_free = MagicMock()
    channel = patched_channel("<session object>")
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    channel.open()
    assert channel._channel == "<channel object>"
    fake_ssh_channel_free.assert_not_called()

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<new channel object>"
    )
    channel.open()
    assert channel._channel == "<channel object>"
    channel._channel = None
    fake_ssh_channel_free.assert_not_called()

    channel.open()
    assert channel._channel == "<new channel object>"
    fake_ssh_channel_free.assert_not_called()


def test_channel_open_ssh_channel_new_error(monkeypatch, patched_channel):

    fake_ssh_channel_free = MagicMock()
    channel = patched_channel("<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_new", lambda *_: None)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.open()
    assert channel._channel is None
    fake_ssh_channel_free.assert_not_called()


def test_channel_open_ssh_channel_open_session_error(monkeypatch, patched_channel):

    fake_ssh_channel_free = MagicMock()
    channel = patched_channel("<session object>")
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_open_session", lambda *_: -1)
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.open()
    assert channel._channel is None
    fake_ssh_channel_free.assert_called_once_with("<channel object>")


def test_channel_close(monkeypatch, patched_channel):

    fake_ssh_channel_free = MagicMock(return_value=pystassh.api.SSH_OK)
    channel = patched_channel("<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr("pystassh.channel.Channel._is_open", lambda *_: False)

    channel._channel = "<channel object>"
    channel.close()
    assert channel._channel is None
    fake_ssh_channel_free.assert_not_called()

    monkeypatch.setattr("pystassh.channel.Channel._is_open", lambda *_: True)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_send_eof", lambda *_: pystassh.api.SSH_OK
    )
    channel._channel = "<channel object>"
    channel.close()
    assert channel._channel is None
    fake_ssh_channel_free.assert_called_once_with("<channel object>")


def test_channel_with_block(monkeypatch, patched_channel):
    def fake_open(self):
        self._channel = "<channel object>"

    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )
    monkeypatch.setattr("pystassh.channel.Channel.open", fake_open)
    monkeypatch.setattr("pystassh.channel.Channel.close", lambda _: None)

    with patched_channel("<session object>") as channel:
        assert channel._is_open()


def test_channel_execute(monkeypatch, patched_channel):
    def fake_result_init(self, channel, command):
        self._channel = channel
        self._command = command

    monkeypatch.setattr("pystassh.channel.Channel.open", lambda _: None)
    monkeypatch.setattr("pystassh.channel.Channel.close", lambda _: None)
    channel = patched_channel("<sesion object>")

    monkeypatch.setattr("pystassh.api.Api.ssh_channel_request_exec", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.execute("ls")

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_exec", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr("pystassh.result.Result.__init__", fake_result_init)

    res = channel.execute("ls")
    assert isinstance(res, pystassh.result.Result)
    assert res._command == "ls"
    assert res._channel == channel._channel


def test_channel_request_shell_error(monkeypatch, patched_channel):

    import pystassh.api
    import pystassh.exceptions

    channel = patched_channel("<session object>")
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.request_shell()

    assert channel._channel is None
    assert str(err.value) == "The channel is not open."

    channel.open()
    assert channel._channel is not None

    monkeypatch.setattr("pystassh.api.Api.ssh_channel_request_pty", lambda *_: -1)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_request_shell", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.request_shell()

    assert str(err.value).startswith("Request a shell failed:")

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.request_shell(request_pty=True)

    assert str(err.value).startswith("Request a pseudo-TTY failed:")


def test_channel_read_write_error_on_closed_channel(monkeypatch, patched_channel):

    import pystassh.api
    import pystassh.exceptions

    channel = patched_channel("<session object>")
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.read(1)

    assert str(err.value) == "The channel is not open."

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.read_nonblocking(1)

    assert str(err.value) == "The channel is not open."

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.write("")

    assert str(err.value) == "The channel is not open."

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.is_eof()

    assert str(err.value) == "The channel is not open."


def test_channel_read_write_error_without_shell(monkeypatch, patched_channel):

    import pystassh.api
    import pystassh.exceptions

    channel = patched_channel("<session object>")
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    # we open a channel but we don't request a shell
    channel.open()

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.read(1)

    assert str(err.value) == "No shell was requested for this channel."

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.read_nonblocking(1)

    assert str(err.value) == "No shell was requested for this channel."

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.write("")

    assert str(err.value) == "No shell was requested for this channel."


def test_channel_read_write_error(monkeypatch, patched_channel):

    import pystassh.api
    import pystassh.exceptions

    channel = patched_channel("<session object>")
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_shell", lambda *_: pystassh.api.SSH_OK
    )

    # we open a channel and request a shell
    channel.open()
    channel.request_shell()

    # make the read/write calls to fail
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_read", lambda *_: pystassh.api.SSH_ERROR
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_read_nonblocking",
        lambda *_: pystassh.api.SSH_ERROR,
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_write", lambda *_: pystassh.api.SSH_ERROR
    )
    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.read(1)

    assert str(err.value) == "Read failed: <error message>"

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.read_nonblocking(1)

    assert str(err.value) == "Read failed: <error message>"

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.write("")

    assert str(err.value) == "Write failed: <error message>"


def test_channel_read_write(monkeypatch, patched_channel):

    import pystassh.api
    import pystassh.exceptions

    channel = patched_channel("<session object>")
    monkeypatch.setattr("pystassh.api.Api.new_chars", lambda sz: [0] * sz)
    monkeypatch.setattr("pystassh.api.Api.to_string", lambda buf: buf[0])
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", lambda *_: "<channel object>"
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_shell", lambda *_: pystassh.api.SSH_OK
    )

    def _fake_read(ch, buf, sz, stderr):
        sz = len(buf)
        buf[0] = "<read {} bytes from {}>".format(sz, ch)
        import pystassh.api

        return pystassh.api.SSH_OK

    _fake_write = MagicMock()

    # we open a channel and request a shell
    channel.open()
    channel.request_shell()

    # make the read/write calls to succeed
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_read", _fake_read)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_read_nonblocking", _fake_read)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_write", _fake_write)

    assert channel.read(1) == "<read 1 bytes from <channel object>>"
    assert channel.read(42) == "<read 42 bytes from <channel object>>"
    assert channel.read_nonblocking(33) == "<read 33 bytes from <channel object>>"

    channel.write("foo")
    _fake_write.assert_called_once_with("<channel object>", b"foo", 3)


def test_channel_get_error_message_error(monkeypatch, patched_channel):
    def fake_get_error_message(_):
        raise pystassh.exceptions.UnknownException

    monkeypatch.setattr("pystassh.api.Api.get_error_message", fake_get_error_message)
    channel = patched_channel("<session object>")
    assert channel.get_error_message() == "<error message irrecoverable>"
