# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

from .base import cli

# Import to register all the commands
from . import (  # noqa: F401
    build,
    build_diskimage,
    build_rootfs,
    cleanup,
    cleanup_azure_partner,
    cleanup_ec2,
    cleanup_ssm,
    configdump,
    control_azure_partner,
    generate_ci,
    update_aws_marketplace,
    upload,
    upload_azure,
    upload_azure_computegallery,
    upload_azure_partner,
    upload_ec2,
    upload_gce,
    put_ssm,
)


def main() -> None:
    cli.main()


if __name__ == '__main__':
    main()
