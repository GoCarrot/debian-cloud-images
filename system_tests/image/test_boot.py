import pytest


class TestBootGce:
    @pytest.fixture(scope="class", autouse=True)
    def check_vendor(self, image_info):
        if image_info.build_info['vendor'] != 'gce':
            pytest.skip('Image vendor is not gce')

    def test_boot_efi_google(self, image_path):
        assert (image_path / 'boot/efi/EFI/Google/gsetup').exists()
