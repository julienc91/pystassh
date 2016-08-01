# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock


@pytest.fixture
def patched_session(monkeypatch):

    monkeypatch.setattr("ctypes.util.find_library", lambda _: "libssh.so.42")
    monkeypatch.setattr("cffi.FFI.dlopen", lambda *_: MagicMock())
    monkeypatch.setattr("pystassh.api.Api.to_string", lambda chars: chars)
    monkeypatch.setattr("pystassh.api.Api.ssh_get_error", lambda *_: "<error message>")

    from pystassh import Session
    return Session


def test_session_init(patched_session):
    session = patched_session("foo", "bar", "baz", "qux", 17)
    assert session._hostname == b'foo'
    assert session._username == b'bar'
    assert session._password == b'baz'
    assert session._passphrase == b'qux'
    assert session._port == b'17'


def test_session_is_connected(monkeypatch, patched_session):

    session = patched_session()
    assert session.is_connected() is False

    session._session = "<session object>"
    monkeypatch.setattr("pystassh.api.Api.ssh_is_connected", lambda *_: 0)
    assert session.is_connected() is False

    monkeypatch.setattr("pystassh.api.Api.ssh_is_connected", lambda *_: 1)
    assert session.is_connected() is True

    session._session = None
    assert session.is_connected() is False


def test_session_connect(monkeypatch, patched_session):

    import pystassh.api
    session = patched_session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_password", lambda *_: pystassh.api.SSH_AUTH_SUCCESS)
    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_autopubkey", lambda *_: pystassh.api.SSH_AUTH_SUCCESS)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))

    session.connect()
    assert session._session == "<session object>"

    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<new session object>")
    session.connect()
    assert session._session == "<session object>"
    session._session = None

    session.connect()
    assert session._session == "<new session object>"


def test_session_connect_ssh_new_error(monkeypatch, patched_session):

    import pystassh.exceptions
    session = patched_session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: None)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))

    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None


def test_session_connect_ssh_options_set_error(monkeypatch, patched_session):

    import pystassh.api
    import pystassh.exceptions
    session = patched_session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))

    monkeypatch.setattr("pystassh.api.Api.ssh_options_set",
                        lambda *_: -1 if _[1] == pystassh.api.SSH_OPTIONS_HOST else pystassh.api.SSH_OK)
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None

    monkeypatch.setattr("pystassh.api.Api.ssh_options_set",
                        lambda *_: -1 if _[1] == pystassh.api.SSH_OPTIONS_PORT_STR else pystassh.api.SSH_OK)
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None

    monkeypatch.setattr("pystassh.api.Api.ssh_options_set",
                        lambda *_: -1 if _[1] == pystassh.api.SSH_OPTIONS_USER else pystassh.api.SSH_OK)
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None


def test_session_connect_ssh_connect_error(monkeypatch, patched_session):

    import pystassh.api
    import pystassh.exceptions
    session = patched_session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))

    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None


def test_session_connect_ssh_userauth_password_error(monkeypatch, patched_session):

    import pystassh.api
    import pystassh.exceptions
    session = patched_session(username="foo", password="bar")
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))

    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_password", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None


def test_session_connect_ssh_userauth_autopubkey_error(monkeypatch, patched_session):

    import pystassh.api
    import pystassh.exceptions
    session = patched_session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))

    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_autopubkey", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None


def test_session_disconnect(monkeypatch, patched_session):

    import pystassh.api
    session = patched_session()
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda *_: False)

    session._session = "<session object>"
    session.disconnect()
    assert session._session is None

    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda *_: True)
    monkeypatch.setattr("pystassh.api.Api.ssh_disconnect", lambda *_: pystassh.api.SSH_OK)
    session._session = "<session object>"
    session.disconnect()
    assert session._session is None


def test_session_with_block(monkeypatch, patched_session):

    def fake_connect(self):
        self._session = "<session object>"

    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))
    monkeypatch.setattr("pystassh.session.Session.connect", fake_connect)
    monkeypatch.setattr("pystassh.session.Session.disconnect", lambda _: None)

    with patched_session() as session:
        assert session.is_connected()


def test_session_execute(monkeypatch, patched_session):

    import pystassh.channel
    import pystassh.exceptions
    session = patched_session()
    with pytest.raises(pystassh.exceptions.PystasshException):
        session.execute("ls")

    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda self: bool(self._session))
    monkeypatch.setattr("pystassh.channel.Channel.execute", lambda _, command: "<result of {}>".format(command))

    session._session = "<session object>"
    session._channel = pystassh.channel.Channel(session._session)
    assert session.execute("ls") == "<result of ls>"


def test_session_get_error_message_error(monkeypatch, patched_session):

    import pystassh.exceptions

    def fake_get_error_message(_):
        raise pystassh.exceptions.UnknownException

    monkeypatch.setattr("pystassh.api.Api.get_error_message", fake_get_error_message)
    session = patched_session()
    assert session.get_error_message() == "<error message irrecoverable>"
