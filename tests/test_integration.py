# -*- coding: utf-8 -*-
""" tests.test_ansible
"""

import os
import mock
import pytest
from fabric import api
from ansible_role import entry


def test_ansible_role_gives_ansible_galaxy_return_value():
    with pytest.raises(SystemExit) as exc:
        entry(['rolename.doesntexist', ])
    assert exc.value.code == 1


def test_ansible_role_gives_ansible_return_value():
    with pytest.raises(SystemExit) as exc:
        entry(['geerlingguy.git', ])
    assert exc.value.code == 0
