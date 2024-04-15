# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

import sys

from debian_cloud_images.utils.oci_image import OciImage


class TestOciImage:
    def test_init(self, tmp_path):
        image_path = tmp_path / 'image'

        OciImage(image_path)

        assert (image_path / 'oci-layout').exists()
        assert (image_path / 'blobs').exists()

    def test_init_exist(self, tmp_path):
        image_path = tmp_path / 'image'
        image_path.mkdir()
        with (image_path / 'oci-layout').open('w') as f:
            f.write('{"imageLayoutVersion": "1.0.0"}')

        OciImage(image_path)

        assert (image_path / 'blobs').exists()

    def test_init_exist_fail(self, tmp_path):
        image_path = tmp_path / 'image'
        image_path.mkdir()

        with pytest.raises(FileNotFoundError):
            OciImage(image_path)

    def test_init_exist_wrong_layout(self, tmp_path):
        image_path = tmp_path / 'image'
        image_path.mkdir()
        with (image_path / 'oci-layout').open('w') as f:
            f.write('{}')

        with pytest.raises(AttributeError):
            OciImage(image_path)

    def test_store_blob(self, tmp_path):
        image_path = tmp_path / 'image'

        i = OciImage(image_path)
        n = i.store_blob({})

        assert n.algorithm == 'sha256'
        assert n.enc == '44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
        assert n.digest == 'sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
        assert n.filename == 'blobs/sha256/44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'

        blob_path = image_path / n.filename
        with blob_path.open('r') as f:
            assert f.read() == '{}'

        assert n.size == blob_path.stat().st_size

    @pytest.mark.skipif(sys.version_info < (3, 11), reason='requires python3.11 or higher')
    def test_store_blob_from_tmp(self, tmp_path):
        image_path = tmp_path / 'image'

        i = OciImage(image_path)

        imagetmp_path = image_path / 'tmp'
        imagetmp_path.mkdir()
        with (imagetmp_path / 'file').open('w') as f:
            f.write('{}')

        n = i.store_blob_from_tmp('file')

        assert n.algorithm == 'sha256'
        assert n.enc == '44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
        assert n.digest == 'sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
        assert n.filename == 'blobs/sha256/44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'

        blob_path = image_path / n.filename
        with blob_path.open('r') as f:
            assert f.read() == '{}'

        assert n.size == blob_path.stat().st_size

    def test_store_index(self, tmp_path):
        image_path = tmp_path / 'image'

        i = OciImage(image_path)
        i.store_index({})

        blob_path = image_path / 'index.json'
        with blob_path.open('r') as f:
            assert f.read() == '{}'
