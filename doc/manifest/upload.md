# Upload manifest

## Supported versions

| Kind | API version |
|---|---|
| `Upload` | `cloud.debian.org/v1alpha1` |

### `Upload`, `cloud.debian.org/v1alpha1`

Each object must contain in a nested object field called "`data`":

* `familyRef`: a provider specific reference to the latest image of this family
* `provider`: the provider API endpoint
* `ref`: a provider specific reference to this exact image

Example:

```json
{
    "apiVersion": "cloud.debian.org/v1alpha1",
    "data": {
        "familyRef": "projects/debian-cloud-experiments/global/images/family/debian-sid-amd64-dev-waldi-manifest-schema",
        "provider": "googleapis.com",
        "ref": "projects/debian-cloud-experiments/global/images/debian-sid-amd64-dev-waldi-manifest-schema-663"
    },
    "kind": "Upload",
    "metadata": {
        "labels": {
            "build.cloud.debian.org/build-id": "waldi-manifest-schema",
            "build.cloud.debian.org/type": "dev",
            "cloud.debian.org/vendor": "gce",
            "cloud.debian.org/version": "663",
            "debian.org/arch": "amd64",
            "debian.org/dist": "debian",
            "debian.org/release": "sid",
            "upload.cloud.debian.org/provider": "cloud.google.com",
            "upload.cloud.debian.org/type": "dev"
        },
        "uid": "b96ea4e0-a5cc-42bf-91c7-65aca1471af0"
    }
}
```
