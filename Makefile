# path to the config space shoud be absolute, see fai.conf(5)
BUILDER_IMG = http://cdimage.debian.org/cdimage/openstack/current-9/debian-9-openstack-amd64.qcow2
FORMAT_NEEDED = raw
UPPER_CLOUD = $(shell echo $(CLOUD) | tr '[:lower:]' '[:upper:]')
UPPER_DIST = $(shell echo $(DIST) | tr '[:lower:]' '[:upper:]')
PWD := $(shell readlink -f .)
SPACE = 8

ifeq ($(CLOUD),openstack)
  SPACE = 2
else ifeq ($(CLOUD),azure)
  FORMAT_NEEDED = vhd
else ifeq ($(CLOUD),gce)
  SPACE = 10
endif

help:
	@echo "To run this makefile, run:"
	@echo "   make <DIST>-image-<CLOUD>"
	@echo "  WHERE <DIST> is buster or stretch"
	@echo "    And <CLOUD> is azure, ec2, gce, openstack, vagrant"

_image.raw:
	sudo fai-diskimage -v \
		--hostname debian-$(DIST) \
		--size $(SPACE)G \
		--class DEBIAN,$(UPPER_DIST),AMD64,GRUB_PC,CLOUD,$(UPPER_CLOUD) \
		--cspace $(PWD)/config_space $(CLOUD)-$(DIST)-image.raw
	if [ "$(FORMAT_NEEDED)" = "vhd" ]; then \
		qemu-img convert -f raw -o subformat=fixed,force_size -O vpc \
		$(CLOUD)-$(DIST)-image.raw $(CLOUD)-$(DIST)-image.vhd; fi
buster-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=buster

stretch-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=stretch

kvm-%:
	bin/launch_kvm.sh --id $*-$(shell date +%s) \
		--target $* \
		--img-url $(BUILDER_IMG)

cleanall:
	rm -rf *.raw *vhd
