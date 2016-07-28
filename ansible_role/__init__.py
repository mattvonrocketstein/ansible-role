# -*- coding: utf-8 -*-
"""
    The missing "ansible-role" command, applying a single role without
    editing a playbook.
"""

import os
import json
import sys
import shutil
import tempfile
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

import jinja2
import shellescape
from fabric import api
from fabric.colors import red, cyan

from .base import report as base_report, eprint
from ansible_role.version import __version__

JINJA_ENV = jinja2.Environment(
    undefined=jinja2.StrictUndefined)

FAIL = FAILURE = red('✖ ')
SUCCESS = cyan('✓ ')

PLAYBOOK_CONTENT = '\n'.join([
    "- hosts: all",
    # "  user: {{user}}",
    "  become: yes",
    "  become_method: sudo",
    "  roles:",
    "  - {role: {{role_path}}{{env}}}",
])

report = lambda *args, **kargs: base_report(
    'ansible-role', *args, **kargs)


def get_parser():
    """ creates the parser for the ansible-role command line utility """
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


def entry(args=[]):
    """ Main entry point """
    args = args or sys.argv[1:]
    report('version {0}'.format(__version__))
    parser = get_parser()
    prog_args, extra_ansible_args = parser.parse_known_args(args)
    role_name = prog_args.rolename.pop()
    module_path = prog_args.module_path
    succes, code = role_apply(
        role_name, module_path, extra_ansible_args)
    raise SystemExit(code)


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
        success, code = apply_ansible_role(
            role_name, role_dir,
            ansible_args=extra_ansible_args,
            report=report)
        if not success and module_path_created:
            report("next time pass --module-path if you "
                   "want to avoid redownloading the role")
    finally:
        if module_path_created:
            shutil.rmtree(module_path)
    return success, code

######


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


def get_playbook_for_role(role_name, role_dir, report=base_report, **env):
    """ this provisioner applies a single ansible role.  this is more
        complicated than it sounds because there's no way to do this
        without a playbook, and so a temporary playbook is created just
        for this purpose.

        To pass ansible variables through to the role, you can use kwargs
        to this function.

        see also:
          https://groups.google.com/forum/#!topic/ansible-project/h-SGLuPDRrs
    """
    env = env.copy()
    env_string = ''
    err = (
        "ansible-role apply only supports passing "
        "simple environment variables (strings or bools). "
        "Found type '{0}' at name '{1}'")
    for k, v in env.items():
        if isinstance(v, (bool, basestring, list)):
            v = json.dumps(v)
        else:
            raise SystemExit(err.format(type(v), k))
        env_string += ', ' + ': '.join([k, v])
    ctx = dict(
        env=env_string,
        role_path=os.path.join(role_dir, role_name),)
    playbook_content = JINJA_ENV.from_string(
        PLAYBOOK_CONTENT).render(**ctx)
    return playbook_content


def apply_ansible_role(role_name, role_dir, ansible_args='', report=base_report, **env):
    """ """
    assert isinstance(role_name, (basestring,))
    assert isinstance(role_dir, (basestring,))
    playbook_content = get_playbook_for_role(
        role_name, role_dir, report=report)
    require_ansible_role(role_name, role_dir, report=report)
    with NamedTemporaryFile() as tmpf:
        tmpf.write(playbook_content)
        tmpf.seek(0)
        msg = "created playbook {0} for applying role: {1}"
        report(SUCCESS + msg.format(tmpf.name, role_name))
        if env:
            report("dynamic playbook content:")
            eprint(playbook_content)
            eprint("\n")
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
