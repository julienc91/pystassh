=====
Tests
=====

Each release of ``pystassh`` is garantied to be delivered with a complete set of unit tests
that cover the entirety of the code. Of course, it cannot be the assurance of a completely
devoid of bug source code; but that's something at least, right?

Tu run the tests, clone the GitHub repository (see :ref:`installation_from_sources`), then run::

    $ python setup.py test

The test suite requires `pytest <http://pytest.org/latest/getting-started.html>`_ to run but will automatically
be installed by running the previous command.
It is still possible to run the tests directly from pytest with::

    $ py.test

Code coverage can also be tested with the `pytest-cov <https://pypi.python.org/pypi/pytest-cov>` package this way::

    $ py.test --cov pystassh
