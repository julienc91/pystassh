# -*- coding: utf-8 -*-

from unittest.mock import Mock

from pystassh.result import Result


def test_result_init(monkeypatch):
    monkeypatch.setattr(
        "pystassh.result.Result._read_stdout_or_stderr",
        lambda _, b: b"bar\n" if b else b"foo\n",
    )
    monkeypatch.setattr("pystassh.result.Result._read_return_code", lambda _: 0)

    result = Result("<channel object>", "ls")
    assert result._channel == "<channel object>"
    assert result._command == "ls"
    assert result._stdout == b"foo\n"
    assert result._stderr == b"bar\n"


def test_result_properties(monkeypatch):

    monkeypatch.setattr(
        "pystassh.result.Result._read_stdout_or_stderr",
        lambda _, b: b"bar\n" if b else b"foo\n",
    )
    monkeypatch.setattr("pystassh.result.Result._read_return_code", lambda _: 17)

    result = Result("<channel object>", "ls")
    assert result.stdout == "foo"
    assert result.raw_stdout == b"foo\n"
    assert result.stderr == "bar"
    assert result.raw_stderr == b"bar\n"
    assert result.return_code == 17
    assert result.command == "ls"


def test_result_read_return_code(monkeypatch):

    monkeypatch.setattr("pystassh.result.Result._read_stdout_or_stderr", lambda *_: b"")
    monkeypatch.setattr("pystassh.api.Api.ssh_channel_get_exit_status", lambda _: 17)

    result = Result("<channel object>", "ls")
    assert result._return_code == 17


def test_result_read_stdout_or_stderr(monkeypatch):
    monkeypatch.setattr(
        "pystassh.result.Result._read_return_code", Mock(return_value=17)
    )
    monkeypatch.setattr(
        "pystassh.api.Api.ssh_channel_read", Mock(side_effect=[3, 0, 0])
    )

    result = Result("<channel object>", "ls")
    assert result._stdout == b""
