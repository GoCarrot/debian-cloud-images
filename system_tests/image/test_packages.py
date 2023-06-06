import pytest


class TestPackages:
    def test_packages_status_status(self, image_packages):
        if image_packages.status_status != 'installed':
            pytest.fail(
                f'dpkg db includes package "{image_packages.name}" with wrong status "{image_packages.status_status}"',
                pytrace=False,
            )

    def test_packages_status_want(self, image_packages):
        if image_packages.status_want != 'install':
            pytest.fail(
                f'dpkg db includes package "{image_packages.name}" with wrong want status "{image_packages.status_want}"',
                pytrace=False,
            )
