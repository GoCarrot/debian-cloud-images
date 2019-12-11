# path to the config space shoud be absolute, see fai.conf(5)

DESTDIR = .

help:
	@echo "To run this makefile, run:"
	@echo "   make image-<DIST>-<CLOUD>"
	@echo "  WHERE <DIST> is bullseye, buster, stretch or sid"
	@echo "    And <CLOUD> is azure, ec2, gce, generic, genericcloud, nocloud"
	@echo "Set DESTDIR= to write images to given directory."

_image.raw:
	umask 022; \
	sudo ./bin/debian-cloud-images build \
	  $(DIST) $(CLOUD) amd64 \
	  --build-id manual \
	  --version 0 \
	  --localdebs \
	  --output $(DESTDIR) \
	  --override-name image-$(CLOUD)-$(DIST)-amd64

image-sid-%:
	${MAKE} _image.raw CLOUD=$* DIST=sid

image-bullseye-%:
	${MAKE} _image.raw CLOUD=$* DIST=bullseye

image-buster-%:
	${MAKE} _image.raw CLOUD=$* DIST=buster

image-stretch-%:
	${MAKE} _image.raw CLOUD=$* DIST=stretch

clean:
	rm -rf image-*.*
