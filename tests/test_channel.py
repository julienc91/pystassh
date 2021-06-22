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

    import pystassh.api
    import pystassh.exceptions

    channel = Channel(session)
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


def test_channel_get_error_message_error(monkeypatch, session):
    monkeypatch.setattr(
        "pystassh.api.Api.get_error_message",
        Mock(side_effect=pystassh.exceptions.UnknownException),
    )
    channel = Channel(session)
    assert channel.get_error_message() == "<error message irrecoverable>"
