The missing "ansible-role" command: downloads, installs, and cleans temporary ansible roles without the need for manually editing ansible playbooks.

### About

The missing ansible-role command provides "anonymous roles" (ie role application without using playbooks) for ansible.  This is mainly intended for the testing phase when you're checking whether a given role will suite your purposes or not.  Basically `ansible-role` works by generating a temporary file for use as a playbook, then invoking `ansible-playbook` on the result.

### Specification

The ansible-role invocation respects data intended for the ansible-playbook command, i.e. ANSIBLE_* shell variables should be passed through, and the unparsed aspect of the `ansible-role` command line is passed through to `ansible-playbook`.

Despite pass-through, the `ansible-role` command parses and understands the `--module-path=FOO` argument if it is given, and by default will look for roles inside `FOO/roles`.

In the event no matching role is available locally, then the role will be downloaded automatically using the `ansible-galaxy` command.

In case a galaxy download is necessary and `--modulepath=FOO` is specified, it is downloaded to `FOO/roles` and NOT cleaned afterwards. File-system caching makes sense here because the `ansible-role` invocation is supposed to be quick and easy, but the usage of the role itself is considered somewhat less than experimental.

In case a galaxy download is necessary and `--modulepath` is NOT given, then there is no caching; file system cleaning for the role-download makes sense here because this is considered a one-off experiment and it's no use cluttering the file system. Thus the role will be downloaded to a temporary directory and will be deleted afterwards (regardless of whether the application of the role succeeds).

Apart from the standard `ansible-playbook` arguments, the `ansible-role` command line understands exactly 2 other arguments: the primary positional argument role_name, which is required and which specifies an ansible-galaxy role, and the host argument (which defaults to localhost). Again, everything else on the command line will be passed through to the `ansible-playbook` invocation.

After cleanup, the `ansible-role` command returns the same exit code as the implied `ansible-playbook` invocation.

### Installation

    $ pip install ansible-role

### Usage

    ansible-role username.rolename [hostname] [ansible-playbook args]

This command applies the given ansible role to the specified host.
When hostname is not given, `localhost` will be used.

If --module-path is not given, the role will be downloaded to a temporary directory using ansible-galaxy.

If --module-path is given, then the role will be downloaded only if "$module_path/roles/rolename.username" does not already exist.  Nothing will be cleaned afterwards.

ALL OTHER OPTIONS will be passed on to ansible-playbook!

### Contributing

**Pull requests and feature requests are welcome**, just use [the githubs](https://github.com/mattvonrocketstein/ansible-roles/).

**Testing:**.   All tests are run with tox, some tests are integration tests rather than proper unittests.  You can view the coverage results in the `htmlcov` folder.

    $ pip install tox
    $ tox

**Commit hooks**: To maintain consistent style in the library, please use the same precommit hooks as me.  To install precommit hooks after cloning the source repository, run these commands:

    $ pip install pre-commit
    $ pre-commit install

### TODO:

- [ ] Remove the fabric dependency as it prevents py3 usage
