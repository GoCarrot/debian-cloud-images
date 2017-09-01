Quick Start building a Debian image using this repo:

* install the necessary fai packages without the recommends, avoid turning your host into
a dhcp server

  sudo apt-get install fai-server fai-setup-storage --no-install-recommends

* calls (p)make help and follow the instruction

About the created disk images:

# generic-vm-image-stretch-image.raw:
These images can be used with QEMU-KVM, Virtualbox or any other virtualization backend that support raw disk images.

You can login as root on the VM console without a password (but not over SSH),and there are no other users. You can add new users using adduser as usual, and you probably want to add them to the `sudo` group.

After the disk image is created you can try it with:
kvm -hda generic-vm-image-stretch-image.raw -nographics
and wait 5s for the boot sequence to start
