#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" setup.py for ansible-role
"""
import os
import sys
from setuptools import setup

# make sure that finding packages works, even
# when setup.py is invoked from outside this dir
this_dir = os.path.dirname(os.path.abspath(__file__))
if not os.getcwd() == this_dir:
    os.chdir(this_dir)

# make sure we can import the version number so that it doesn't have
# to be changed in two places. ymir/__init__.py is also free
# to import various requirements that haven't been installed yet
sys.path.append(os.path.join(this_dir, 'ansible_role'))
from version import __version__ as release_version  # flake8: noqa
sys.path.pop()

base_url = 'https://github.com/mattvonrocketstein/ansible-role-apply/'

setup(
    name='ansible-role',
    version=release_version,
    license='apache',
    description='The missing "ansible-role" command',
    long_description=(
        'The missing "ansible-role" command: downloads, '
        'installs, and cleans temporary ansible roles without '
        'the need for manually editing ansible playbooks'),
    author='mattvonrocketstein',
    author_email='$author@gmail',
    url=base_url,
    download_url=base_url + '/tarball/master',
    packages=['ansible_role'],
    keywords=['ansible', 'role', 'devops'],
    entry_points={
        'console_scripts':
        ['ansible-role = ansible_role:entry', ]},
    install_requires=[
        'shellescape==3.4.1',
        "Fabric",
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    zip_safe=False,
)
