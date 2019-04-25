class TestEtc:
    def test_etc_cloud_release(self, image_path):
        assert (image_path / 'etc' / 'cloud-release').exists()

    def test_etc_default_locale(self, image_path):
        p = (image_path / 'etc' / 'default' / 'locale')
        assert p.exists(), '/etc/default/locale does not exist'

        with p.open() as f:
            assert f.read() == 'LANG=C.UTF-8\n', 'Default locale is not C.UTF-8'

    def test_etc_fstab(self, image_path):
        assert (image_path / 'etc' / 'fstab').exists()
