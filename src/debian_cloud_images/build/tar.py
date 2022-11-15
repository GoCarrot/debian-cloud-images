# SPDX-License-Identifier: GPL-2.0-or-later

import base64
import hashlib
import logging
import pathlib
import subprocess


logger = logging.getLogger(__name__)


BUF_SIZE = 16 * 1024 * 1024


class RunTar:
    input_filename: pathlib.Path
    output_filename: pathlib.Path
    inner_filename: str

    def __init__(
            self, *,
            input_filename: pathlib.Path,
            output_filename: pathlib.Path,
            inner_filename: str='disk.raw',  # noqa:E252
    ):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.inner_filename = inner_filename

    def __call__(self, run: bool, *, popen=subprocess.Popen) -> str:
        cmd = self.command
        output_hash = hashlib.sha512()

        if run:
            logger.info(f'Running tar: {" ".join(cmd)}')

            with self.output_filename.open('wb') as output:
                try:
                    process = popen(cmd, bufsize=0, stdout=subprocess.PIPE)

                    while True:
                        o = process.stdout.read(BUF_SIZE)
                        if len(o) == 0:
                            break
                        output.write(o)
                        output_hash.update(o)

                    retcode = process.wait()
                    if retcode:
                        raise subprocess.CalledProcessError(retcode, cmd)

                finally:
                    process.kill()

        else:
            logger.info(f'Would run tar: {" ".join(cmd)}')

        output_digest = base64.b64encode(output_hash.digest()).decode().rstrip('=')
        digest = f'{output_hash.name}:{output_digest}'

        logger.info(f'Image tar digest: {digest}')

        return digest

    @property
    def command(self) -> tuple:
        return (
            'tar',
            '--create',
            '--absolute-names',
            '--sparse',
            '--transform', r's/.*/' + self.inner_filename + '/',
            self.input_filename.as_posix(),
        )
