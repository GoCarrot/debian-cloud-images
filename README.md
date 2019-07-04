# FAI Cloud image builder

This repository aims to build Debian images for all cloud providers

## Getting started

You will need a checkout of this repository on your disk and a recent fai-server
package (at least 5.7) installed. Install the necessary fai packages without
the recommends (which avoids turning your host into a DHCP server!).
You also need python3-libcloud from Buster or newer.

```
  # git clone https://salsa.debian.org/cloud-team/debian-cloud-images.git
  # sudo apt install --no-install-recommends ca-certificates debsums dosfstools \
    fai-server fai-setup-storage make python3 python3-libcloud python3-marshmallow \
    qemu-utils udev
```

  Call `make help` and follow the instructions

Example 1:

```
   # make stretch-image-nocloud
```

This will create some log output and the following files:

- nocloud-stretch-image.build.json
- nocloud-stretch-image.info
- nocloud-stretch-image.raw
- nocloud-stretch-image.raw.tar

Example 2:

```
    # make buster-image-openstack
```

- openstack-buster-image.build.json
- openstack-buster-image.info
- openstack-buster-image.qcow2
- openstack-buster-image.qcow2.tar
- openstack-buster-image.raw

These images can be used with QEMU-KVM, Virtualbox or any other virtualization
backend that support raw disk or qcow2 images.

You can login as root on the VM console without a password (but not over
SSH), and there are no other users. You can add new users using `adduser` as
usual, and you probably want to add them to the `sudo` group.

After the disk image is created you can try it with kvm, and wait 5s for the
boot sequence to start:

```
    # kvm -m1000 -hda openstack-image-buster.raw
```

## Supported image types

As shown above, various types of images can be built for different use
cases. Each type of image can be built with the following command:

```
    # make <suite>-image-<type>
```

where `<suite>` is one of `stretch`, `buster`, or `sid`. `<type>` can
be any of the following:

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

 * https://fai-project.org/fai-guide/
 * https://noah.meyerhans.us/blog/2017/02/10/using-fai-to-customize-and-build-your-own-cloud-images/

## New cloud vendor how-to

First of all, we are pretty confident that `generic-vm-image` should boot
mostly everywhere. If you really need adjustments for your image, start looking
at the directory structure and only drop in adjustments where really required.
Our CLOUD (base) class should already take care of the most of what is needed
for a cloud image.

## Uploader

Uploaders typically need some variables set with credentials or targets.

### Amazon EC2

 * `$CLOUD_UPLOAD_EC2_DEV_ENABLED`: Set to `1` to upload and create images during development.
 * `$CLOUD_UPLOAD_EC2_DEV_BUCKET`: Amazon S3 bucket to create temporary files during development.
 * `$CLOUD_UPLOAD_EC2_DEV_REGIONS`: Comma separated list of Amazon EC2 regions to create images during development.
 * `$AWS_ACCESS_KEY_ID`
 * `$AWS_SECRET_ACCESS_KEY`

### Google Compute Engine

 * `$CLOUD_UPLOAD_GCE_AUTH`: JSON string of service account credentials.
 * `$CLOUD_UPLOAD_GCE_DEV_ENABLED`: Set to `1` to upload and create images during development.
 * `$CLOUD_UPLOAD_GCE_DEV_PROJECT`: Google Cloud project to create images during development.
 * `$CLOUD_UPLOAD_GCE_DEV_BUCKET`: Google Storage bucket to create temporary files during development.

### Microsoft Azure

 * `$CLOUD_UPLOAD_AZURE_AUTH`: Azure OAuth credentials (`TENANT:APPLICATION:SECRET`).
 * `$CLOUD_UPLOAD_AZURE_DEV_ENABLED`: Set to `1` to upload images during development.
 * `$CLOUD_UPLOAD_AZURE_DEV_STORAGE_GROUP`: Azure Subscription and Resource group (`SUBSCRIPTION:GROUP`).
 * `$CLOUD_UPLOAD_AZURE_DEV_STORAGE`: Azure Storage ID or name.

#### Uploads for daily builds

 * `$CLOUD_UPLOAD_AZURE_AUTH`: Azure OAuth credentials (`TENANT:APPLICATION:SECRET`).
 * `$CLOUD_UPLOAD_AZURE_DAILY_ENABLED`: Set to `1` to upload images.
 * `$CLOUD_UPLOAD_AZURE_DAILY_NOTIFY_EMAIL`: Run publish process and send report to given e-mail address.
 * `$CLOUD_UPLOAD_AZURE_DAILY_PUBLISHER`: Azure Publisher ID.
 * `$CLOUD_UPLOAD_AZURE_DAILY_STORAGE`: Azure Storage ID or name.
