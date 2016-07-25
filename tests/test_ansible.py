# -*- coding: utf-8 -*-
""" tests.test_ansible
"""

import json
import mock
import pytest
from fabric import api


def test_basic():
    assert 1 == 1


def test_cli():
    with api.settings(warn_only=True):
        assert api.local("ansible-role-apply --help").succeeded
