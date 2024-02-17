# SPDX-License-Identifier: GPL-2.0-or-later

import pytest


class TestPackages:
    def test_packages_status_status(self, image_packages_entry):
        if image_packages_entry.status_status != 'installed':
            pytest.fail(
                f'dpkg db includes package "{image_packages_entry.name}" with wrong status "{image_packages_entry.status_status}"',
                pytrace=False,
            )

    def test_packages_status_want(self, image_packages_entry):
        if image_packages_entry.status_want != 'install':
            pytest.fail(
                f'dpkg db includes package "{image_packages_entry.name}" with wrong want status "{image_packages_entry.status_want}"',
                pytrace=False,
            )
