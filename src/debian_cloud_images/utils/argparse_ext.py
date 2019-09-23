import argparse
import os


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


class ConfigStoreAction(argparse.Action):
    def __init__(
        self,
        *,
        config,
        config_key,
        default=None,
        help='',
        required=False,
        **kw,
    ):
        if default:
            help += f'\n    (default: {default})'
        help += f'\n    (config key: {config_key})'
        config_default = config.get(config_key, default)
        if config_default:
            required = False
        super().__init__(
            default=config_default,
            help=help,
            required=required,
            **kw,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class ConfigAppendAction(argparse.Action):
    def __init__(
        self,
        *,
        config,
        config_key,
        default=None,
        help='',
        required=False,
        **kw,
    ):
        if default:
            help += f'\n    (default: {default})'
        help += f'\n    (config key: {config_key})'
        config_default = config.get(config_key, default)
        if config_default:
            config_default = config_default.split(' ')
            required = False
        super().__init__(
            default=config_default,
            help=help,
            required=required,
            **kw,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, [])
        items = items[:] + values
        setattr(namespace, self.dest, items)


class ConfigHashAction(argparse.Action):
    def __init__(
        self,
        *,
        config,
        config_key,
        default=None,
        dest=None,
        help='',
        metavar=None,
        required=False,
        **kw,
    ):
        if default:
            help += f'\n    (default: {default})'
        help += f'\n    (config key: {config_key})'
        config_default = config.get(config_key, default)
        if config_default:
            config_default = self._parse_values(config_default.split(' '))
            required = False
        if metavar is None:
            metavar = f'{dest.upper()}=VALUE'
        super().__init__(
            default=config_default,
            dest=dest,
            help=help,
            metavar=metavar,
            required=required,
            **kw,
        )

    @staticmethod
    def _parse_values(values):
        return dict(i.split('=', 1) for i in values)

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None or items is self.default:
            items = {}
        items.update(self._parse_values(values))
        setattr(namespace, self.dest, items)


class ConfigStoreAzureAuthAction(ConfigStoreAction):
    class AzureAuth:
        def __init__(self, tenant_id, client_id, client_secret):
            self.tenant_id = tenant_id
            self.client_id = client_id
            self.client_secret = client_secret

    def __init__(self, **kw):
        kw.setdefault('config_key', 'azure-auth')
        kw.setdefault('help', 'Authentication info for Azure AD service principal')
        kw.setdefault('metavar', 'TENANT:APPLICATION:SECRET')
        kw.setdefault('type', self.create)
        super().__init__(**kw)

    def create(self, value):
        try:
            return self.AzureAuth(*value.split(':'))
        except TypeError:
            raise argparse.ArgumentError(self, 'invalid value')
