class TestBin:
    def test_bin_qemu(self, image_path):
        exist = frozenset(i.name for i in (image_path / 'usr/bin').glob('qemu-*'))
        ignore = frozenset(('qemu-img', 'qemu-io', 'qemu-nbd'))
        assert len(exist - ignore) == 0
