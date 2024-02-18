# SPDX-License-Identifier: GPL-2.0-or-later

import importlib.resources
import logging
import pathlib
import os.path
import subprocess

from typing import Dict, List

from .. import resources


dci_path = os.path.join(os.path.dirname(__file__), '../..')
logger = logging.getLogger(__name__)


class RunFAI:
    output_filename: pathlib.Path
    release: str
    classes: List[str]
    size_gb: int
    env: Dict[str, str]
    fai_filename: str

    def __init__(
            self, *,
            output_filename: pathlib.Path,
            release: str,
            classes: List[str],
            size_gb: int,
            env: Dict[str, str],
            fai_filename: str='fai-diskimage',  # noqa:E252
    ):
        self.output_filename = output_filename
        self.release = release
        self.classes = classes
        self.size_gb = size_gb
        self.env = env
        self.fai_filename = fai_filename

    def __call__(self, run: bool, *, popen=subprocess.Popen, dci_path=dci_path) -> None:
        with importlib.resources.as_file(importlib.resources.files(resources) / 'fai_config' / self.release) as release_config_path:
            cmd = self.command(dci_path, release_config_path.as_posix())

            if run:
                logger.info(f'Running FAI: {" ".join(cmd)}')

                try:
                    process = popen(cmd)
                    retcode = process.wait()
                    if retcode:
                        raise subprocess.CalledProcessError(retcode, cmd)

                finally:
                    process.kill()

            else:
                logger.info(f'Would run FAI: {" ".join(cmd)}')

    def command(self, dci_path: str, config_path: str) -> tuple:
        return (
            'sudo',
            'env',
            f'PYTHONPATH={dci_path}',
        ) + tuple(f'{k}={v}' for k, v in sorted(self.env.items())) + (
            self.fai_filename,
            '--verbose',
            '--hostname', 'debian',
            '--class', ','.join(self.classes),
            '--size', f'{self.size_gb}G',
            '--cspace', config_path,
            self.output_filename.as_posix(),
        )
