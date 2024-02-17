# SPDX-License-Identifier: GPL-2.0-or-later

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
    assert pdev.vendor_family == 'debian-release-arch-dev-buildid'
    assert pdev.vendor_name == 'debian-release-arch-dev-buildid-version'
    assert pdev.vendor_description

    pdaily = ImagePublicInfo(
        public_type=ImagePublicType.daily,
    ).apply(info)
    assert pdaily.vendor_family == 'debian-release-arch-daily'
    assert pdaily.vendor_name == 'debian-release-arch-daily-version'
    assert pdaily.vendor_description

    prelease = ImagePublicInfo(
        public_type=ImagePublicType.release,
    ).apply(info)
    assert prelease.vendor_family == 'debian-release-arch'
    assert prelease.vendor_name == 'debian-release-arch-version'
    assert prelease.vendor_description


def test_ImagePublicInfo_field_gce():
    len_max = 63
    len_release = 32
    len_arch = 32
    len_version = 8
    assert len_max < len_release + len_arch + len_version

    info = {
        'release_id': 'r' * len_release,
        'arch': 'a' * len_arch,
        'build_id': '',
        'version': 'v' * len_version,
    }

    p = ImagePublicInfo().apply(info)
    assert len(p.vendor_name63) == len_max
    assert len(p.vendor_gce_family) == len_max
    assert p.vendor_name63[-len_version:] == 'v' * len_version


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
