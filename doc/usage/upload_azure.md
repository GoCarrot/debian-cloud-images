# `debian-cloud-images upload-azure`

## Usage

```
debian-cloud-images upload-azure SUBSCRIPTION:GROUP STORAGE
```

### Positional arguments

| Option | Description |
|---|---|
| `SUBSCRIPTION:GROUP` | Azure Subscription and Resource group |
| `STORAGE` | Azure Storage name |

### Optional arguments

| Option | Description |
|---|---|
| `--path PATH` | read manifests and images from |
| `--variant PUBLIC_TYPE` | TODO |
| `--version-override OVERRIDE_VERSION` | TODO |
| `--auth TENANT:APPLICATION:SECRET` | Authentication info for Azure AD application |

## Description

This command creates a private Azure image.

The private Azure image is created in the Azure subscription and resource group specified, using the region of the resource group.

The file is first uploaded to the specified storage, which needs to be located in the same region as the created image.

All files are read and created in the directory the `path` argument points to.

## Examples
