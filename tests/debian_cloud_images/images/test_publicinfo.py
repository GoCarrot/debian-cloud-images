import pytest

from debian_cloud_images.images.publicinfo import ImagePublicInfo, ImagePublicType


def test_ImagePublicInfo():
    ImagePublicInfo()


def test_ImagePublicInfo_field():
    info = {
        'release_id': 'release',
        'arch': 'arch',
        'build_id': 'buildid',
        'version': 'version',
    }

    pdev = ImagePublicInfo(
        public_type=ImagePublicType.dev,
    ).apply(info)
    assert pdev.vendor_name == 'debian-release-arch-dev-buildid-version'

    pdaily = ImagePublicInfo(
        public_type=ImagePublicType.daily,
    ).apply(info)
    assert pdaily.vendor_name == 'debian-release-arch-daily-version'

    prelease = ImagePublicInfo(
        public_type=ImagePublicType.release,
    ).apply(info)
    assert prelease.vendor_name == 'debian-release-arch-version'


def test_ImagePublicInfo_field_override():
    info = {
        'release_id': 'release',
        'arch': 'arch',
        'build_id': 'buildid',
        'version': 'version',
    }
    override_info = {
        'version': 'override',
    }

    pdev = ImagePublicInfo(
        public_type=ImagePublicType.dev,
        override_info=override_info,
    ).apply(info)
    assert pdev.vendor_name == 'debian-release-arch-dev-buildid-override'

    pdaily = ImagePublicInfo(
        public_type=ImagePublicType.daily,
        override_info=override_info,
    ).apply(info)
    assert pdaily.vendor_name == 'debian-release-arch-daily-override'

    prelease = ImagePublicInfo(
        public_type=ImagePublicType.release,
        override_info=override_info,
    ).apply(info)
    assert prelease.vendor_name == 'debian-release-arch-override'


def test_ImagePublicInfo_field_unknown():
    p = ImagePublicInfo().apply({})

    with pytest.raises(KeyError):
        p.undefined
