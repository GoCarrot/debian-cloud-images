#!/bin/bash -e

# Author: Ben Howard <darkarts@utlemming.org>
# Author: Daniel Watkins <dwatkins@canonical.com>

# ORIGIN: http://bazaar.launchpad.net/~ubuntu-on-ec2/vmbuilder/jenkins_kvm/view/head:/launch_kvm.sh
# PROJECT: https://launchpad.net/vmbuilder

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This is a fork from the original file to support builing Debian
# images via FAI.

my_f=$(readlink -f ${0})
my_d=$(dirname ${my_f})

usage() {
cat << EOF
This program is a KVM wrapper for performing tasks inside a KVM Environment.
Its primary goal is to help developers do dangerous tasks that their IS/IT
deparment won't allow them to do on an existing machine.
    --id <ARG>           The ID you want to use to identify the KVM image
                         this is used to name the image
    --disk-gb <ARG>      Disk size you want to resize the image too
                         Default it to _add_ 30GB
    --smp <ARG>          KVM SMP options, defaults to:
                         ${smp_opt}
    --mem <ARG>          How much RAM do you want to use
    --img-url <ARG>      Location of the image file.
    --raw-size <ARG>     Size of RAW disk in GB.
    --target             FAI target, i.e. buster-image-gce
EOF
exit 1
}

short_opts="h"
long_opts="id:,disk-gb:,mem:,img-url:,smp:,target:,help"
getopt_out=$(getopt --name "${0##*/}" \
    --options "${short_opts}" --long "${long_opts}" -- "$@") &&
    eval set -- "${getopt_out}" ||
    usage

write_user_data() {
    cat <<EOC
Content-Type: multipart/mixed; boundary="===============8645434374073493512=="
MIME-Version: 1.0

--===============8645434374073493512==
MIME-Version: 1.0
Content-Type: text/cloud-config; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="cloud-config"

#cloud-config

output: { all: "| tee -a /dev/ttys0 /var/log/cloud-init-output.log" }
hostname: ${target}
packages:
- eatmydata
- fai-client
- fai-server
- fai-setup-storage
- make
- qemu-utils

power_state:
 delay: "+30m"
 mode: poweroff
 message: Execution finished
 timeout: 30
 condition: True

--===============8645434374073493512==
MIME-Version: 1.0
Content-Type: text/x-shellscript; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename="execution"

#!/bin/bash
trap "shutdown -h now" sysfail SIGINT SIGTERM
cat <<EOM

**************************************************
BUILDING ${target} in KVM environment

**************************************************
EOM

mount /dev/vdc /mnt
mkdir /tmp/build
find /mnt
cp -au /mnt/fai /tmp/build
cd /tmp/build/fai

**************************************************
BUILDING ${target} in KVM environment

**************************************************
eatmydata make ${target}
touch /tmp/build/success

tar -cvf /dev/vdb \
    *raw \
    /var/log/cloud-init*

shutdown -h now
--===============8645434374073493512==--

EOC
}

builder_id=$(< /proc/sys/kernel/random/uuid)
size_gb=15
mem=2048
smp_opt="4"
target=""
img_loc="${BUILDER_CLOUD_IMAGE:-http://cdimage.debian.org/cdimage/openstack/current-9/debian-9-openstack-amd64.qcow2}"
KVM_PID=""

while [ $# -ne 0 ]; do
    cur=${1}; next=${2};
    case "$cur" in
    --id)                       id="$2"; shift;;
    --disk-gb)                  size_gb="$2"; shift;;
    --mem)                      mem="$2"; shift;;
    --img-url)                  img_loc="$2"; shift;;
    --smp)                      smp_opts="$2"; shift;;
    --target)                   target="$2"; shift;;
    -h|--help)                  usage; exit 0;;
    --) shift; break;;
  esac
  shift;
done

work_d="$(mktemp -d /tmp/kvm-builder.XXXX)"
kvm_pidfile="$(mktemp --tmpdir=${work_d})"

error() { echo "$@" 1>&2; }
cleanup() {
        [ -n "${KVM_PID}" ] && kill -9 ${KVM_PID};
        [ -n "${TAIL_PID}" ] && kill -9 ${TAIL_PID};
        rm -rf "${work_d}";
}
fail() { error "$@"; cleanup;  exit 1; }
debug() { error "$(date -R):" "$@"; }
sysfail() {
    cleanup
    fail "failed to build"
}

# Make sure that we kill everything
trap sysfail SIGINT SIGTERM

debug "Creating Cloud-Init configuration..."
write_user_data > "${work_d}/user-data.txt"
echo "instance-id: ${builder_id}" > "${work_d}/meta-data"
echo "local-hostname: builder" >> "${work_d}/meta-data"

debug "Creating Seed for Cloud-Init..."
"${0%/*}/make-seed.sh" \
    "${work_d}/seed.img" \
    "${work_d}/user-data.txt" \
    "${work_d}/meta-data" ||
    fail "Failed to create Configruation ISO"

# Place the image in place
debug "Build image location is ${img_loc}"
img_f=$(basename ${img_loc})
if [[ "${img_loc}" =~ "http" ]]; then
    debug "Fetching cloud image from ${img_loc}"
    wget -O "${work_d}/img-${builder_id}" "${img_loc}" ||
        fail "Unable to fetch pristine image from '${img_loc}'"
else
    cp "${img_loc}" "${work_d}/img-${builder_id}" ||
        fail "Unable to copy '${img_loc}'"
fi

debug "Adding ${size_gb}G to image size"
qemu-img resize "${work_d}/img-${builder_id}" +"${size_gb}G" ||
    fail "Unable to resize image to ${size_gb}G"

raw_disk="$(mktemp --tmpdir=${work_d})"
dd if=/dev/zero of=${raw_disk} bs=1M count=1 seek=15000 &&
   debug "Create new raw disk" ||
   fail "Unable to create raw disk"


debug "________________________________________________"
debug "Launching instance..."
kvm_cmd=(
   ${QEMU_COMMAND:-kvm}
   -name ${builder_id}
   -drive file=${work_d}/img-${builder_id},snapshot=on,if=virtio,bus=0,cache=unsafe,unit=0
   -drive file=${raw_disk},if=virtio,format=raw,bus=0,unit=1
   -drive file=${work_d}/seed.img,if=virtio,media=cdrom,bus=0,cache=unsafe,unit=2
   -net nic,model=virtio
   -net user
   -no-reboot
   -display none
   -daemonize
   -serial file:${work_d}/console.log
   -smp ${smp_opt}
   -m ${mem}
   -pidfile ${kvm_pidfile}
)

debug "KVM command is: ${kvm_cmd[@]}"
"${kvm_cmd[@]}" ||
    fail "Failed to launch KVM image\n${kvm_out}"

read KVM_PID < ${kvm_pidfile}
debug "KVM PID is: ${KVM_PID}"

tail -f "${work_d}/console.log" &
TAIL_PID=$!

# Wait on the pid until the max timeout
count=0
max_count=${MAX_CYCLES:-720}
while $(ps ${KVM_PID} > /dev/null 2>&1)
do
    sleep 10
    count=$((count + 1))
    if [ "${count}" -gt "${max_count}" ]; then
        kill -15 ${KVM_PID}
        debug "Build timed out...killing PID ${KVM_PID}"
    fi
done

debug "________________________________________________"
debug "KVM PID has ended. Work is done"
kill -15 ${TAIL_PID}

unset KVM_PID
unset TAIL_PID

[ -n "${raw_disk}" ] &&
    debug "Extracting raw tarball" &&
    { tar xvvf "${raw_disk}" || /bin/true; }

cp "${work_d}/console.log" .

trap -

# Wait for Cloud-Init to finish any work
debug "Cleaning up..."
cleanup
exit 0
