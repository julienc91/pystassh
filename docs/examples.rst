========
Examples
========

Running simple commands:

    >>> from pystassh import Session
    >>> with Session('remote_host.org', username='foo', password='baz') as ssh_session:
    ...     res = ssh_session.execute('whoami')
    >>> res.stdout
    'foo'

Handling errors:

    >>> from pystassh import Session
    >>> with Session('remote_host.org', username='foo', password='baz') as ssh_session:
    ...     res = ssh_session.execute('whoam')
    >>> res.stderr
    'bash: whoam : command not found'

Running multiple commands:

    >>> from pystassh import Session
    >>> with Session('remote_host.org', username='foo', password='baz') as ssh_session:
    ...     ssh_session.execute('echo "bar" > /tmp/foo')
    ...     res = ssh_session.execute('cat /tmp/foo')
    >>> res.stdout
    'bar'

Use a session without a ``with`` block:

    >>> from pystassh import Session
    >>> ssh_session = Session('remote_host.org', username='foo', password='baz')
    >>> ssh_session.connect()
    >>> res = ssh_session.execute('whoami')
    >>> res.stdout
    'foo'
    >>> ssh_session.disconnect()
