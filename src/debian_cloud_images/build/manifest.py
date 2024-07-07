# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import json
import logging
import pathlib

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from ..api.cdo.build import v1alpha1_BuildSchema, Build
from ..api import wellknown
from ..utils.dataclasses_deb822 import read_deb822, field_deb822


logger = logging.getLogger(__name__)


@dataclass
class Package:
    package: str = field_deb822('Package')
    version: str = field_deb822('Version')
    arch: str = field_deb822('Architecture')
    multi_arch: Optional[str] = field_deb822(
        'Multi-Arch',
        default=None,
    )

    def get_manifest(self) -> dict[str, str]:
        ret: dict[str, str] = {
            'name': self.package,
            'version': self.version,
        }
        if self.multi_arch == 'same':
            ret['name'] += f':{self.arch}'
        return ret


class CreateManifest:
    input_filename: pathlib.Path
    output_filename: pathlib.Path | None
    info: Dict[str, str]

    def __init__(
            self, *,
            dpkg_status: pathlib.Path,
            output_filename: pathlib.Path | None,
            info: Dict[str, str],
    ):
        self.dpkg_status = dpkg_status
        self.output_filename = output_filename
        self.info = info

    def write(self, run: bool, digest: Iterable[str]) -> None:
        if not run or not self.output_filename:
            return

        with self.output_filename.open('w') as f:
            json.dump(self(digest), f, indent=4, separators=(',', ': '), sort_keys=True)

    def __call__(self, digest: Iterable[str] = ()) -> dict:
        manifest = Build(packages=[])

        with self.dpkg_status.open() as f:
            for p in read_deb822(Package, f, ignore_unknown=True):
                manifest.packages.append(p.get_manifest())

        manifest.info = self.info

        manifest.metadata.labels[wellknown.label_cdo_vendor] = self.info['vendor']
        manifest.metadata.labels[wellknown.label_cdo_version] = self.info['version']
        manifest.metadata.labels[wellknown.label_do_arch] = self.info['arch']
        manifest.metadata.labels[wellknown.label_do_dist] = 'debian'
        manifest.metadata.labels[wellknown.label_do_release] = self.info['release']
        if self.info['type'] == 'dev':
            manifest.metadata.labels[wellknown.label_bcdo_build_id] = self.info['build_id']
            manifest.metadata.labels[wellknown.label_bcdo_type] = self.info['type']

        if digest:
            manifest.metadata.annotations[wellknown.annotation_cdo_digest] = ','.join(digest)

        return v1alpha1_BuildSchema().dump(manifest)
