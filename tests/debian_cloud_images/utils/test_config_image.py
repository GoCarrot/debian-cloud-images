from debian_cloud_images.utils.config_image import ConfigImageLoader


class TestConfigImage:
    def test_default_filenames(self, monkeypatch):
        monkeypatch.setenv('XDG_CONFIG_DIRS', '/dirs1/root:/dirs2/root')
        monkeypatch.setenv('XDG_CONFIG_HOME', '/home1/root:/home2/root')

        filenames = [i.as_posix() for i in ConfigImageLoader._default_filenames('name')]

        assert filenames == [
            '/home1/root/debian-cloud-images/name',
            '/home2/root/debian-cloud-images/name',
            '/dirs1/root/debian-cloud-images/name',
            '/dirs2/root/debian-cloud-images/name',
        ]
