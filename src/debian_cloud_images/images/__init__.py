import contextlib
import json
import logging
import os
import subprocess
import tarfile
import tempfile

from ..api.registry import registry as api_registry


logger = logging.getLogger(__name__)


class Images(dict):
    def read(self, manifest):
        if not manifest.name.endswith('.build.json'):
            return

        name = manifest.name.rsplit('.', 3)[0]
        logger.info('Reading build %s', name)

        try:
            with manifest.open() as f:
                d = api_registry.load(json.load(f))
                self[name] = Image(name, manifest.parent, d)

        except Exception:
            logger.exception('Can\'t load build')


class Image:
    def __init__(self, name, path, build):
        self.name = name
        self.__path = path
        self.build = build

        self.build_info = build.info
        self.build_arch = build.info['arch']
        self.build_release = build.info['release']
        self.build_release_id = build.info['release_id']
        self.build_vendor = build.info['vendor']
        self.build_version = build.info['version']

    def _convert_image_f(self, format):
        if format == 'qcow2':
            return self.__convert_image_to_qcow2
        if format == 'vhd':
            return self.__convert_image_to_vhd
        if format == 'vmdk':
            return self.__convert_image_to_vmdk
        raise NotImplementedError

    def __convert_image_to_qcow2(self, name_in, name_out):
        subprocess.check_call((
            'qemu-img',
            'convert',
            '-f', 'raw',
            '-O', 'qcow2',
            '-c',
            '-o', 'compat=0.10',
            name_in,
            name_out,
        ))

    def __convert_image_to_vhd(self, name_in, name_out):
        subprocess.check_call((
            'qemu-img',
            'convert',
            '-f', 'raw',
            '-O', 'vpc',
            '-o', 'subformat=fixed,force_size',
            name_in,
            name_out,
        ))

    def __convert_image_to_vmdk(self, name_in, name_out):
        subprocess.check_call((
            'qemu-img',
            'convert',
            '-f', 'raw',
            '-O', 'vmdk',
            '-o', 'subformat=streamOptimized',
            name_in,
            name_out,
        ))

    @contextlib.contextmanager
    def open_image(self, format):
        convert = self._convert_image_f(format)

        with self.open_tar() as tar:
            with tempfile.TemporaryDirectory() as tempdirname:
                name_raw = os.path.join(tempdirname, 'disk.raw')
                name_converted = os.path.join(tempdirname, 'disk.{}'.format(format))

                logger.debug('Extract image to %s', name_raw)
                tar.extract('disk.raw', path=tempdirname, set_attrs=False)

                logger.debug('Converting image %s to %s as %s', name_raw, name_converted, format)
                convert(name_raw, name_converted)

                with open(name_converted, mode='rb', buffering=0) as fout_converted:
                    yield fout_converted

    def open_tar(self):
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
            return 'debian-{}-{}-daily-{}'.format(self.build_release_id, self.build_arch, version)
        elif variant == 'dev':
            return 'debian-{}-{}-dev-{}'.format(self.build_release_id, self.build_arch, version)
        elif variant == 'release':
            return 'debian-{}-{}-{}'.format(self.build_release_id, self.build_arch, version)
        else:
            raise RuntimeError

    def write_manifests(self, tool, manifests):
        """ Write manifests """
        manifest_file = self.__path.joinpath('{}.{}.json'.format(self.name, tool))
        with manifest_file.open('w') as f:
            json.dump(api_registry.dump(manifests), f, indent=4, separators=(',', ': '), sort_keys=True)

    def write_vendor_manifest(self, stage, data):
        """ Write upload manifest """
        manifest = {
            '_meta': {
                'name': self.name,
                'stage': stage,
            },
            self.build_vendor: data,
        }

        manifest_file = self.__path.joinpath('{}.{}.json'.format(self.name, stage))
        with manifest_file.open('w') as f:
            json.dump(manifest, f, indent=4, separators=(',', ': '), sort_keys=True)
