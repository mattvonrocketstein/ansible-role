# -*- coding: utf-8 -*-
"""
    The missing "ansible-role" command, applying a single role without
    editing a playbook.
"""
import os
import sys
import shutil
import tempfile
from argparse import ArgumentParser

import shellescape
from fabric import api

from ansible_role_apply.base import report as base_report
from ansible_role_apply.version import __version__
from ansible_role_apply import util

report = lambda *args, **kargs: base_report(
    'ansible-role-apply', *args, **kargs)


def get_parser():
    """ creates the parser for the ansible-role-apply command line utility """
    parser = ArgumentParser(prog=os.path.split(sys.argv[0])[-1])
    parser.add_argument(
        'rolename',
        metavar='role_name', type=str, nargs=1,)
    parser.add_argument(
        '--module-path', '-M',
        help='ansible module-path')
    parser.add_argument(
        '--env', help='JSON env for role-application')
    return parser


def get_or_create_role_dir(module_path):
    role_dir = os.path.join(module_path, 'roles')
    if not os.path.exists(role_dir):
        msg = "ansible role-dir does not exist at '{0}', creating it"
        report(msg.format(role_dir))
        api.local('mkdir -p "{0}"'.format(role_dir))
    return role_dir


def entry():
    """ Main entry point """
    report('version {0}'.format(__version__))
    parser = get_parser()
    prog_args, extra_ansible_args = parser.parse_known_args(sys.argv[1:])
    role_name = prog_args.rolename.pop()
    module_path = prog_args.module_path
    do_work(role_name, module_path, extra_ansible_args)


def escape_args(extra_ansible_args):
    """ """
    return [
        shellescape.quote(x) if ' ' in x else x
        for x in extra_ansible_args
    ]


def do_work(role_name, module_path, extra_ansible_args):
    module_path_created = False
    if not module_path:
        module_path = tempfile.mkdtemp()
        module_path_created = True
        report("ansible module-path not given, using {0}".format(module_path))
    else:
        extra_ansible_args += ['--module-path', module_path]
    extra_ansible_args = escape_args(extra_ansible_args)
    role_dir = get_or_create_role_dir(module_path)
    try:
        success = util.apply_ansible_role(
            role_name, role_dir,
            ansible_args=extra_ansible_args,
            report=report)
        if not success and module_path_created:
            report("next time pass --module-path if you "
                   "want to avoid redownloading the role")
    finally:
        if module_path_created:
            shutil.rmtree(module_path)
