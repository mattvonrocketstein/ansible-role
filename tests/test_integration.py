# -*- coding: utf-8 -*-
""" tests.test_ansible
"""

import os
import mock
import pytest
from fabric import api
from ansible_role import entry

TMPDIR = os.path.join(os.path.dirname(__file__), 'tmp')
if not os.path.exists(TMPDIR):
    os.mkdir(TMPDIR)


def test_ansible_role_gives_ansible_galaxy_return_value():
    with pytest.raises(SystemExit) as exc:
        entry(['rolename.doesntexist', ])
    assert exc.value.code == 1


def test_ansible_role_help():
    with pytest.raises(SystemExit) as exc:
        entry(['--help', ])
    assert exc.value.code == 0


def test_ansible_role_gives_ansible_return_value_success():
    """ """
    with pytest.raises(SystemExit) as exc:
        # f500.dumpall is a no-op role that simply dumps debugging variables
        entry(['f500.dumpall', '--module-path', TMPDIR, '--become'])
    assert exc.value.code == 0
