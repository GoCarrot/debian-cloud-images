# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import grp
import json
import os
import pwd
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from typing import (
    Any,
    IO,
)


class SandboxIdmapError(ValueError):
    pass


@dataclass
class OciBundle:
    cmd: str
    bindmounts: list[tuple[Path, Path, bool]]
    env: dict[str, str]

    uid: int = field(default_factory=os.getuid)
    gid: int = field(default_factory=os.getgid)
    subuid: int = field(default=0)
    subgid: int = field(default=0)

    def __post_init__(self) -> None:
        self.bindmounts.append((Path('/etc/resolv.conf'), Path('/etc/resolv.conf'), False))
        self.bindmounts.append((Path('/etc/ssl/certs'), Path('/etc/ssl/certs'), False))
        self.bindmounts.append((Path('/usr'), Path('/usr'), False))

        if self.subuid == 0:
            self.subuid = self.subuid_base()
        if self.subgid == 0:
            self.subgid = self.subgid_base()

    def create(self, p: Path) -> None:
        self._rootfs(p)
        with (p / 'config.json').open('w') as f:
            json.dump(self.config, f)

    def _rootfs(self, p: Path) -> None:
        r = p / 'rootfs'
        r.mkdir()
        for i in ('dev', ):
            (r / i).mkdir()
        for i in ('bin', 'lib', 'lib32', 'lib64', 'sbin'):
            (r / i).symlink_to(f'usr/{i}')

    @property
    def config(self) -> dict[str, Any]:
        return {
            'ociVersion': '1.0.1',
            'process': {
                'args': [
                    '/bin/bash',
                    '-c',
                    self.cmd,
                ],
                'cwd': '/',
                'env': [f'{i}={j}' for i, j in self.env.items()],
                'terminal': True,
                'user': {
                    'uid': 0,
                    'gid': 0,
                    'umask': 18,
                },
                'capabilities': {
                    'bounding': [
                        'CAP_CHOWN',
                        'CAP_DAC_OVERRIDE',
                        'CAP_FOWNER',
                        'CAP_SETFCAP',
                        'CAP_SETGID',
                        'CAP_SETUID',
                        'CAP_SYS_ADMIN',
                        'CAP_SYS_CHROOT',
                        'CAP_SYS_PTRACE',
                    ],
                    'inheritable': [
                        'CAP_CHOWN',
                        'CAP_DAC_OVERRIDE',
                        'CAP_FOWNER',
                        'CAP_SETFCAP',
                        'CAP_SETGID',
                        'CAP_SETUID',
                        'CAP_SYS_ADMIN',
                        'CAP_SYS_CHROOT',
                        'CAP_SYS_PTRACE',
                    ],
                },
            },
            'root': {
                'path': 'rootfs',
                'readonly': True,
            },
            'linux': {
                'namespaces': [
                    {'type': 'mount'},
                    {'type': 'pid'},
                    {'type': 'user'},
                ],
                'uidMappings': [
                    {
                        'containerID': 0,
                        'hostID': self.uid,
                        'size': 1,
                    },
                    {
                        'containerID': 1,
                        'hostID': self.subuid,
                        'size': 999,
                    },
                    {
                        'containerID': 65534,
                        'hostID': self.subuid + 999,
                        'size': 1,
                    },
                ],
                'gidMappings': [
                    {
                        'containerID': 0,
                        'hostID': self.gid,
                        'size': 1,
                    },
                    {
                        'containerID': 1,
                        'hostID': self.subgid,
                        'size': 999,
                    },
                    {
                        'containerID': 65534,
                        'hostID': self.subgid + 999,
                        'size': 1,
                    },
                ],
            },
            'mounts': [
                {
                    'destination': '/dev/pts',
                    'type': 'devpts',
                    'source': 'devpts',
                    'options': [
                        'nosuid',
                        'noexec',
                        'newinstance',
                        'ptmxmode=0666',
                        'mode=0620',
                        'gid=5',
                    ],
                },
                {
                    'destination': '/proc',
                    'type': 'proc',
                    'source': 'proc',
                },
                {
                    'destination': '/target',
                    'type': 'tmpfs',
                    'source': '/run/target',
                    'options': [
                        'mode=0755',
                    ],
                }
            ] + [
                {
                    'destination': i,
                    'type': 'tmpfs',
                    'source': 'none',
                } for i in ('/run', '/tmp', '/var/run')
            ] + [
                {
                    'destination': str(destination),
                    'options': ['rbind', 'nodev', 'nosuid', 'rw' if readwrite else 'ro'],
                    'type': 'none',
                    'source': str(source),
                }
                for source, destination, readwrite in self.bindmounts
            ],
        }

    def subgid_base(self) -> int:
        gname = grp.getgrgid(self.gid).gr_name
        try:
            return self._idmap_base(Path('/etc/subgid'), str(self.gid), gname)
        except SandboxIdmapError:
            if self.gid == 0:
                return 1
            raise

    def subuid_base(self) -> int:
        uname = pwd.getpwuid(self.uid).pw_name
        try:
            return self._idmap_base(Path('/etc/subuid'), str(self.uid), uname)
        except SandboxIdmapError:
            if self.gid == 0:
                return 1
            raise

    def _idmap_base(self, p: Path, *match: str) -> int:
        if not p.is_file():
            raise SandboxIdmapError(f'{p} does not exist')
        with p.open() as f:
            for line in f:
                if line:
                    i = line.split(':', 2)
                    if i[0] in match and int(i[2]) >= 1000:
                        return int(i[1])
        raise SandboxIdmapError(f'Unable to find large enough mapping in {p} mathing current user or group')


def run_shell(
    cmd: str,
    *,
    bindmounts: list[tuple[Path, Path, bool]] = [],
    stdin: IO[Any] | int | None = None,
    env: dict[str, str] = {},
) -> CompletedProcess:
    with TemporaryDirectory(prefix='debian-cloud-images-sandbox') as d:
        p = Path(d)
        OciBundle(cmd, bindmounts, env).create(p)

        return subprocess.run(
            ['crun', 'run', f'--bundle={p}', p.name],
            stdin=stdin,
            check=True,
        )
