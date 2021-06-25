# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


current_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_directory, "README.md")) as f:
    long_description = f.read()

setup(
    name="pystassh",
    version="1.1.0",
    author="Julien Chaumont",
    author_email="pystassh@julienc.io",
    description="An easy to use libssh wrapper to execute commands on a remote server via SSH with Python",
    license="MIT",
    url="https://julienc91.github.io/pystassh/",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["cffi"],
)
