from .upload_base import UploadBaseCommand
from ..utils import argparse_ext


class UploadGceCommand(UploadBaseCommand):
    argparser_name = 'upload-gce'
    argparser_help = 'upload Debian images to GCE'
    argparser_usage = '%(prog)s'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

    def __init__(self, **kw):
        super().__init__(**kw)


if __name__ == '__main__':
    parser = UploadGceCommand._argparse_init_base()
    args = parser.parse_args()
    UploadGceCommand(**vars(args))()
