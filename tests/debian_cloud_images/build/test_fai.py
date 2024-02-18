# SPDX-License-Identifier: GPL-2.0-or-later

import importlib.resources
import pytest
import subprocess

from unittest.mock import Mock

from debian_cloud_images.build.fai import (
    RunFAI,
)
from debian_cloud_images import resources


class TestRunFAI:
    def test___call__(self, tmp_path):
        env = {'ENV1': 'env1', 'ENV2': 'env2'}
        run = RunFAI(
            output_filename=tmp_path,
            release='release',
            classes=['CLASS1', 'CLASS2'],
            size_gb=23,
            env=env,
            fai_filename=tmp_path.as_posix(),
        )
        popen_proc = Mock()
        popen_proc.wait = Mock(return_value=0)
        popen = Mock(return_value=popen_proc)

        with importlib.resources.as_file(importlib.resources.files(resources) / 'fai_config' / 'release') as release_config_path:
            run(True, popen=popen, dci_path='/nonexistent')

            popen.assert_called_with(
                (
                    'sudo',
                    'env',
                    'PYTHONPATH=/nonexistent',
                    'ENV1=env1',
                    'ENV2=env2',
                    tmp_path.as_posix(),
                    '--verbose',
                    '--hostname', 'debian',
                    '--class', 'CLASS1,CLASS2',
                    '--size', '23G',
                    '--cspace', release_config_path.as_posix(),
                    tmp_path.as_posix(),
                ),
            )

    def test___call___fail(self, tmp_path):
        env = {'ENV1': 'env1', 'ENV2': 'env2'}
        run = RunFAI(
            output_filename=tmp_path,
            release='release',
            classes=['CLASS1', 'CLASS2'],
            size_gb=23,
            env=env,
            fai_filename=tmp_path.as_posix(),
        )
        popen_proc = Mock()
        popen_proc.wait = Mock(return_value=23)
        popen = Mock(return_value=popen_proc)

        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            run(True, popen=popen)

        assert excinfo.value.returncode == 23

    def test___call___noop(self, tmp_path):
        env = {'ENV1': 'env1', 'ENV2': 'env2'}
        run = RunFAI(
            output_filename=tmp_path,
            release='release',
            classes=['CLASS1', 'CLASS2'],
            size_gb=23,
            env=env,
            fai_filename=tmp_path.as_posix(),
        )
        popen = Mock()

        run(False, popen=popen)

        popen.assert_not_called()
