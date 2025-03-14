# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

import shutil
import subprocess

from debian_cloud_images.utils.sandbox import (
    run_shell,
    SandboxIdmapError,
)


check_no_crun = shutil.which('crun') is None
skip_no_crun = pytest.mark.skipif(check_no_crun, reason='Need available crun')


@skip_no_crun
def test_run_shell():
    try:
        s = run_shell(
            'echo stdout >&1; echo stderr >&2',
            stdout=subprocess.PIPE,
        )
        assert s.stdout == b'stdout\nstderr\n'
    except SandboxIdmapError:
        pytest.skip('No suitable uid/gid mapping')


@skip_no_crun
def test_run_shell_fail():
    try:
        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            run_shell(
                'exit 1',
                stdout=subprocess.PIPE,
            )
        assert excinfo.value.returncode == 1
    except SandboxIdmapError:
        pytest.skip('No suitable uid/gid mapping')
