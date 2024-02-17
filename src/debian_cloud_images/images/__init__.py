# SPDX-License-Identifier: GPL-2.0-or-later

import contextlib
import json
import logging
import os
import subprocess
import tarfile
import tempfile

from ..api.cdo.build import Build
from ..api.cdo.upload import Upload
from ..api.registry import registry as api_registry


logger = logging.getLogger(__name__)


class Images(dict):
    def read(self, manifest):
        try:
            name = manifest.name.rsplit('.', 3)[0]
            image = self.setdefault(name, Image(name, manifest.parent))
            image.read_manifests(manifest)

        except Exception:
            logger.exception(f'Unable to load manifest {manifest.name}')


class Image:
    def __init__(self, name, path):
        self.name = name
        self.__path = path
        self.__builds = []
        self.__uploads = []

    @property
    def build(self):
        return self.__builds[0]

    @property
    def build_info(self):
        return self.build.info

    @property
    def build_arch(self):
        return self.build.info['arch']

    @property
    def build_release(self):
        return self.build.info['release']

    @property
    def build_release_id(self):
        return self.build.info['release_id']

    @property
    def build_vendor(self):
        return self.build.info['vendor']

    @property
    def build_version(self):
        return self.build.info['version']

    @property
    def uploads(self):
        return self.__uploads

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
            '-o', 'compat=1.1',
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
    def open_image(self, *formats):
        with self.open_tar() as tar:
            with tempfile.TemporaryDirectory() as tempdirname:
                names = []

                name_raw = os.path.join(tempdirname, 'disk.raw')

                logger.debug('Extract image to %s', name_raw)
                tar.extract('disk.raw', path=tempdirname, set_attrs=False)

                for format in formats:
                    if format:
                        name_converted = os.path.join(tempdirname, 'disk.{}'.format(format))
                        names.append(name_converted)

                        convert = self._convert_image_f(format)
                        logger.debug('Converting image %s to %s as %s', name_raw, name_converted, format)
                        convert(name_raw, name_converted)
                    else:
                        names.append(name_raw)

                files = [open(i, mode='rb', buffering=0) for i in names]
                if len(files) == 1:
                    yield files[0]
                else:
                    yield files
                [f.close() for f in files]

    def open_tar(self):
        return tarfile.open(fileobj=self.open_tar_raw(), mode='r:*')

    def open_tar_raw(self):
        for ext in ('.tar', '.tar.xz'):
            file_in = self.__path.joinpath(self.name + ext)
            if file_in.exists():
                f_in = open(file_in, 'rb')
                setattr(f_in, 'extension', ext)
                return f_in

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

    def read_manifests(self, manifest_file):
        logging.info(f'Read manifests from {manifest_file.name}')

        with manifest_file.open() as f:
            manifests = api_registry.load(json.load(f))

        if not isinstance(manifests, list):
            manifests = [manifests]

        for manifest in manifests:
            if isinstance(manifest, Build):
                logging.debug('Found Build manifest')
                self.__builds.append(manifest)
            elif isinstance(manifest, Upload):
                logging.debug('Found Upload manifest')
                self.__uploads.append(manifest)
            else:
                logging.info('Found unknown manifest')

    def write_manifests(self, tool, manifests, output):
        """ Write manifests """
        output.mkdir(parents=True, exist_ok=True)
        manifest_file = output.joinpath('{}.{}.json'.format(self.name, tool))
        with manifest_file.open('w') as f:
            json.dump(api_registry.dump(manifests), f, indent=4, separators=(',', ': '), sort_keys=True)

    def write_merged_manifests(self, f, manifests):
        """ Write manifests """
        manifests = self.__builds + self.__uploads + manifests
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
