# -*- coding: utf-8 -*-

from unittest.mock import Mock

import cffi.model
import pytest

import pystassh.api
import pystassh.exceptions


def test_api_getattr():

    with pytest.raises(AttributeError):
        pystassh.api.Api.i_dont_exist()

    assert (
        pystassh.api.Api.ssh_channel_open_session
        is pystassh.api.Api.lib.ssh_channel_open_session
    )


def test_init_api(monkeypatch):
    monkeypatch.setattr("ctypes.util.find_library", Mock(return_value=None))

    with pytest.raises(pystassh.exceptions.PystasshException):
        pystassh.api._init_api()


def test_api_to_string(monkeypatch):
    s = cffi.FFI().new("char[]", b"foo")
    assert pystassh.api.Api.to_string(s) == b"foo"


def test_api_get_error_message(monkeypatch):
    monkeypatch.setattr("pystassh.api.Api.ssh_get_error", Mock(side_effect=ValueError))
    with pytest.raises(pystassh.exceptions.UnknownException):
        pystassh.api.Api.get_error_message("<session object>")

    error = cffi.FFI().new("char[]", b"foo")
    monkeypatch.setattr("pystassh.api.Api.ssh_get_error", Mock(return_value=error))
    assert pystassh.api.Api.get_error_message("<session object>") == b"foo"
