from debian_cloud_images.cli.build import (
    ArchEnum,
    ReleaseEnum,
)


class TestCommand:
    def test_check(self):
        sid = ReleaseEnum.sid
        amd64 = ArchEnum.amd64
        arm64 = ArchEnum.arm64
        ppc64el = ArchEnum.ppc64el

        assert sid.supports_linux_image_cloud_for_arch(amd64.name) is True
        assert sid.supports_linux_image_cloud_for_arch(arm64.name) is True
        assert sid.supports_linux_image_cloud_for_arch(ppc64el.name) is False
