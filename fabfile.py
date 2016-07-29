#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# fabfile for ansible_role
#
# this file is a self-hosting fabfile, meaning it
# supports direct invocation with standard option
# parsing, including --help and -l (for listing commands).
#
# summary of commands/arguments:
#
#   * fab pypi_repackage: update this package on pypi
#   * fab version_bump: bump the package version

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

ldir = _dirname(__file__)

pkg_name = 'ansible_role'


VERSION_DELTA = .01
pkg_name = 'ansible_role'


@api.task
def version_bump():
    """ bump the version number for """ + pkg_name
    sandbox = {}
    version_file = os.path.join(pkg_name, 'version.py')
    err = 'version file not found in expected location: ' + version_file
    assert os.path.exists(version_file), err
    # running "import pkg.version" should have no side-effects,
    # so there's little point in parsing the file.  just exec
    execfile(version_file, sandbox)
    current_version = sandbox['__version__']
    new_version = current_version + VERSION_DELTA
    with open(version_file, 'r') as fhandle:
        version_file_contents = [x for x in fhandle.readlines()
                                 if x.strip()]
    new_file = version_file_contents[:-1] + \
        ["__version__={0}".format(new_version)]
    new_file = '\n'.join(new_file)
    print colors.red("warning:") + \
        " version will be changed to {0}".format(new_version)
    print
    print colors.red("new version file will look like this:\n")
    print new_file
    ans = confirm('proceed with version change?')
    if not ans:
        print 'aborting.'
        return
    with open(version_file, 'w') as fhandle:
        fhandle.write(new_file)
        print 'version has been rewritten.'


@api.task
def release(force=False):
    """ releases the master branch at the current version to pypi """
    with api.quiet():
        cmd = 'git rev-parse --abbrev-ref HEAD'
        current_branch = api.local(cmd, capture=True)
    if not current_branch.succeeded:
        err = "wait a minute, is this even a git repo?"
        print colors.red("ERROR: ") + err
        raise SystemExit(1)
    if current_branch != 'master':
        err = "you must do releases from master, but this is {0}"
        print colors.red("ERROR:") + err.format(current_branch)
        raise SystemExit(1)
    ldir = _dirname(__file__)
    if not force:
        print colors.red("WARNING:\n") + \
            ("  did you commit local master?\n"
             "  did you bump the version string?\n")
        this_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(os.path.join(this_dir, pkg_name))
        from version import __version__ as release_version  # flake8: noqa
        sys.path.pop()
        release_version = str(release_version)
        print colors.blue("current branch: ") + current_branch
        print colors.blue("current version: ") + release_version
        print colors.blue("current dir: ") + "{0}".format(ldir)
        question = '\nproceed with pypi update?'
        ans = confirm(colors.red(question))
        if not ans:
            raise SystemExit(1)

    with api.lcd(ldir):
        # stash local changes if there are any
        api.local("git stash")
        # warn-only, because if the branch already exists the command fails
        with api.settings(warn_only=True):
            tmp_checkout = api.local("git checkout -b pypi")
        if tmp_checkout.failed:
            api.local("git checkout pypi")
        api.local("git reset --hard master")
        api.local("python setup.py register -r pypi")
        api.local("python setup.py sdist upload -r pypi")
        api.local('git checkout {0}'.format(current_branch))


@api.task
def vulture():
    """ try to find dead code paths """
    with api.quiet():
        if not api.local('which vulture').succeeded:
            print 'vulture not found, installing it'
            api.local('pip install vulture')
    vulture_cmd = 'vulture {pkg_name} --exclude fabfile.py'
    vulture_cmd = vulture_cmd.format(pkg_name=pkg_name)
    with api.lcd(os.path.dirname(__file__)):
        with api.settings(warn_only=True):
            with api.hide('everything'):
                result = api.local(vulture_cmd, capture=True)
                exit_code = result.return_code
    print result
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
