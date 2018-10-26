import argparse
import os


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
