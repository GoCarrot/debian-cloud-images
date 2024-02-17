# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

import os
import shutil
import subprocess

from debian_cloud_images.utils.sandbox import (
    run_shell,
    SandboxIdmapError,
)


check_no_crun = shutil.which('crun') is None
skip_no_crun = pytest.mark.skipif(check_no_crun, reason='Need available crun')


@skip_no_crun
def test_run_shell(capfd):
    # Workaround for crun wanting a tty
    _, pty = os.openpty()
    try:
        run_shell(
            'echo stdout >&1; echo stderr >&2',
            stdin=pty,
        )
        c = capfd.readouterr()
        # We use terminal mode, so stdout and stderr are multiplexed
        assert c.out == 'stdout\r\nstderr\r\n'
    except SandboxIdmapError:
        pytest.skip('No suitable uid/gid mapping')


@skip_no_crun
def test_run_shell_fail():
    # Workaround for crun wanting a tty
    _, pty = os.openpty()
    try:
        with pytest.raises(subprocess.CalledProcessError):
            run_shell(
                'exit 1',
                stdin=pty,
            )
    except SandboxIdmapError:
        pytest.skip('No suitable uid/gid mapping')
