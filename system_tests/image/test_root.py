class TestRoot:
    def test_initrdimg(self, image_path):
        assert not (image_path / 'initrd.img').exists()

    def test_vmlinux(self, image_path):
        assert not (image_path / 'vmlinux').exists()

    def test_vmlinuz(self, image_path):
        assert not (image_path / 'vmlinuz').exists()
