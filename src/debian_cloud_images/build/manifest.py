# SPDX-License-Identifier: GPL-2.0-or-later

import json
import logging
import pathlib

from typing import Dict, Iterable

from ..api.cdo.build import v1alpha1_BuildSchema
from ..api import wellknown


logger = logging.getLogger(__name__)


class CreateManifest:
    input_filename: pathlib.Path
    output_filename: pathlib.Path
    info: Dict[str, str]

    def __init__(
            self, *,
            input_filename: pathlib.Path,
            output_filename: pathlib.Path,
            info: Dict[str, str],
    ):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.info = info

    def __call__(self, run: bool, digest: Iterable[str]) -> None:
        if not run:
            return

        with self.input_filename.open() as f:
            manifest = v1alpha1_BuildSchema().load(json.load(f))

        manifest.info = self.info

        manifest.metadata.labels[wellknown.label_cdo_vendor] = self.info['vendor']
        manifest.metadata.labels[wellknown.label_cdo_version] = self.info['version']
        manifest.metadata.labels[wellknown.label_do_arch] = self.info['arch']
        manifest.metadata.labels[wellknown.label_do_dist] = 'debian'
        manifest.metadata.labels[wellknown.label_do_release] = self.info['release']
        if self.info['type'] == 'dev':
            manifest.metadata.labels[wellknown.label_bcdo_build_id] = self.info['build_id']
            manifest.metadata.labels[wellknown.label_bcdo_type] = self.info['type']

        manifest.metadata.annotations[wellknown.annotation_cdo_digest] = ','.join(digest)

        with self.output_filename.open('w') as f:
            json.dump(v1alpha1_BuildSchema().dump(manifest), f, indent=4, separators=(',', ': '), sort_keys=True)
