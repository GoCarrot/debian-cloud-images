from .base import BaseCommand


class UploadBaseCommand(BaseCommand):
    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

    def __init__(self, **kw):
        super().__init__(**kw)
