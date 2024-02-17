# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import os
import yaml


class ActionEnum(argparse.Action):
    def __init__(self, enum, help='', **kw):
        self.enum = enum
        choices = (name for name, member in enum.__members__.items())
        help += ' (choices: {})'.format(', '.join(choices))
        super().__init__(help=help, type=self.get_value, **kw)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

    def get_value(self, name):
        try:
            return self.enum[name]
        except KeyError:
            raise argparse.ArgumentError(self, 'invalid value: {}'.format(name))


class ActionEnv(argparse.Action):
    def __init__(self, env, default=None, required=True, help=None, **kw):
        default = os.environ.get(env, default)
        if default:
            required = False
        help_env = '(default: ${})'.format(env)
        if help:
            help += ' ' + help_env
        else:
            help = help_env
        super().__init__(default=default, required=required, help=help, **kw)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class HashAction(argparse.Action):
    def __init__(
        self,
        *,
        default=None,
        dest=None,
        help='',
        metavar=None,
        **kw,
    ):
        assert default is None
        if metavar is None:
            metavar = f'{dest.upper()}=VALUE'
        super().__init__(
            default={},
            dest=dest,
            help=help,
            metavar=metavar,
            **kw,
        )

    def __call__(self, parser, namespace, value, option_string=None):
        items = getattr(namespace, self.dest)
        k, v = value.split('=', 1)

        subitem = items
        kl = k.split('.')
        for k in kl[:-1]:
            subitem = subitem.setdefault(k, {})
        subitem[kl[-1]] = yaml.safe_load(v)

        setattr(namespace, self.dest, items)
