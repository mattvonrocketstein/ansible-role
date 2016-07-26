# -*- coding: utf-8 -*-
""" tests.test_ansible
"""

import os
import mock
import pytest
from fabric import api

from .backports import TemporaryDirectory
from ansible_role_apply.util import (
    require_ansible_role,)
from ansible_role_apply import (
    role_apply, entry, report, get_parser)
from argparse import ArgumentParser


def test_get_parser():
    parser = get_parser()
    assert type(parser) == ArgumentParser


@mock.patch("ansible_role_apply.util.apply_ansible_role")
def test_entry(aar):
    entry()
    assert aar.called_once


def test_require_ansible_role_good_val():
    role_name = 'role.name'
    with mock.patch("fabric.api.local") as fake:
        with TemporaryDirectory() as tmp_dir:
            require_ansible_role(
                role_name, tmp_dir, report=report)
        cmd = 'ansible-galaxy install -p {0} {1}'
        cmd = cmd.format(tmp_dir, role_name)
        fake.assert_called_with(cmd)


@mock.patch("ansible_role_apply.util.apply_ansible_role")
def test_help(aar):
    with TemporaryDirectory() as tmp_dir:
        role_name = 'role.name'
        role_apply(role_name,
                   module_path=tmp_dir,
                   extra_ansible_args=[])
    ansible_args = '--module-path {0}'
    ansible_args = ansible_args.format(tmp_dir).split()
    aar.assert_called_with(
        role_name,
        os.path.join(tmp_dir, 'roles'),
        ansible_args=ansible_args,
        report=report)
