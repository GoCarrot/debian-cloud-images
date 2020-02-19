# SPDX-License-Identifier: GPL-2.0-or-later

import json
import logging
import pathlib

from ..api.registry import registry as api_registry


logger = logging.getLogger(__name__)


class CreateManifest:
    input_filename: pathlib.Path
    output_filename: pathlib.Path

    def __init__(
            self, *,
            input_filename: pathlib.Path,
            output_filename: pathlib.Path,
    ):
        self.input_filename = input_filename
        self.output_filename = output_filename

    def __call__(self, run: bool) -> None:
        if not run:
            return

        with self.input_filename.open() as f:
            manifest = api_registry.load(json.load(f))

        with self.output_filename.open('w') as f:
            json.dump(api_registry.dump(manifest), f, indent=4, separators=(',', ': '), sort_keys=True)
