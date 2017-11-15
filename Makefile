# path to the config space shoud be absolute, see fai.conf(5)
BUILDER_IMG = http://cdimage.debian.org/cdimage/openstack/current-9/debian-9-openstack-amd64.qcow2
FORMAT_NEEDED = raw
UPPER_CLOUD = $(shell echo $(CLOUD) | tr '[:lower:]' '[:upper:]')
UPPER_DIST = $(shell echo $(DIST) | tr '[:lower:]' '[:upper:]')
PWD := $(shell readlink -f .)
SPACE = 8

VALID_CLOUDS = (azure|ec2|gce|openstack|vm|vagrant)
VALID_DISTS = (stretch|buster)

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
	@echo $(CLOUD) | egrep -q "$(VALID_CLOUDS)" || { \
		 echo "$(CLOUD) is an invalid. Valid clouds are $(VALID_CLOUDS)"; exit 1; }
	@echo $(DIST) | egrep -q "$(VALID_DISTS)" || { \
		echo "$(DIST) is an invalid. Valid clouds are $(VALID_DISTS)"; exit 1; }
	umask 022; \
	sudo fai-diskimage -v \
		--hostname debian-$(DIST) \
		--size $(SPACE)G \
		--class DEBIAN,$(UPPER_DIST),AMD64,GRUB_PC,CLOUD,$(UPPER_CLOUD) \
		--cspace $(PWD)/config_space $(CLOUD)-$(DIST)-image.raw
ifeq ($(FORMAT_NEEDED), vhd)
	qemu-img convert -f raw -o subformat=fixed,force_size -O vpc \
		$(CLOUD)-$(DIST)-image.raw $(CLOUD)-$(DIST)-image.vhd
endif

buster-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=buster

stretch-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=stretch


kvm-%:
	bin/launch_kvm.sh --id $*-$(shell date +%s) \
		--target $* \
		--img-url $(BUILDER_IMG)

clean: cleanall

cleanall:
	rm -rf *.raw *vhd
