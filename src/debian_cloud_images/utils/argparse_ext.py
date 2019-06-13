import argparse
import os


class ActionAzureAuth(argparse.Action):
    class AzureAuth:
        def __init__(self, tenant_id, client_id, client_secret):
            self.tenant_id = tenant_id
            self.client_id = client_id
            self.client_secret = client_secret

    def __init__(self, **kw):
        kw.setdefault('help', 'Authentication info for Azure AD service principal')
        kw.setdefault('metavar', 'TENANT:APPLICATION:SECRET')
        super().__init__(**kw)

    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, self.AzureAuth(*value.split(':')))


class ActionCommaSeparated(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        values = [i for i in value.split(',') if i]
        setattr(namespace, self.dest, values)


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
