# -*- coding: utf-8 -*-
""" ansible_role
    The missing "ansible-role" command,
    for applying a single role without editing a playbook.

    see also:
      https://mattvonrocketstein.github.io/heredoc/ansible-role.html
"""

import os
import sys
import shutil
import tempfile
import argparse
from tempfile import NamedTemporaryFile

import shellescape
from fabric import api
from fabric.colors import red, cyan

from ansible_role.version import __version__
from ansible_role.console import report as base_report

FAIL = red('✖ ')
SUCCESS = cyan('✓ ')

report = lambda *args, **kargs: base_report(
    'ansible-role', *args, **kargs)
USAGE = (
    'Usage: ansible-role rolename.username [hostname]'
    ' [ansible-playbook args]\n\nThis command applies the given ansible '
    'role to the specified host.\nWhen hostname is not given, '
    '`localhost` will be used.\n\nIf --module-path is not given, '
    'the role will be downloaded to a temporary directory using '
    'ansible-galaxy.\n\nIf --module-path is given, then the role will '
    'be downloaded only if "$module_path/roles/rolename.username" does '
    'not already exist.  Nothing will be cleaned afterwards.\n\n\n'
    'ALL OTHER OPTIONS will be passed on to ansible-playbook!\n\n')


def get_parser():
    """ creates the parser for the ansible-role command line utility """
    class MyHelpFormatter(argparse.HelpFormatter):
        usage = USAGE

        def format_help(self):
            return self.usage
    parser = argparse.ArgumentParser(
        prog=os.path.split(sys.argv[0])[-1],
        formatter_class=MyHelpFormatter,)
    parser.add_argument('rolename', type=str, nargs=1,)
    parser.add_argument('host', type=str, nargs='?', default='localhost',)
    parser.add_argument('--module-path', '-M',)
    return parser


def get_or_create_role_dir(module_path):
    role_dir = os.path.join(module_path, 'roles')
    if not os.path.exists(role_dir):
        msg = "ansible role-dir does not exist at '{0}', creating it"
        report(msg.format(role_dir))
        api.local('mkdir -p "{0}"'.format(role_dir))
    return role_dir


def escape_args(extra_ansible_args):
    """ """
    return [
        shellescape.quote(x) if ' ' in x else x
        for x in extra_ansible_args
    ]


def role_apply(role_name='role.name', module_path=None, extra_ansible_args=[]):
    """ """
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
        success, exit_code = apply_ansible_role(
            role_name, role_dir,
            ansible_args=extra_ansible_args,
            report=report)
        if not success and module_path_created:
            report("next time pass --module-path if you "
                   "want to avoid redownloading the role")
    finally:
        if module_path_created:
            shutil.rmtree(module_path)
    return success, exit_code


def require_ansible_role(role_name, role_dir, report=base_report):
    """ """
    if role_name not in os.listdir(role_dir):
        galaxy_cmd = 'ansible-galaxy install -p {role_dir} {role_name}'
        msg = "role '{0}' not found in {1}"
        report(FAIL + msg.format(role_name, role_dir))
        cmd = galaxy_cmd.format(role_dir=role_dir, role_name=role_name)
        result = api.local(cmd)
        if not result.succeeded:
            err = "missing role {0} could not be installed"
            raise RuntimeError(err.format(role_name))
    msg = "ansible role '{0}' installed to '{1}'"
    msg = msg.format(role_name, role_dir)
    report(SUCCESS + msg)


def get_playbook_for_role(role_name, role_dir, report=base_report):
    """ this provisioner applies a single ansible role.  this is more
        complicated than it sounds because there's no way to do this
        without a playbook, and so a temporary playbook is created just
        for this purpose.

        To pass ansible variables through to the role, you can use kwargs
        to this function.


    """
    def make_playbook_string(role_path):
        return '\n'.join([
            "- hosts: all",
            "  roles:",
            "  - {role: " + role_path + "}",
        ])
    role_path = os.path.join(role_dir, role_name)
    playbook_content = make_playbook_string(role_path)
    return playbook_content


def apply_ansible_role(role_name, role_dir, ansible_args='', report=None):
    """ """
    report = report or base_report
    err = " should be a string!"
    assert isinstance(role_name, (basestring,)), "role_name" + err
    assert isinstance(role_dir, (basestring,)), "role_dir" + err
    playbook_content = get_playbook_for_role(
        role_name, role_dir, report=report)
    require_ansible_role(role_name, role_dir, report=report)
    with NamedTemporaryFile() as tmpf:
        tmpf.write(playbook_content)
        tmpf.seek(0)
        msg = "created playbook {0} for applying role: {1}"
        report(SUCCESS + msg.format(tmpf.name, role_name))
        report("applying ansible role '{0}'".format(role_name))
        ansible_args = ansible_args if isinstance(ansible_args, (list,)) \
            else ansible_args.split()
        cmd = ['ansible-playbook', tmpf.name] + ansible_args
        cmd = " ".join(cmd)
        with api.settings(warn_only=True):
            result = api.local(cmd)
    success = result.succeeded
    code = result.return_code
    icon = SUCCESS if success else FAIL
    msg = 'succeeded' if success else 'failed'
    report(icon + msg +
           " applying ansible role: {0}".format(role_name))
    return success, code


def entry(args=[]):
    """ Command-line entry point """
    args = args or sys.argv[1:]
    report('version {0}'.format(__version__))
    parser = get_parser()
    prog_args, extra_ansible_args = parser.parse_known_args(args)
    role_name = prog_args.rolename.pop()
    module_path = prog_args.module_path
    succes, code = role_apply(
        role_name, module_path, extra_ansible_args)
    raise SystemExit(code)
