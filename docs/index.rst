.. pystassh documentation master file, created by
   sphinx-quickstart on Mon Aug  1 20:53:15 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

========
pystassh
========

An easy to use libssh wrapper to execute commands on a remote server via SSH with Python.

You can go straight to the API documentation here: :ref:`ref_api`.

Description
===========

``pystassh`` is a Python 3 library that allows you to easily run commands on a remote server via SSH.


Compatibility
=============

Currently supported versions and implementations of Python are:

* python 3.3
* python 3.4
* python 3.5
* pypy3

Others might be compatible but are not officially supported.


Requirements
============

Required libraries are automatically installed when installing ``pystassh`` (see :ref:install to learn more).
In its current version, ``pystassh`` requires ``cffi``additional libraries to interact with ``libssh`` and to run the tests and build the documentation:

* cffi 1.7.0
* pytest 2.9.1
* pytest-cov-2.2.1
* Sphinx 1.4.1
* sphinx-autobuild 0.6.0

``libssh`` and ``libffi-dev`` may have to be installed separately.


Documentation
=============

Refer to other sections of this documentation to learn more about ``pystassh``.

.. toctree::
   :maxdepth: 3

   installation
   examples
   tests
   ref_api
   about