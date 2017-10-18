# FAI Cloud image builder

This repository aims to build Debian images for all cloud providers

## Getting started

You will need a checkout of this repository on your disk and a recent fai-server package installed.
Install the necessary fai packages without the recommends, avoid turning your host into
a dhcp server!

```
  # git clone https://git.debian.org/git/cloud/fai-cloud-images.git 
  # sudo apt-get install fai-server fai-setup-storage qemu-utils --no-install-recommends
```

  call *make help* and follow the instruction

## New cloud vendor howto

First of all, we are pretty confident, that our generic-vm-image should boot mostly everywhere. If you really need adjustments for your image, here is what our directory structure looks like:

```

```



About the created disk images:

### generic-vm-image-stretch-image.raw:
These images can be used with QEMU-KVM, Virtualbox or any other virtualization backend that support raw disk images.

You can login as root on the VM console without a password (but not over SSH),and there are no other users. You can add new users using adduser as usual, and you probably want to add them to the `sudo` group.

After the disk image is created you can try it with:
kvm -hda generic-vm-image-stretch-image.raw -nographics
and wait 5s for the boot sequence to start
