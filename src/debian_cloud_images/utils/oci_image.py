# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OciBlobInfo:
    algorithm: str
    enc: str
    size: int

    @property
    def digest(self) -> str:
        return f'{self.algorithm}:{self.enc}'

    @property
    def filename(self) -> str:
        return f'blobs/{self.algorithm}/{self.enc}'


class OciImage:
    _base: Path
    _blobs: Path

    def __init__(self, base: Path) -> None:
        self._base = base
        self._blobs = base / 'blobs' / 'sha256'

        layout = base / 'oci-layout'
        if not base.is_dir():
            base.mkdir()
            with layout.open('w') as f:
                json.dump({
                    'imageLayoutVersion': '1.0.0',
                }, f)
        else:
            with layout.open('r') as f:
                if (v := json.load(f).get('imageLayoutVersion')) != '1.0.0':
                    raise AttributeError(f'Directory exists, found unsupported version {v}')

        self._blobs.mkdir(parents=True, exist_ok=True)

    def store_blob(self, content: dict[str, str | int | dict | list]) -> OciBlobInfo:
        data = json.dumps(content).encode('utf-8')
        enc = hashlib.sha256(data).hexdigest()
        path = self._blobs / enc
        with path.open('wb') as f:
            f.write(data)
        return OciBlobInfo('sha256', enc, len(data))

    def store_blob_from_tmp(self, name: str) -> OciBlobInfo:
        path_in = self._base / 'tmp' / name
        with path_in.open('rb') as f:
            enc = hashlib.file_digest(f, 'sha256').hexdigest()
        size = path_in.stat().st_size
        path = self._blobs / enc
        path.hardlink_to(path_in)
        return OciBlobInfo('sha256', enc, size)

    def store_index(self, content: dict[str, str | int | dict | list]) -> None:
        data = json.dumps(content).encode('utf-8')
        path = self._base / 'index.json'
        with path.open('wb') as f:
            f.write(data)
