# FAI Cloud image builder

This repository aims to build Debian images for all cloud providers

## Getting started

You will need a checkout of this repository on your disk and a recent fai-server package (at least 5.3.6) installed.
Install the necessary fai packages without the recommends, avoid turning your host into
a dhcp server!

```
  # git clone https://git.debian.org/git/cloud/fai-cloud-images.git 
  # sudo apt-get install fai-server fai-setup-storage qemu-utils --no-install-recommends
```

  call *make help* and follow the instruction

## New cloud vendor howto

First of all, we are pretty confident, that our generic-vm-image should boot mostly everywhere. If you really need adjustments for your image, start looking at the directory structure and only drop in adjustments where really required. Our CLOUD (base) class should alreday take care of the most of what is needed for a cloud image. 


    .
    \-- config_space
        +-- class
        +-- debconf
        +-- disk_config
        +-- files
                +-- etc
                        +-- apt
                                +-- sources.list
                                \-- sources.list.d
                                    +-- backports.list
                                    \-- gce.list
                        +-- cloud
                                \-- cloud.cfg.d
                                    +-- 01_debian_cloud.cfg
                                    \-- 99-disable-network-config.cfg
                        +-- default
                                \-- grub.d
                                    +-- 10_cloud_disable_net.ifnames.cfg
                                    \-- 20_add_extra_serial_console.cfg
                        \-- udev
                            \-- rules.d
                                \-- 98-azure-disable-timesync.rules
                \-- usr
                    \-- local
                        \-- sbin
                            \-- inet6-ifup-helper
        +-- package_config
        +-- scripts
                +-- AZURE
                +-- BACKPORTS
                +-- CLOUD
                +-- DEBIAN
                +-- EC2
                +-- GCE
                +-- GRUB_PC
                +-- OPENSTACK
                +-- VAGRANT
                \-- VM_IMAGE
        \-- tests


## Documentation

 * https://fai-project.org/fai-guide/
 * https://noah.meyerhans.us/blog/2017/02/10/using-fai-to-customize-and-build-your-own-cloud-images/


About the created disk images:

### generic-vm-image-stretch-image.raw:
These images can be used with QEMU-KVM, Virtualbox or any other virtualization backend that support raw disk images.

You can login as root on the VM console without a password (but not over SSH),and there are no other users. You can add new users using adduser as usual, and you probably want to add them to the `sudo` group.

After the disk image is created you can try it with:
kvm -hda generic-vm-image-stretch-image.raw -nographics
and wait 5s for the boot sequence to start
