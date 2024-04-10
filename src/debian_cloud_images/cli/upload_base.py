# SPDX-License-Identifier: GPL-2.0-or-later

from .base import BaseCommand
from ..images import Images
from ..images.publicinfo import ImagePublicInfo


class UploadBaseCommand(BaseCommand):
    def __init__(self, *, manifests=[], output=None, public_type=None, override_version=None, **kw):
        super().__init__(**kw)

        self.output = output

        override_info = {}
        if override_version:
            override_info['version'] = override_version
        self.image_public_info = ImagePublicInfo(public_type=public_type, override_info=override_info)

        self.images = Images()
        for manifest in manifests:
            self.images.read(manifest)

    def __call__(self):
        for image in self.images.values():
            self.uploader(image, public_info=self.image_public_info.apply(image.build_info))
