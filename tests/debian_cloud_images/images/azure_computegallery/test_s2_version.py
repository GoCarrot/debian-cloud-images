from debian_cloud_images.images.azure_computegallery.s2_version import (
    ImagesAzureComputegalleryVersion,
    ImagesAzureComputegalleryVersions,
)


class TestImagesAzureComputegalleryVersion:
    def test___init__(self, azure_conn, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/compute/gallery-image-versions/get#get-a-gallery-image-version-with-replication-status.
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/galleries/gallery/images/item/versions/version?api-version=2021-10-01',
            json={
                "properties": {},
                "name": "version",
            },
        )

        t = ImagesAzureComputegalleryVersion(
            'resource_group',
            'gallery',
            'item',
            'version',
            azure_conn,
        )

        assert t.name == 'version'


class TestImagesAzureComputegalleryVersions:
    def test___init__(self, azure_conn, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/compute/gallery-image-versions/list-by-gallery-image#list-gallery-image-versions-in-a-gallery-image-definition.
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/galleries/gallery/images/item/versions?api-version=2021-10-01',
            json={
                'value': [
                    {
                        "properties": {},
                        "name": "version",
                    },
                ],
            },
        )

        t = ImagesAzureComputegalleryVersions(
            'resource_group',
            'gallery',
            'item',
            azure_conn
        )

        assert len(t) == 1
        assert t['version'].name == 'version'
