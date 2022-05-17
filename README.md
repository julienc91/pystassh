![Build](https://github.com/julienc91/pystassh/actions/workflows/main.yml/badge.svg)
[![codecov](https://codecov.io/gh/julienc91/pystassh/branch/main/graph/badge.svg?token=yI3VdGc0rZ)](https://codecov.io/gh/julienc91/pystassh)
[![Documentation](https://readthedocs.org/projects/pystassh/badge/)](http://pystassh.readthedocs.org/en/latest/)

pystassh
========

An easy to use libssh wrapper to execute commands on a remote server via SSH with Python.

* Author: Julien CHAUMONT (https://julienc.io)
* Version: 1.2.2
* Date: 2022-05-17
* Licence: MIT
* Url: https://julienc91.github.io/pystassh/

Installation
------------

Just use `pip` to install the package:

    pip install pystassh
    
`pystassh` is working with python 3+ and pypy.

Requirements
------------

`pystassh` is using libssh to work, you will have to install the library before using
`pystassh`. Only version 0.7.3 was used during the development, but versions 0.5 and above should work fine as well with `pystassh`.
Visit [libssh's official website](https://www.libssh.org/get-it/) for more information.
`libffi-dev` is also required by the `cffi` module.

On Debian and Ubuntu:

    apt-get install libssh-4 libffi-dev
    
On Fedora:

    dnf install libssh libffi-devel

Examples
--------

Establishing a connection:

```python
>>> from pystassh import Session
>>> # With default private key
>>> session = Session('remote_host.org', username='user')
>>> # With username and password
>>> session = Session('remote_host.org', username='foo', password='bar')
>>> # With specific private key and a passphrase
>>> session = Session('remote_host.org', privkey_file='/home/user/.ssh/my_key', passphrase='baz')
```

Running simple commands:

```python
>>> from pystassh import Session
>>> with Session('remote_host.org', username='user') as ssh_session:
...     res = ssh_session.execute('whoami')
>>> res.stdout
'foo'
```
    
Handling errors:

```python
>>> from pystassh import Session
>>> with Session('remote_host.org', username='user') as ssh_session:
...     res = ssh_session.execute('whoam')
>>> res.stderr
'bash: whoam : command not found'
```

Running multiple commands:

```python
>>> from pystassh import Session
>>> with Session('remote_host.org', username='user') as ssh_session:
...     ssh_session.execute('echo "bar" > /tmp/foo')
...     res = ssh_session.execute('cat /tmp/foo')
>>> res.stdout
'bar'
```
    
Using a session without a `with` block:

```python
>>> from pystassh import Session
>>> ssh_session = Session('remote_host.org', username='user')
>>> ssh_session.connect()
>>> res = ssh_session.execute('whoami')
>>> res.stdout
'foo'
>>> ssh_session.disconnect()
```

Using a shell:

```python
>>> from pystassh import Session
>>> with Session('remote_host.org', username='user') as ssh_session:
...     channel = ssh_session.channel
...     with channel:
...         channel.request_shell(request_pty=False)
...         # non blocking read to flush the motd, if there is one
...         channel.read_nonblocking(1024)
...         channel.write("export foo=42;\n")
...         channel.write("echo $foo;\n")
...         channel.read(2048)
b'42\n'
```

Documentation
-------------

The complete documentation is available at: http://pystassh.readthedocs.org/en/latest/
