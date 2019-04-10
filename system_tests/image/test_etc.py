class TestEtc:
    def test_etc_cloud_release(self, image_path):
        assert (image_path / 'etc' / 'cloud-release').exists()

    def test_etc_fstab(self, image_path):
        assert (image_path / 'etc' / 'fstab').exists()
