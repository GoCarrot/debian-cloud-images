# path to the config space shoud be absolute, see fai.conf(5)
UPPER_CLOUD = $(shell echo $(CLOUD) | tr '[:lower:]' '[:upper:]')
UPPER_DIST = $(shell echo $(DIST) | tr '[:lower:]' '[:upper:]')
PWD := $(shell readlink -f ${PWD})
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
	@echo "   make <DIST>-image_<CLOUD>"
	@echo "  WHERE <DIST> is buster or stretch"
	@echo "    And <CLOUD> is azure, ec2, gce, openstack, vagrant"

_image.raw:
	sudo fai-diskimage -v \
		--hostname debian-$(DIST) \
		--size $(SPACE)G \
		--class DEBIAN,$(UPPER_DIST),AMD64,GRUB_PC,CLOUD,$(UPPER_CLOUD) \
		--cspace $(PWD)/config_space $(CLOUD)-$(DIST)-image.raw
	[ $(FORMAT_NEEDED) = "vhd" ] && \
		qemu-img convert -f raw -o subformat=fixed,force_size -O vpc \
		$(CLOUD)-$(DIST)-image.raw $(CLOUD)-$(DIST)-image.vhd
buster-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=buster

stretch-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=stretch


cleanall:
	rm -rf *.raw *vhd
