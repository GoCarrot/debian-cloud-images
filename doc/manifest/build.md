# Build manifest

TODO: re-do definition of the whole `info` field.

## Supported versions

| Kind | API version |
|---|---|
| `Build` | `cloud.debian.org/v1alpha1` |

### `Build`, `cloud.debian.org/v1alpha1`

Each object must contain in a nested object field called "`data`":

* `info`: build config, a nested object including:
  * `arch`
  * `build_id`
  * `release`
  * `release_id`
  * `type`
  * `vendor`
  * `version`
* `packages`: a list of objects, for each package included into the image:
  * `name`: name of package
  * `version`: versions of package

Example:

```json
{
    "apiVersion": "cloud.debian.org/v1alpha1",
    "data": {
        "info": {
            "arch": "amd64",
            "build_id": "waldi-manifest-schema",
            "release": "sid",
            "release_id": "sid",
            "type": "dev",
            "vendor": "gce",
            "version": "663"
        },
        "packages": [
            {
                "name": "adduser",
                "version": "3.118"
            }
    },
    "kind": "Build",
    "metadata": {
        "labels": {
            "build.cloud.debian.org/build-id": "waldi-manifest-schema",
            "build.cloud.debian.org/type": "dev",
            "cloud.debian.org/vendor": "gce",
            "cloud.debian.org/version": "663",
            "debian.org/arch": "amd64",
            "debian.org/dist": "debian",
            "debian.org/release": "sid"
        },
        "uid": "ed21b645-c9a1-40e3-8d23-04ae8ee67ff6"
    }
}
```
