from debian_cloud_images.images.azure_computegallery.s1_item import (
    ImagesAzureComputegalleryItem,
    ImagesAzureComputegalleryItems,
)


class TestImagesAzureComputegalleryItem:
    def test___init__(self, azure_conn, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/compute/galleries/list-by-resource-group#list-galleries-in-a-resource-group.
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/galleries/gallery/images/item?api_version=2021-10-01',
            json={
                "properties": {},
                "name": "item",
            },
        )

        t = ImagesAzureComputegalleryItem(
            'resource_group',
            'gallery',
            'item',
            azure_conn,
        )

        assert t.name == 'item'
        assert t.properties == {}


class TestImagesAzureComputegalleryItems:
    def test___init__(self, azure_conn, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/compute/gallery-images/get#get-a-gallery-image.
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/galleries/gallery/images?api_version=2021-10-01',
            json={
                'value': [
                    {
                        "properties": {},
                        "name": "item",
                    },
                ],
            },
        )

        t = ImagesAzureComputegalleryItems(
            'resource_group',
            'gallery',
            azure_conn
        )

        assert len(t) == 1
        assert t['item'].name == 'item'
        assert t['item'].properties == {}
