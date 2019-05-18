class TestBin:
    def test_bin_qemu(self, image_path):
        assert len(list((image_path / 'usr/bin').glob('qemu-*'))) == 0
