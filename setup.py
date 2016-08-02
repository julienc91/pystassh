# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="pystassh",
    version="1.0.1",
    author="Julien Chaumont",
    author_email="pystassh@julienc.io",
    description="An easy to use libssh wrapper to execute commands on a remote server via SSH with Python",
    license="MIT",
    url="https://julienc91.github.io/pystassh/",
    packages=find_packages(),
    install_requires=["cffi"],
    setup_requires=['pytest-runner'],
    tests_require=["pytest", "pytest-cov", "mock"]
)
