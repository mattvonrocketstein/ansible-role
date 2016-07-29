# -*- coding: utf-8 -*-
""" ansible_role.console

    helpers for pretty-printing console status messages
"""
from __future__ import print_function
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class Reporter(object):

    def _report_name(self):
        return self.__class__.__name__

    def report(self, msg, *args, **kargs):
        """ 'print' replacement that includes some color and formatting """
        template = '\x1b[31;01m{0}:\x1b[39;49;00m {1} {2}'
        name = self._report_name()
        name = name.replace('_', '')
        eprint(template.format(
            name, msg, args or ''))


def report(title, msg, *args, **kargs):
    _reporter = type(title, (Reporter,), dict())()
    _reporter.report(msg)
