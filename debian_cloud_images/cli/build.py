from .base import BaseCommand


class BuildCommand(BaseCommand):
    argparser_name = 'build'
    argparser_help = 'build Debian images'
    argparser_usage = '%(prog)s'

    @classmethod
    def register_args(cls, parser):
        super().register_args(parser)

    def __init__(self, args):
        super().__init__(args)


if __name__ == '__main__':
    parser = BuildCommand._argparse_init_base()

    args = parser.parse_args()
    print(args)
