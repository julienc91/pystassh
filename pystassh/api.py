# -*- coding: utf-8 -*-

import ctypes.util
import os

from cffi import FFI

from . import exceptions

SSH_OK = 0
SSH_ERROR = -1
SSH_AUTH_SUCCESS = 0

SSH_OPTIONS_HOST = 0
SSH_OPTIONS_PORT_STR = 2
SSH_OPTIONS_USER = 4


def _init_api():

    lib_name = ctypes.util.find_library("ssh")
    if not lib_name and not os.environ.get("READTHEDOCS"):
        raise exceptions.PystasshException(
            "libssh not found, please visit https://www.libssh.org/get-it/"
        )

    ffi = FFI()
    lib = ffi.dlopen(lib_name)
    ffi.cdef(
        """
        void* ssh_new();
        int ssh_free(void*);
        int ssh_options_set(void*, int, char*);
        int ssh_connect(void*);
        int ssh_disconnect(void*);
        int ssh_is_connected(void*);
        char* ssh_get_error(void*);

        int ssh_userauth_password(void*, char*, char*);
        int ssh_userauth_autopubkey(void*, char*);
        int ssh_userauth_publickey(void*, const char*, const void*);

        int ssh_pki_import_privkey_file(const char*, const char*, void*, void*, void**);
        void ssh_key_free(void*);

        void* ssh_channel_new(void*);
        int ssh_channel_open_session(void*);
        int ssh_channel_is_open(void*);
        void ssh_channel_free(void*);
        int ssh_channel_request_exec(void*, char*);
        int ssh_channel_request_pty(void*);
        int ssh_channel_request_shell(void*);

        int ssh_channel_get_exit_status(void*);
        int ssh_channel_read(void*, char*, int, int);
        int ssh_channel_send_eof(void*);
        int ssh_channel_is_eof(void*);
        int ssh_channel_write(void*, const void*, uint32_t);
        int ssh_channel_read_nonblocking(void*, void*, uint32_t, int);
    """
    )
    return ffi, lib


class ApiMetaclass(type):
    def __getattr__(cls, name):
        if hasattr(cls.lib, name):
            return getattr(cls.lib, name)
        raise AttributeError("Api has no attribute {}".format(name))


class Api(metaclass=ApiMetaclass):

    ffi, lib = _init_api()
    NULL = ffi.NULL

    @classmethod
    def to_string(cls, chars):
        return cls.ffi.string(chars)

    @classmethod
    def new_chars(cls, size):
        return cls.ffi.new("char[{}]".format(size))

    @classmethod
    def new_key_pointer(cls):
        return cls.ffi.new("void**")

    @classmethod
    def get_error_message(cls, session):
        try:
            raw_error = cls.ssh_get_error(session)
        except (TypeError, ValueError, AttributeError):
            raise exceptions.UnknownException("Error message irrecoverable")
        return cls.to_string(raw_error)
