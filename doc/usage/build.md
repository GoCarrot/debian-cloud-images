# `debian-cloud-images build`

## Usage

```
debian-cloud-images build RELEASE VENDOR ARCH
```

### Positional arguments

| Option | Description |
|---|---|
| `RELEASE` | Debian release to build |
| `VENDOR` | Vendor to build image for |
| `ARCH` | Architecture or sub-architecture to build image for |

### Optional arguments

| Option | Description |
|---|---|
| `--build-id ID` | TODO |
| `--build-type TYPE` | Type of image to build |
| `--noop` | TODO |
| `--localdebs` | Read extra debs from localdebs directory |
| `--path PATH` | write manifests and images to |
| `--override-name OVERRIDE_NAME` | override name of output |
| `--version VERSION` | version of image |
| `--version-date VERSION_DATE` | date part of version |

## Description

This command builds a Debian Cloud image.

It leverages FAI and `fai-diskimage` to do the actual work.

The output is an intermediate image file and a build manifest including information about the image.
This files are created in the directory the `path` argument points to.

## Examples
