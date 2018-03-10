# path to the config space shoud be absolute, see fai.conf(5)
BUILDER_IMG = http://cdimage.debian.org/cdimage/openstack/current-9/debian-9-openstack-amd64.qcow2

help:
	@echo "To run this makefile, run:"
	@echo "   make <DIST>-image-<CLOUD>"
	@echo "  WHERE <DIST> is buster or stretch"
	@echo "    And <CLOUD> is azure, ec2, gce, openstack, vagrant"

_image.raw:
	umask 022; \
	bin/run-fai $(DIST) $(CLOUD) amd64 $(CLOUD)-$(DIST)-image

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
