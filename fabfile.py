#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fabfile for ansible_role
#
# Summary of commands/arguments (you can also use `fab -l`):
#
#   * fab release: update this package on pypi
#   * fab version_bump: bump the package version
#   * fab vulture: look for dead code
#   * fab show_version: shows current pkg version
#
import os
import sys
from fabric import api
from fabric import colors
from fabric.contrib.console import confirm

_ope = os.path.exists
_mkdir = os.mkdir
_expanduser = os.path.expanduser
_dirname = os.path.dirname

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_NAME = 'ansible_role'
VERSION_DELTA = .01


@api.task
def version_bump(force=False):
    """ bump the version number for """ + PKG_NAME
    sandbox = {}
    version_file = os.path.join(PKG_NAME, 'version.py')
    err = 'version file not found in expected location: ' + version_file
    assert os.path.exists(version_file), err
    # running "import pkg.version" should have no side-effects,
    # so there's little point in ASTing the file.  just exec it
    execfile(version_file, sandbox)
    current_version = sandbox['__version__']
    new_version = current_version + VERSION_DELTA
    with open(version_file, 'r') as fhandle:
        version_file_contents = [
            x for x in fhandle.readlines() if x.strip()]
    new_file = version_file_contents[:-1] + \
        ["__version__={0}".format(new_version)]
    new_file = '\n'.join(new_file)
    if not force:
        print colors.red("warning:"),
        print " version will be changed to {0}\n".format(new_version)
        print colors.red("new version file will look like this:\n")
        print new_file
        ans = confirm('proceed with version change?')
        if not ans:
            print 'aborting.'
            raise SystemExit(1)
    with open(version_file, 'w') as fhandle:
        fhandle.write(new_file)
        print 'version rewritten to {0}'.format(new_version)


def get_pkg_version():
    """ """
    sys.path.append(os.path.join(THIS_DIR, PKG_NAME))
    from version import __version__ as release_version  # flake8: noqa
    sys.path.pop()
    return release_version


@api.task
def show_version():
    """ show current version of this package """
    print get_pkg_version()


def git_branch():
    """ returns (branch-name, hash) """
    with api.quiet():
        cmd = 'git rev-parse --abbrev-ref HEAD'
        current_branch = api.local(cmd, capture=True)
        cmd = 'git rev-parse HEAD'
        current_hash = api.local(cmd, capture=True)
    return current_hash, current_branch


@api.task
def release(force=False):
    """ releases the master branch at the current version to pypi """
    with api.lcd(THIS_DIR):
        return _release(force=force)


def _release(force=False):
    """ """
    def assert_master(branch_name):
        if current_branch != 'master':
            err = "you must do releases from master, but this is {0}"
            print colors.red("ERROR:") + err.format(current_branch)
            raise SystemExit(1)

    def assert_git(hash, branch_name):
        is_git_repo = all([current_branch.succeeded, current_hash.succeeded])
        if not is_git_repo:
            print colors.red("ERROR: ") + \
                "wait a minute, is this even a git repo?"
            raise SystemExit(1)

    def assert_confirm():
        print colors.red("WARNING:\n") + \
            ("  did you commit local master?\n"
             "  did you bump the version string?\n")
        question = '\nproceed with pypi update?'
        ans = confirm(colors.red(question))
        if not ans:
            raise SystemExit(1)
    current_version = get_pkg_version()
    current_hash, current_branch = git_branch()
    assert_git(current_hash, current_branch)
    assert_master(current_branch)
    print colors.blue("current branch: ") + current_branch
    print colors.blue("current version: ") + str(current_version)
    print colors.blue("current dir: ") + "{0}".format(THIS_DIR)
    if not force:
        assert_confirm()
    result = api.local("git stash")  # stash local changes if there are any
    stashed_changes = result.succeeded and str(
        result) != 'No local changes to save'
    # warn-only, because if the branch already exists the command fails
    with api.settings(warn_only=True):
        tmp_checkout = api.local("git checkout -b pypi")
    if tmp_checkout.failed:
        api.local("git checkout pypi")
    api.local("git reset --hard master")
    api.local("python setup.py register -r pypi")
    api.local("python setup.py sdist upload -r pypi")
    print colors.red("release successful")
    print "  hash {0} for branch {1} will be tagged as {2}".format(
        colors.blue(current_hash[:6]),
        colors.blue(current_branch),
        colors.blue(current_version))
    cmd = 'git tag -a "{0}" {1} -m "version {0}"'
    api.local(cmd.format(current_version, current_hash))
    api.local("git push origin --tags")
    api.local('git checkout {0}'.format(current_branch))
    if stashed_changes:
        with api.settings(warn_only=True):
            api.local('git stash pop')

import contextlib
VULTURE_EXCLUDE_PATHS = []
VULTURE_IGNORE_FUNCTIONS = ['format_help', 'entry']


@api.task
def vulture():
    """ try to find dead code paths """
    with api.quiet():
        if not api.local('which vulture').succeeded:
            print 'vulture not found, installing it'
            api.local('pip install vulture')
    ignore_functions_grep = 'egrep -v "{0}"'.format(
        '|'.join(VULTURE_IGNORE_FUNCTIONS))
    excluded = ",".join(VULTURE_EXCLUDE_PATHS)
    excluded_paths = (' --exclude ' + excluded) if excluded else ''
    vulture_cmd = '\n  vulture {pkg_name}{exclude}{pipes}'
    vulture_cmd = vulture_cmd.format(
        pkg_name=PKG_NAME,
        exclude=excluded_paths,
        pipes='|'.join(['', ignore_functions_grep]))
    changedir = api.lcd(os.path.dirname(__file__))
    warn_only = api.settings(warn_only=True)
    be_quit = api.hide('warnings')
    with contextlib.nested(changedir, warn_only, be_quit):
        result = api.local(vulture_cmd, capture=True)
        exit_code = result.return_code
    print result.strip()
    raise SystemExit(exit_code)


if __name__ == '__main__':
    # a neat hack that makes this file a "self-hosting" fabfile,
    # ie it is invoked directly but still gets all the fabric niceties
    # like real option parsing, including --help and -l (for listing
    # commands). note that as of fabric 1.10, the file for some reason
    # needs to end in .py, despite what the documentation says.  see:
    # http://docs.fabfile.org/en/1.4.2/usage/fabfiles.html#fabfile-discovery
    #
    # the .index() manipulation below should make this work regardless of
    # whether this is invoked from shell as "./foo.py" or "python foo.py"
    import sys
    from fabric.main import main as fmain
    patched_argv = ['fab', '-f', __file__, ] + \
        sys.argv[sys.argv.index(__file__) + 1:]
    sys.argv = patched_argv
    fmain()
