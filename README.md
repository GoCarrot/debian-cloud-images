# FAI Cloud image builder

This repository aims to build Debian images for all cloud providers

## Getting started

You will need a checkout of this repository on your disk and a recent fai-server
package (at least 5.7) installed. Install the necessary fai packages without
the recommends (which avoids turning your host into a DHCP server!).

```
  # git clone https://salsa.debian.org/cloud-team/debian-cloud-images.git
  # sudo apt install --no-install-recommends ca-certificates debsums dosfstools \
    fai-server fai-setup-storage fdisk make python3 python3-libcloud python3-marshmallow \
    python3-pytest python3-yaml qemu-utils udev
```

  Call `make help` and follow the instructions

Example 1:

```
   # make image_sid_nocloud_amd64
```

This will create some log output and the following files:

- `image_sid_nocloud_amd64.build.json`
- `image_sid_nocloud_amd64.info`
- `image_sid_nocloud_amd64.raw`
- `image_sid_nocloud_amd64.tar`

Example 2:

```
    # make image_sid_genericcloud_amd64
```

- `image_sid_genericcloud_amd64.build.json`
- `image_sid_genericcloud_amd64.info`
- `image_sid_genericcloud_amd64.raw`
- `image_sid_genericcloud_amd64.tar`

These images can be used with QEMU-KVM, Virtualbox or any other virtualization
backend that support raw disk images.

You can login as root on the VM console without a password (but not over
SSH), and there are no other users. You can add new users using `adduser` as
usual, and you probably want to add them to the `sudo` group.

After the disk image is created you can try it with kvm, and wait 5s for the
boot sequence to start:

```
    # kvm -nic user,model=virtio -m 1024 -drive format=raw,file=image-sid-genericcloud-amd64.raw
```

## Supported image types

As shown above, various types of images can be built for different use
cases. Each type of image can be built with the following command:

```
    # make image_<suite>_<type>_<arch>
```

where `<suite>` is a supported Debian release codename
(e.g. `bookworm`, `trixie`, or `sid`). `<type>` can be any of the
following:

 * `azure`: Optimized for Microsoft's cloud computing platform Azure
 * `ec2`: Optimized for the Amazon Elastic Compute Cloud (EC2)
 * `gce`: Optimized for the Google Cloud Engine
 * `generic`: Should run in any environment
 * `genericcloud`: Should run in any virtualised environment. Is
   smaller than `generic` by excluding drivers for physical hardware.
 * `nocloud`: Mostly useful for testing the build process
   itself. Doesn't have cloud-init installed, but instead allows root
   login without a password.

## Documentation

 * [Details about creating images](doc/details.md)
 * https://fai-project.org/fai-guide/
 * https://noah.meyerhans.us/blog/2017/02/10/using-fai-to-customize-and-build-your-own-cloud-images/

## New cloud vendor how-to

First of all, we are pretty confident that `generic-vm-image` should boot
mostly everywhere. If you really need adjustments for your image, start looking
at the directory structure and only drop in adjustments where really required.
Our CLOUD (base) class should already take care of the most of what is needed
for a cloud image.
