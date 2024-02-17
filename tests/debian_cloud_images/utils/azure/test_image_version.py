# SPDX-License-Identifier: GPL-2.0-or-later

import pytest

from debian_cloud_images.utils.azure.image_version import AzureImageVersion


def test_init():
    v = AzureImageVersion(1, 2, 3)
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3


def test_init_str():
    v = AzureImageVersion('1', '2', '3')
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3


def test_hash():
    hash(AzureImageVersion(1, 2, 3))


def test_from_string():
    v = AzureImageVersion.from_string('1.2.3')
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3


@pytest.mark.parametrize(
    'a,b,res',
    [
        ('1.1.1', '1.1.1', True),
        ('1.1.1', '2.1.1', False),
        ('1.1.1', '1.2.1', False),
        ('1.1.1', '1.1.2', False),
    ],
)
def test_eq(a, b, res):
    va = AzureImageVersion.from_string(a)
    vb = AzureImageVersion.from_string(b)

    if res:
        assert va == vb
        assert not va != vb
        assert va <= vb
        assert va >= vb
    else:
        assert not va == vb
        assert va != vb


@pytest.mark.parametrize(
    'a,b,res',
    [
        ('1.1.1', '1.1.1', False),
        ('1.1.1', '0.0.2', False),
        ('1.1.1', '0.2.2', False),
        ('1.1.1', '1.0.0', False),
        ('1.1.1', '1.0.2', False),
        ('1.1.1', '1.2.2', True),
        ('1.1.1', '1.1.0', False),
        ('1.1.1', '1.1.2', True),
    ],
)
def test_lt(a, b, res):
    va = AzureImageVersion.from_string(a)
    vb = AzureImageVersion.from_string(b)

    if res:
        assert va < vb
        assert not va > vb
    else:
        assert not va < vb
