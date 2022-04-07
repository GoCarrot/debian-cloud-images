from debian_cloud_images.images.azure_partnerlegacy.s1_offer import (
    ImagesAzurePartnerlegacyOffer,
)


class TestImagesAzurePartnerlegacyOffer:
    data = {
        'test': 'test',
    }

    def test_get(self, azure_conn, requests_mock):
        requests_mock.get(
            'https://host/api/publishers/publisher/offers/offer?api-version=2017-10-31',
            json=self.data.copy(),
        )

        t = ImagesAzurePartnerlegacyOffer(
            'publisher',
            'offer',
            azure_conn,
        )

        assert t.get() == self.data

    def test_put(self, azure_conn, requests_mock):
        put = requests_mock.put(
            'https://host/api/publishers/publisher/offers/offer?api-version=2017-10-31',
        )

        t = ImagesAzurePartnerlegacyOffer(
            'publisher',
            'offer',
            azure_conn,
        )

        t.put(self.data.copy())

        assert put.last_request.json() == self.data

    def test_control_golive(self, azure_conn, requests_mock):
        post = requests_mock.post(
            'https://host/api/publishers/publisher/offers/offer/golive?api-version=2017-10-31',
        )

        t = ImagesAzurePartnerlegacyOffer(
            'publisher',
            'offer',
            azure_conn,
        )

        t.control_golive()

        assert post.last_request.text is None

    def test_control_publish(self, azure_conn, requests_mock):
        post = requests_mock.post(
            'https://host/api/publishers/publisher/offers/offer/publish?api-version=2017-10-31',
        )

        t = ImagesAzurePartnerlegacyOffer(
            'publisher',
            'offer',
            azure_conn,
        )

        t.control_publish()

        assert post.last_request.json()
