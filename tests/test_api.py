# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock


@pytest.fixture
def patched_api(monkeypatch):

    mock = MagicMock()
    del mock.i_dont_exist
    monkeypatch.setattr("ctypes.util.find_library", lambda _: "libssh.so.42")
    monkeypatch.setattr("cffi.FFI.dlopen", lambda *_: mock)

    from pystassh import api
    return api


@pytest.fixture
def patched_init_api(monkeypatch):

    monkeypatch.setattr("ctypes.util.find_library", lambda _: None)
    from pystassh.api import _init_api
    return _init_api


def test_api_getattr(patched_api):

    with pytest.raises(AttributeError):
        patched_api.Api.i_dont_exist()

    assert patched_api.Api.ssh_channel_open_session is patched_api.Api.lib.ssh_channel_open_session


def test_init_api(monkeypatch, patched_api):

    import pystassh.exceptions

    monkeypatch.setattr("ctypes.util.find_library", lambda _: None)

    with pytest.raises(pystassh.exceptions.PystasshException):
        patched_api._init_api()


def test_api_to_string(monkeypatch, patched_api):
    monkeypatch.setattr("pystassh.api.Api.ffi.string", lambda s: s)
    assert patched_api.Api.to_string(b'foo') == b'foo'


def test_api_new_chars(monkeypatch, patched_api):
    monkeypatch.setattr("pystassh.api.Api.ffi.new", lambda s: b'   ')
    assert patched_api.Api.new_chars(3) == b'   '


def test_api_get_error_message(monkeypatch, patched_api):

    import pystassh.exceptions

    def fake_get_error_message(_):
        raise ValueError()

    monkeypatch.setattr("pystassh.api.Api.ssh_get_error", fake_get_error_message)
    with pytest.raises(pystassh.exceptions.UnknownException):
        patched_api.Api.get_error_message("<session object>")