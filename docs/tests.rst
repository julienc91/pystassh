=====
Tests
=====

Each release of ``pystassh`` is garantied to be delivered with a complete set of unit tests
that cover the entirety of the code. Of course, it cannot be the assurance of a completely
devoid of bug source code; but that's something at least, right?

Tu run the tests, clone the GitHub repository (see :ref:`installation_from_sources`) and install the dependencies::

    $ pip install requirements.txt

The run the test suite with:

    $ pytest .

Code coverage can also be tested with the `pytest-cov <https://pypi.python.org/pypi/pytest-cov>` package this way::

    $ pytest --cov pystassh
