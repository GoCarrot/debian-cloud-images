# SPDX-License-Identifier: GPL-2.0-or-later

import json
import pytest

from debian_cloud_images.build.manifest import CreateManifest


class TestCreateManifest:
    info = {
        'vendor': 'vendor',
        'version': 'version',
        'arch': 'arch',
        'release': 'release',
        'build_id': 'build_id',
        'type': 'type',
    }

    def test___call__(self, tmp_path):
        input_filename = tmp_path / 'in'
        output_filename = tmp_path / 'out'
        run = CreateManifest(
            dpkg_status=input_filename,
            output_filename=output_filename,
            info=self.info,
        )

        with input_filename.open('w') as f:
            f.write('')

        run.write(True, ['digest'])

        with output_filename.open() as f:
            data = json.load(f)
            assert data['data']['info'] == self.info

    def test___call___fail(self, tmp_path):
        input_filename = tmp_path / 'in'
        output_filename = tmp_path / 'out'
        run = CreateManifest(
            dpkg_status=input_filename,
            output_filename=output_filename,
            info=self.info,
        )

        with pytest.raises(FileNotFoundError):
            run.write(True, [])

    def test___call___noop(self, tmp_path):
        input_filename = tmp_path / 'in'
        output_filename = tmp_path / 'out'
        run = CreateManifest(
            dpkg_status=input_filename,
            output_filename=output_filename,
            info=self.info,
        )

        run.write(False, [])
