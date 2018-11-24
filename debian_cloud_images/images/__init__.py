import json
import logging
import tarfile


logger = logging.getLogger(__name__)


class Images(dict):
    def read_path(self, path):
        for manifest in path.glob('*.json'):
            logger.info('Reading manifest %s', manifest.name)

            try:
                with manifest.open() as f:
                    manifest = json.load(f)
                    basename = manifest['_meta']['name']
                    stage = manifest['_meta']['stage']
                    image = self.setdefault(basename, Image(basename, path))

                    if stage == 'build':
                        image.read_build_manifest(manifest)
                    else:
                        raise RuntimeError('Manifest type {} not supported'.format(stage))

            except Exception:
                logger.exception('Can\'t load manifest')


class Image:
    def __init__(self, name, path):
        self.name = name
        self.__path = path

    def read_build_manifest(self, data):
        self.build_arch = data['build_info']['arch']
        self.build_image_type = data['build_info']['image_type']
        self.build_release = data['build_info']['release']
        self.build_release_id = data['build_info']['release_id']
        self.build_vendor = data['build_info']['vendor']
        self.build_version = data['cloud_release'].get('version')

    def get_tar(self):
        for ext in ('.tar', '.tar.xz'):
            file_in = self.__path.joinpath(self.name + ext)
            if file_in.exists():
                return tarfile.open(file_in, 'r:*')

        raise RuntimeError('Unable to find image tar file for {} in {}'.format(self.name, self.__path.as_posix()))

    def image_name(self, variant, version_override):
        version = version_override or self.build_version
        if not version:
            raise RuntimeError('No version or version override specified')

        if variant == 'daily':
            return 'debian-{}-daily-{}'.format(self.build_release_id, version)
        elif variant == 'dev':
            return 'debian-{}-dev-{}'.format(self.build_release_id, version)
        elif variant == 'release':
            return 'debian-{}-{}'.format(self.build_release_id, version)
        else:
            raise RuntimeError

    def write_vendor_manifest(self, stage, data):
        """ Write upload manifest """
        manifest = {
            '_meta': {
                'basename': self.name,
                'stage': stage,
            },
            self.build_vendor: data,
        }

        manifest_file = self.__path.joinpath('{}.{}.json'.format(self.name, stage))
        with manifest_file.open('w') as f:
            json.dump(manifest, f, indent=4, separators=(',', ': '), sort_keys=True)
