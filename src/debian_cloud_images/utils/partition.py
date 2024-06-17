# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import dataclasses
import enum
from pathlib import Path
from typing import BinaryIO
from subprocess import run
from uuid import UUID


@dataclasses.dataclass
class PartitionTypeEntry:
    uuid: UUID


class PartitionType(PartitionTypeEntry, enum.Enum):
    ESP = UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b')
    ROOT_AMD64 = UUID('4f68bce3-e8cd-4db1-96e7-fbcaf984b709')
    BOOT_AMD64 = UUID('21686148-6449-6e6f-744e-656564454649')


@dataclasses.dataclass
class PartitionEntry:
    SECTOR_SIZE = 512

    file: Path
    type_: PartitionType
    uuid: UUID
    nr: int
    start: int
    size: int

    @property
    def start_sector(self) -> int:
        return self.start // self.SECTOR_SIZE

    def copy_in(self, fsrc: BinaryIO) -> None:
        with self.file.open('rb+') as fdst:
            fsrc.seek(0)
            fdst.seek(self.start)

            fsrc_read = fsrc.read
            fdst_write = fdst.write
            while True:
                buf = fsrc_read(16 * 1024 * 1024)
                if not buf:
                    break
                fdst_write(buf)

    def copy_in_bytes(self, src: bytes) -> None:
        if len(src) > self.size:
            raise ValueError

        with self.file.open('rb+') as fdst:
            fdst.seek(self.start)
            fdst.write(src)

    @property
    def _format_sfdisk(self) -> str:
        start = self.start // self.SECTOR_SIZE
        size = self.size // self.SECTOR_SIZE
        return f'p{self.nr} : start={start}, size={size}, type={self.type_.uuid!s}, uuid={self.uuid!s}'


@dataclasses.dataclass
class Partition:
    ALIGN = 1024 * 1024

    file: Path
    size: int
    entries: list[PartitionEntry] = dataclasses.field(init=False, default_factory=list)

    def _get_start(self) -> int:
        if e := self.entries:
            return e[-1].start + e[-1].size
        return self.ALIGN

    def _get_size(self, start: int, size: int | None) -> int:
        if size is not None:
            if start + size + self.ALIGN >= self.size:
                raise ValueError('Partition too large')
            return size
        return self.size - self.ALIGN - start

    def add(
        self,
        type_: PartitionType,
        uuid: UUID,
        nr: int,
        size: int | None = None,
    ) -> PartitionEntry:
        start = self._get_start()
        size = self._get_size(start, size)

        entry = PartitionEntry(self.file, type_, uuid, nr, start, size)
        self.entries.append(entry)
        return entry

    @property
    def _format_sfdisk(self) -> str:
        ret = [
            'label: gpt',
            'unit: sectors',
            'sector-size: 512',
        ] + [
            i._format_sfdisk for i in self.entries
        ]
        return '\n'.join(ret) + '\n'

    def write(self) -> None:
        with self.file.open('ab') as f:
            f.truncate(self.size)
        run(
            [
                'sfdisk',
                str(self.file),
            ],
            check=True,
            input=self._format_sfdisk.encode('ascii'),
        )
