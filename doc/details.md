# Details of how to build an image

There are two ways of building an image. You can call `make` which
calls the Python script debian-cloud-images build script. This script
creates some options and the list of FAI classes for calling
fai-diskimage(8). It can also upload the image to the cloud
provider. This is what the Debian cloud team is using inside the
gitlab CI.

It's also possible to call fai-diskimage(8) directly.

Example 1 nocloud:

    # fai-diskimage --hostname debian --class DEBIAN,CLOUD,BUSTER,BACKPORTS,NOCLOUD,AMD64,LINUX_IMAGE_BASE,LAST --size 2G --cspace ... debian-buster-nocloud.raw

Example 2 genericcloud (OpenStack):

    # fai-diskimage --hostname debian --class DEBIAN,CLOUD,BUSTER,BACKPORTS,GENERIC,AMD64,LINUX_IMAGE_CLOUD,LAST --size 2G --cspace ... debian-buster-genericcloud.raw


Example 3 Azure:

    # fai-diskimage --hostname debian --class DEBIAN,CLOUD,BUSTER,BACKPORTS,AZURE,IPV6_DHCP,AMD64,LINUX_IMAGE_CLOUD,LAST --size 30G --cspace ... debian-buster-azure.raw

Example 4 EC2:

    # fai-diskimage --hostname debian --class DEBIAN,CLOUD,SID,EC2,IPV6_DHCP,AMD64,LINUX_IMAGE_BASE,LAST --size 8G --cspace ... debian-sid-ec2.raw


In these examples we replaced the directory to the config space with ...


# Short description of the classes

* `CLOUD`: important class, does a lot
* `DEBIAN`: important class, does a lot
* `NOCLOUD`: remove root pw, set grub timeout to 5
* `DISABLE_IPV6`: uses 70-disable-ipv6.conf for disabling it
* `IPV6_DHCP`: enable IPv6 for Azure, EC2
* `EXTRA`: add useful packages
* `DEVEL`: add packages, NOT USED
* `GENERIC`: add cloud-init for generic images (others already include cloud-init)
* `TYPE_DEV`: development configs, add tty, set grub timeout
* `GCE_SDK`: add SDK package for GCE
* `GCE`: provider specific configs
* `AZURE`: provider specific configs
* `EC2`: provider specific configs
* `LAST`: write manifest and do cleanup
* `LINUX_IMAGE_CLOUD`: use the cloud kernel
* `LINUX_IMAGE_BASE`: use the default Debian kernel
* `LOCALDEBS`: for debugging/internal use, use packages from localdebs directory
* `BACKPORTS`: enable backports repository

These are classes containing architecture specific configs:

* AMD64
* ARM64
* PPC64EL


Release specific classes:

* BULLSEYE
* BUSTER
* SID


Only for internal use:

* BULLSEYE_BUILD
* BUSTER_BUILD
* SID_BUILD
