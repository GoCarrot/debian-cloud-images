# path to the config space shoud be absolute, see fai.conf(5)
PWD != pwd

generic-vm-image-stretch-image.raw:
	sudo fai-diskimage --hostname debian-stretch --size 8G \
	--class DEBIAN,STRETCH,AMD64,GRUB_PC,DHCPC,VM_IMAGE \
	--cspace $(PWD)/config_space $@ || rm $@

# based on https://noah.meyerhans.us/blog/2017/02/10/using-fai-to-customize-and-build-your-own-cloud-images/
ec2-stretch-image.raw:
	sudo fai-diskimage --hostname debian-stretch --size 8G \
	--class DEBIAN,STRETCH,AMD64,GRUB_PC,CLOUD,EC2 \
	--cspace $(PWD)/config_space $@ || rm $@

gce-stretch-image.raw:
	sudo fai-diskimage --hostname debian-stretch --size 8G \
	--class DEBIAN,STRETCH,AMD64,GRUB_PC,CLOUD,GCE \
	--cspace $(PWD)/config_space $@ || rm $@

openstack-stretch-image.raw:
	sudo fai-diskimage --hostname debian-stretch --size 8G \
	--class DEBIAN,STRETCH,AMD64,GRUB_PC,CLOUD,OPENSTACK \
	--cspace $(PWD)/config_space $@ || rm $@

vagrant-stretch-image.raw:
	sudo fai-diskimage --hostname debian-stretch --size 8G \
	--class DEBIAN,STRETCH,AMD64,GRUB_PC,DHCPC,VM_IMAGE,VAGRANT \
	--cspace $(PWD)/config_space $@ || rm $@

help:
	@echo "available targets:"
	@echo "make generic-vm-image-stretch-image.raw"
	@echo "make ec2-stretch-image.raw"
	@echo "make gce-stretch-image.raw"

cleanall:
	rm *.raw
