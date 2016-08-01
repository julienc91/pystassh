# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock


@pytest.fixture
def patched_result(monkeypatch):
    monkeypatch.setattr("ctypes.util.find_library", lambda _: "libssh.so.42")
    monkeypatch.setattr("cffi.FFI.dlopen", lambda *_: MagicMock())
    monkeypatch.setattr("pystassh.api.Api.to_string", lambda chars: chars)
    monkeypatch.setattr("pystassh.api.Api.ssh_get_error", lambda *_: "<error message>")

    from pystassh.result import Result
    return Result


def test_result_init(monkeypatch, patched_result):

    monkeypatch.setattr("pystassh.result.Result._read_stdout_or_stderr", lambda _, b: b"bar\n" if b else b"foo\n")
    monkeypatch.setattr("pystassh.result.Result._read_return_code", lambda _: 0)

    result = patched_result("<channel object>", "ls")
    assert result._channel == "<channel object>"
    assert result._command == "ls"
    assert result._stdout == b"foo\n"
    assert result._stderr == b"bar\n"


def test_result_properties(monkeypatch, patched_result):

    monkeypatch.setattr("pystassh.result.Result._read_stdout_or_stderr", lambda _, b: b"bar\n" if b else b"foo\n")
    monkeypatch.setattr("pystassh.result.Result._read_return_code", lambda _: 17)

    result = patched_result("<channel object>", "ls")
    assert result.stdout == "foo"
    assert result.raw_stdout == b"foo\n"
    assert result.stderr == "bar"
    assert result.raw_stderr == b"bar\n"
    assert result.return_code == 17
    assert result.command == "ls"


def test_result_read_return_code(monkeypatch, patched_result):

    monkeypatch.setattr("pystassh.result.Result._read_stdout_or_stderr", lambda *_: b"")
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_get_exit_status", lambda _: 17)

    result = patched_result("<channel object>", "ls")
    assert result._return_code == 17


def test_result_read_stdout_or_stderr(monkeypatch, patched_result):

    def fake_ssh_channel_read(*_):
        if fake_ssh_channel_read.nb_loops == 3:
            return 0
        fake_ssh_channel_read.nb_loops += 1
        return 3
    fake_ssh_channel_read.nb_loops = 0

    monkeypatch.setattr("pystassh.result.Result._read_return_code", lambda _: 17)
    monkeypatch.setattr("pystassh.api.Api.new_chars", lambda _: b"foo")
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_read", fake_ssh_channel_read)

    result = patched_result("<channel object>", "ls")
    assert result._stdout == b"foofoofoo"
