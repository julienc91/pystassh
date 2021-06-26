# -*- coding: utf-8 -*-

from unittest.mock import Mock

import pytest

import pystassh.api
import pystassh.exceptions
import pystassh.result
from pystassh.channel import Channel
from pystassh.session import Session


@pytest.fixture()
def session():
    return Session("example.com")


def test_channel_is_open(monkeypatch, session):
    channel = Channel(session)
    assert channel._is_open() is False

    channel._channel = "<channel object>"
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_is_open", Mock(return_value=0))
    assert channel._is_open() is False

    monkeypatch.setattr("pystassh.api.Api.ssh_channel_is_open", Mock(return_value=1))
    assert channel._is_open() is True

    channel._channel = None
    assert channel._is_open() is False


def test_channel_open(monkeypatch, session):
    fake_ssh_channel_free = Mock()
    channel = Channel(session)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session",
        Mock(return_value=pystassh.api.SSH_OK),
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


def test_channel_open_ssh_channel_new_error(monkeypatch, session):
    fake_ssh_channel_free = Mock()
    channel = Channel(session)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_new", Mock(return_value=None))
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.open()
    assert channel._channel is None
    fake_ssh_channel_free.assert_not_called()


def test_channel_open_ssh_channel_open_session_error(monkeypatch, session):
    fake_ssh_channel_free = Mock()
    channel = Channel(session)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session", Mock(return_value=-1)
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.open()
    assert channel._channel is None
    fake_ssh_channel_free.assert_called_once_with("<channel object>")


def test_channel_close(monkeypatch, session):
    fake_ssh_channel_free = Mock(return_value=pystassh.api.SSH_OK)
    channel = Channel(session)
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_free", fake_ssh_channel_free)
    monkeypatch.setattr("pystassh.channel.Channel._is_open", Mock(return_value=False))

    channel._channel = "<channel object>"
    channel.close()
    assert channel._channel is None
    fake_ssh_channel_free.assert_not_called()

    monkeypatch.setattr("pystassh.channel.Channel._is_open", Mock(return_value=True))
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_send_eof", Mock(return_value=pystassh.api.SSH_OK)
    )
    channel._channel = "<channel object>"
    channel.close()
    assert channel._channel is None
    fake_ssh_channel_free.assert_called_once_with("<channel object>")


def test_channel_with_block(monkeypatch, session):
    def fake_open(self):
        self._channel = "<channel object>"

    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )
    monkeypatch.setattr("pystassh.channel.Channel.open", fake_open)
    monkeypatch.setattr("pystassh.channel.Channel.close", Mock())

    with Channel(session) as channel:
        assert channel._is_open()


def test_channel_execute(monkeypatch, session):
    def fake_result_init(self, channel, command):
        self._channel = channel
        self._command = command

    monkeypatch.setattr("pystassh.channel.Channel.open", Mock())
    monkeypatch.setattr("pystassh.channel.Channel.close", Mock())
    channel = Channel(session)

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_exec", Mock(return_value=-1)
    )
    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.execute("ls")

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_exec",
        Mock(return_value=pystassh.api.SSH_OK),
    )
    monkeypatch.setattr("pystassh.result.Result.__init__", fake_result_init)

    res = channel.execute("ls")
    assert isinstance(res, pystassh.result.Result)
    assert res._command == "ls"
    assert res._channel == channel._channel


def test_channel_request_shell_error(monkeypatch, session):
    channel = Channel(session)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session",
        Mock(return_value=pystassh.api.SSH_OK),
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

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_pty",
        Mock(return_value=pystassh.api.SSH_ERROR),
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_shell",
        Mock(return_value=pystassh.api.SSH_ERROR),
    )
    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.request_shell()

    assert str(err.value).startswith("Request a shell failed:")

    with pytest.raises(pystassh.exceptions.ChannelException) as err:
        channel.request_shell(request_pty=True)

    assert str(err.value).startswith("Request a pseudo-TTY failed:")


@pytest.mark.parametrize("read_method", ["read", "read_nonblocking"])
def test_channel_read_write_error_on_closed_channel(monkeypatch, session, read_method):
    channel = Channel(session)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session",
        Mock(return_value=pystassh.api.SSH_OK),
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    with pytest.raises(ValueError):
        getattr(channel, read_method)(-1)

    with pytest.raises(
        pystassh.exceptions.ChannelException, match="The channel is not open"
    ):
        getattr(channel, read_method)(1)

    with pytest.raises(
        pystassh.exceptions.ChannelException, match="The channel is not open"
    ):
        channel.write("")

    with pytest.raises(
        pystassh.exceptions.ChannelException, match="The channel is not open"
    ):
        channel.is_eof()


@pytest.mark.parametrize("read_method", ["read", "read_nonblocking"])
def test_channel_read_write_error_without_shell(monkeypatch, session, read_method):
    channel = Channel(session)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session",
        Mock(return_value=pystassh.api.SSH_OK),
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )

    # we open a channel but we don't request a shell
    channel.open()

    with pytest.raises(
        pystassh.exceptions.ChannelException,
        match="No shell was requested for this channel",
    ):
        getattr(channel, read_method)(1)

    with pytest.raises(
        pystassh.exceptions.ChannelException,
        match="No shell was requested for this channel",
    ):
        channel.write("")


@pytest.mark.parametrize("read_method", ["read", "read_nonblocking"])
def test_channel_read_write_error(monkeypatch, session, read_method):
    channel = Channel(session)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session",
        Mock(return_value=pystassh.api.SSH_OK),
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_shell",
        Mock(return_value=pystassh.api.SSH_OK),
    )

    # we open a channel and request a shell
    channel.open()
    channel.request_shell()

    # make the read/write calls to fail
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_{}".format(read_method),
        Mock(return_value=pystassh.api.SSH_ERROR),
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_write", Mock(return_value=pystassh.api.SSH_ERROR)
    )
    with pytest.raises(
        pystassh.exceptions.ChannelException,
        match="Read failed: <error message irrecoverable>",
    ):
        getattr(channel, read_method)(1)

    with pytest.raises(
        pystassh.exceptions.ChannelException,
        match="Write failed: <error message irrecoverable>",
    ):
        channel.write("")


@pytest.mark.parametrize("read_method", ["read", "read_nonblocking"])
def test_channel_read_write(monkeypatch, session, read_method):
    channel = Channel(session)
    monkeypatch.setattr("pystassh.api.Api.new_chars", lambda sz: [0] * sz)
    monkeypatch.setattr("pystassh.api.Api.to_string", lambda buf: buf[0])
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_new", Mock(return_value="<channel object>")
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_open_session",
        Mock(return_value=pystassh.api.SSH_OK),
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel._is_open", lambda self: bool(self._channel)
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_request_shell",
        Mock(return_value=pystassh.api.SSH_OK),
    )

    def _fake_read(ch, buf, sz, stderr):
        sz = len(buf)
        buf[0] = "<read {} bytes from {}>".format(sz, ch)
        import pystassh.api

        return pystassh.api.SSH_OK

    _fake_write = Mock()

    # we open a channel and request a shell
    channel.open()
    channel.request_shell()

    with pytest.raises(ValueError):
        channel.read(-3)

    # make the read/write calls to succeed
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_{}".format(read_method), _fake_read
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_write", _fake_write)

    assert getattr(channel, read_method)(1) == "<read 1 bytes from <channel object>>"
    assert getattr(channel, read_method)(42) == "<read 42 bytes from <channel object>>"

    channel.write("foo")
    _fake_write.assert_called_once_with("<channel object>", b"foo", 3)


def test_channel_is_eof(monkeypatch, session):
    channel = Channel(session)

    # channel is not open
    with pytest.raises(pystassh.exceptions.ChannelException):
        channel.is_eof()

    monkeypatch.setattr(channel, "_is_open", Mock(return_value=True))
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_is_eof", Mock(return_value=1))

    assert channel.is_eof()


def test_channel_get_error_message_error(monkeypatch, session):
    monkeypatch.setattr(
        "pystassh.api.Api.get_error_message",
        Mock(side_effect=pystassh.exceptions.UnknownException),
    )
    channel = Channel(session)
    assert channel.get_error_message() == "<error message irrecoverable>"
