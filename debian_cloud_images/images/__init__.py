import json
import logging


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
                    image = self.setdefault(basename, Image(basename))

                    if stage == 'build':
                        image.read_build_manifest(manifest)
                    else:
                        raise RuntimeError('Manifest type {} not supported'.format(stage))

            except Exception:
                logger.exception('Can\'t load manifest')


class Image:
    def __init__(self, name):
        self.name = name

    def read_build_manifest(self, data):
        self.build_arch = data['build_info']['arch']
        self.build_image_type = data['build_info']['image_type']
        self.build_release = data['build_info']['release']
        self.build_release_id = data['build_info']['release_id']
        self.build_vendor = data['build_info']['vendor']
        self.build_version = data['cloud_release'].get('version')
