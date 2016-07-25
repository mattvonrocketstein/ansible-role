# -*- coding: utf-8 -*-
""" tests.test_ansible
"""

import json
import mock
import pytest
from fabric import api


def test_help():
    with api.settings(warn_only=True):
        assert api.local("ansible-role-apply --help").succeeded


def test_simple_invocation_with_failure():
    with api.settings(warn_only=True):
        assert api.local("ansible-role-apply role.doesnotexist").failed
