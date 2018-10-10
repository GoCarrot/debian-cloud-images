# path to the config space shoud be absolute, see fai.conf(5)

help:
	@echo "To run this makefile, run:"
	@echo "   make <DIST>-image-<CLOUD>"
	@echo "  WHERE <DIST> is buster, stretch or sid"
	@echo "    And <CLOUD> is azure, ec2, gce, openstack, nocloud"

_image.raw:
	umask 022; \
	sudo bin/build $(DIST) $(CLOUD) amd64 $(CLOUD)-$(DIST)-image dev

sid-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=sid

buster-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=buster

stretch-image-%:
	${MAKE} _image.raw CLOUD=$* DIST=stretch

clean: cleanall

cleanall:
	rm -rf *.raw *vhd *.tar *.qcow2
