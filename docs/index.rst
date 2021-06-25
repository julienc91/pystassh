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

* python 3.6+
* pypy3

Others might be compatible but are not officially supported.


Requirements
============

Required libraries are automatically installed when installing ``pystassh`` (see :ref:`install` to learn more).
You can install them by running ``pip install -r requirements.txt``.

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
