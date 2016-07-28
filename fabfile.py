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
def release():
    """ releases the master branch at the current version to pypi """
    ldir = _dirname(__file__)
    print colors.red("warning:") + \
        (" by now you should have commited local"
         " master and bumped version string")
    ans = confirm('proceed with pypi update in "{0}"?'.format(ldir))
    if not ans:
        return
    with api.lcd(ldir):
        # stash local changes if there are any
        api.local("git stash")
        current_branch = api.local('git rev-parse --abbrev-ref HEAD')
        # warn-only, because if the branch already exists the command fails
        with api.settings(warn_only=True):
            tmp_checkout = api.local("git checkout -b pypi").succeeded
        if tmp_checkout.failed:
            api.local("git checkout pypi")
        api.local("git reset --hard master")
        api.local("python setup.py register -r pypi")
        api.local("python setup.py sdist upload -r pypi")
        api.local('git checkout {0}'.format(current_branch))


@api.task
def vulture():
    with api.lcd(os.path.dirname(__file__)):
        api.local(
            'vulture {0} --exclude fabfile.py')

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
