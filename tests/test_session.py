# -*- coding: utf-8 -*-

import gc
from unittest.mock import MagicMock

import cffi
import pytest

import pystassh.api
import pystassh.exceptions
from pystassh import Session


def test_session_init():
    session = Session("foo", "bar", "baz", "qux", 17, "filename")
    assert session._hostname == b"foo"
    assert session._username == b"bar"
    assert session._password == b"baz"
    assert session._passphrase == b"qux"
    assert session._port == b"17"
    assert session._privkey_file == b"filename"


def test_session_is_connected(monkeypatch):

    session = Session()
    assert session.is_connected() is False

    session._session = "<session object>"
    monkeypatch.setattr("pystassh.api.Api.ssh_is_connected", lambda *_: 0)
    assert session.is_connected() is False

    monkeypatch.setattr("pystassh.api.Api.ssh_is_connected", lambda *_: 1)
    assert session.is_connected() is True

    session._session = None
    assert session.is_connected() is False


def test_session_connect(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr("pystassh.api.Api.ssh_disconnect", lambda *_: None)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_userauth_password",
        lambda *_: pystassh.api.SSH_AUTH_SUCCESS,
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_userauth_autopubkey",
        lambda *_: pystassh.api.SSH_AUTH_SUCCESS,
    )
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    session.connect()
    assert session._session == "<session object>"
    fake_ssh_free.assert_not_called()

    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<new session object>")
    session.connect()
    assert session._session == "<session object>"
    session._session = None
    fake_ssh_free.assert_not_called()

    session.connect()
    assert session._session == "<new session object>"
    fake_ssh_free.assert_not_called()


def test_session_connect_ssh_new_error(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: None)
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_not_called()


def test_session_connect_ssh_options_set_error(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set",
        lambda *_: -1 if _[1] == pystassh.api.SSH_OPTIONS_HOST else pystassh.api.SSH_OK,
    )
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")
    fake_ssh_free.reset_mock()

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set",
        lambda *_: -1
        if _[1] == pystassh.api.SSH_OPTIONS_PORT_STR
        else pystassh.api.SSH_OK,
    )
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")
    fake_ssh_free.reset_mock()

    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set",
        lambda *_: -1 if _[1] == pystassh.api.SSH_OPTIONS_USER else pystassh.api.SSH_OK,
    )
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")
    fake_ssh_free.reset_mock()


def test_session_connect_ssh_connect_error(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.ConnectionException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")


def test_session_connect_ssh_userauth_password_error(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session(username="foo", password="bar")
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_password", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")


def test_session_connect_ssh_userauth_privkey_error(monkeypatch):
    def _fake_ssh_pki_import_privkey_file(filename, passphrase, _a, _b, pkey):
        pkey[0] = cffi.FFI().new(
            "char[]",
            ("<key object from {} with pass {}>".format(filename, passphrase)).encode(),
        )
        return pystassh.api.SSH_OK

    fake_ssh_free = MagicMock()
    fake_ssh_key_free = MagicMock()
    session = Session(privkey_file="filename")
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    # mock the load of a private key without passphrase
    # monkeypatch.setattr("pystassh.api.Api.new_key_pointer", lambda: ["null"])
    monkeypatch.setattr("pystassh.api.Api.ssh_key_free", fake_ssh_key_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_pki_import_privkey_file",
        _fake_ssh_pki_import_privkey_file,
    )

    # make the authentication to fail
    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_publickey", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")
    fake_ssh_key_free.assert_called_once()

    fake_ssh_free.reset_mock()
    fake_ssh_key_free.reset_mock()

    # same but with a passphrase
    session = Session(privkey_file="filename", passphrase="pystassh rocks!")
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")
    fake_ssh_key_free.assert_called_once()

    fake_ssh_free.reset_mock()
    fake_ssh_key_free.reset_mock()

    # same but now it is the load of the private key which fails
    monkeypatch.setattr("pystassh.api.Api.ssh_pki_import_privkey_file", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")
    fake_ssh_key_free.assert_not_called()


def test_session_connect_ssh_userauth_autopubkey_error(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    monkeypatch.setattr("pystassh.api.Api.ssh_new", lambda *_: "<session object>")
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_options_set", lambda *_: pystassh.api.SSH_OK
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_connect", lambda *_: pystassh.api.SSH_OK)
    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )

    monkeypatch.setattr("pystassh.api.Api.ssh_userauth_autopubkey", lambda *_: -1)
    with pytest.raises(pystassh.exceptions.AuthenticationException):
        session.connect()
    assert session._session is None
    assert session.channel is None
    fake_ssh_free.assert_called_once_with("<session object>")


def test_session_disconnect(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    channel = MagicMock()
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda *_: False)

    session._session = "<session object>"
    session._channel = channel
    session.disconnect()
    assert session._session is None
    assert session.channel is None
    channel.close.assert_not_called()
    fake_ssh_free.assert_not_called()

    channel.reset_mock()
    fake_ssh_free.reset_mock()

    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda *_: True)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_disconnect", lambda *_: pystassh.api.SSH_OK
    )
    session._session = "<session object>"
    session._channel = channel
    session.disconnect()
    assert session._session is None
    assert session.channel is None
    channel.close.assert_called_once_with()
    fake_ssh_free.assert_called_once_with("<session object>")


def test_session_del(monkeypatch):
    fake_ssh_free = MagicMock()
    session = Session()
    channel = MagicMock()
    monkeypatch.setattr("pystassh.api.Api.ssh_free", fake_ssh_free)
    monkeypatch.setattr("pystassh.session.Session.is_connected", lambda *_: True)
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_disconnect", lambda *_: pystassh.api.SSH_OK
    )

    session._session = "<session object>"
    session._channel = channel

    # If this is the only reference to the session object, after
    # the 'del' the object should be garbage-collected and automatically
    # disconnect. To be sure, we call GC explicitly.
    del session
    gc.collect()

    channel.close.assert_called_once_with()
    fake_ssh_free.assert_called_once_with("<session object>")


def test_session_with_block(monkeypatch):
    def fake_connect(self):
        self._session = "<session object>"

    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )
    monkeypatch.setattr("pystassh.session.Session.connect", fake_connect)
    monkeypatch.setattr("pystassh.session.Session.disconnect", lambda _: None)

    with Session() as session:
        assert session.is_connected()


def test_session_execute(monkeypatch):
    session = Session()
    with pytest.raises(pystassh.exceptions.PystasshException):
        session.execute("ls")

    monkeypatch.setattr(
        "pystassh.session.Session.is_connected", lambda self: bool(self._session)
    )
    monkeypatch.setattr(
        "pystassh.channel.Channel.execute",
        lambda _, command: "<result of {}>".format(command),
    )
    monkeypatch.setattr("pystassh.api.Api.ssh_disconnect", lambda *_: None)
    monkeypatch.setattr("pystassh.api.Api.ssh_free", lambda *_: None)

    session._session = "<session object>"
    session._channel = pystassh.channel.Channel(session._session)
    assert session.execute("ls") == "<result of ls>"


def test_session_get_error_message_error(monkeypatch):
    def fake_get_error_message(_):
        raise pystassh.exceptions.UnknownException

    monkeypatch.setattr("pystassh.api.Api.get_error_message", fake_get_error_message)
    session = Session()
    assert session.get_error_message() == "<error message irrecoverable>"
