from debian_cloud_images.api.cdo.image_config import ImageConfigArch

from debian_cloud_images.images.azure_partnerlegacy.s3_version import (
    ImagesAzurePartnerlegacyVersion,
)


class TestImagesAzurePartnerlegacyVersion:
    def test_create(self, azure_conn, requests_mock):
        requests_mock.get(
            'https://host/api/publishers/publisher/offers/offer?api-version=2017-10-31',
            json={
                'definition': {
                    'plans': [
                        {
                            'planId': 'plan',
                            'microsoft-azure-corevm.vmImagesArchitecture': 'Arch',
                            'microsoft-azure-corevm.vmImagesPublicAzure': {},
                            'diskGenerations': [
                                {
                                    'planId': 'plan-other',
                                    'microsoft-azure-corevm.vmImagesArchitecture': 'Other',
                                    'microsoft-azure-corevm.vmImagesPublicAzure': {},
                                },
                                {
                                    'planId': 'plan-suffix',
                                    'microsoft-azure-corevm.vmImagesArchitecture': 'Arch',
                                    'microsoft-azure-corevm.vmImagesPublicAzure': {},
                                },
                            ],
                        },
                    ],
                },
            },
        )

        put = requests_mock.put(
            'https://host/api/publishers/publisher/offers/offer?api-version=2017-10-31',
        )

        t = ImagesAzurePartnerlegacyVersion(
            'publisher',
            'offer',
            'plan',
            'version',
            azure_conn,
        )
        assert t.create('u', ImageConfigArch(name='arch', azure_name='Arch')) == [
            {
                'description': 'publisher_offer_plan_version',
                'label': 'publisher_offer_plan',
                'mediaName': 'publisher_offer_plan_version',
                'osVhdUrl': 'u',
            },
            {
                'description': 'publisher_offer_plan-suffix_version',
                'label': 'publisher_offer_plan-suffix',
                'mediaName': 'publisher_offer_plan-suffix_version',
                'osVhdUrl': 'u',
            },
        ]

        assert put.last_request.json() == {
            'definition': {
                'plans': [
                    {
                        'planId': 'plan',
                        "microsoft-azure-corevm.vmImagesArchitecture": "Arch",
                        'microsoft-azure-corevm.vmImagesPublicAzure': {
                            'version': {
                                'description': 'publisher_offer_plan_version',
                                'label': 'publisher_offer_plan',
                                'mediaName': 'publisher_offer_plan_version',
                                'osVhdUrl': 'u'
                            },
                        },
                        'diskGenerations': [
                            {
                                'planId': 'plan-other',
                                'microsoft-azure-corevm.vmImagesArchitecture': 'Other',
                                'microsoft-azure-corevm.vmImagesPublicAzure': {},
                            },
                            {
                                'planId': 'plan-suffix',
                                'microsoft-azure-corevm.vmImagesArchitecture': 'Arch',
                                'microsoft-azure-corevm.vmImagesPublicAzure': {
                                    'version': {
                                        'description': 'publisher_offer_plan-suffix_version',
                                        'label': 'publisher_offer_plan-suffix',
                                        'mediaName': 'publisher_offer_plan-suffix_version',
                                        'osVhdUrl': 'u'
                                    },
                                },
                            },
                        ],
                    },
                ],
            },
        }

    def test_get(self, azure_conn, requests_mock):
        requests_mock.get(
            'https://host/api/publishers/publisher/offers/offer?api-version=2017-10-31',
            json={
                'definition': {
                    'plans': [
                        {
                            'planId': 'plan',
                            'microsoft-azure-corevm.vmImagesPublicAzure': {
                                'version': {
                                    'description': 'd',
                                    'label': 'l',
                                    'mediaName': 'm',
                                    'osVhdUrl': 'u',
                                },
                            },
                        },
                    ],
                },
            },
        )

        t = ImagesAzurePartnerlegacyVersion(
            'publisher',
            'offer',
            'plan',
            'version',
            azure_conn,
        )
        assert t.get() == {
            'description': 'd',
            'label': 'l',
            'mediaName': 'm',
            'osVhdUrl': 'u',
        }
