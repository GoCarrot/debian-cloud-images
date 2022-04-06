from debian_cloud_images.images.azure_computeimage.s1_image import (
    ImagesAzureComputeimageImage,
)


class TestImagesAzureComputeimageImage:
    def test___init__(self, azure_conn, requests_mock):
        # https://docs.microsoft.com/en-us/rest/api/compute/images/get
        requests_mock.get(
            'https://host/subscriptions/subscription/resourceGroups/resource_group/providers/Microsoft.Compute/images/image?api-version=2021-10-01',
            json={
                'name': 'image',
                'properties': {},
            },
        )

        t = ImagesAzureComputeimageImage(
            'resource_group',
            'image',
            azure_conn,
        )

        assert t.name == 'image'
