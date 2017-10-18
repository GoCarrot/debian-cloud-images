#!/bin/bash
#
# Author: Scott Moser <smoser@ubuntu.com>
# Author: Ben Howard <darkarts@utlemming.org>

# ORIGIN: http://bazaar.launchpad.net/~ubuntu-on-ec2/vmbuilder/jenkins_kvm/view/head:/make-seed.sh
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

VERBOSITY=0
TEMP_D=""
DEF_DISK_FORMAT="raw"

my_f=$(readlink -f ${0})
my_d=$(dirname ${my_f})
pdir=$(dirname ${my_d})

error() { echo "$@" 1>&2; }
errorp() { printf "$@" 1>&2; }
fail() { [ $# -eq 0 ] || error "$@"; exit 1; }
failp() { [ $# -eq 0 ] || errorp "$@"; exit 1; }

Usage() {
    cat <<EOF
Usage: ${0##*/} [ options ] output user-data [meta-data]

   Create a disk for cloud-init to utilize nocloud

   options:
     -h | --help            show usage
     -d | --disk-format D   disk format to output. default: raw
     -i | --interfaces  F   write network interfaces file into metadata
     -m | --dsmode      M   add 'dsmode' ('local' or 'net') to the metadata
                            default in cloud-init is 'net', meaning network is
                            required.

   Example:
    * cat my-user-data
      #cloud-config
      password: passw0rd
      chpasswd: { expire: False }
      ssh_pwauth: True
    * echo "instance-id: \$(uuidgen || echo i-abcdefg)" > my-meta-data
    * ${0##*/} my-seed.img my-user-data my-meta-data
EOF
}

bad_Usage() { Usage 1>&2; [ $# -eq 0 ] || error "$@"; exit 1; }
cleanup() {
    [ -z "${TEMP_D}" -o ! -d "${TEMP_D}" ] || rm -Rf "${TEMP_D}"
}

debug() {
    local level=${1}; shift;
    [ "${level}" -gt "${VERBOSITY}" ] && return
    error "${@}"
}

short_opts="hi:d:m:o:v"
long_opts="disk-format:,dsmode:,help,interfaces:,output:,verbose"
getopt_out=$(getopt --name "${0##*/}" \
    --options "${short_opts}" --long "${long_opts}" -- "$@") &&
    eval set -- "${getopt_out}" ||
    bad_Usage

## <<insert default variables here>>
output=""
userdata=""
metadata=""
diskformat=$DEF_DISK_FORMAT
interfaces=_unset
dsmode=""


while [ $# -ne 0 ]; do
    cur=${1}; next=${2};
    case "$cur" in
        -h|--help) Usage ; exit 0;;
        -v|--verbose)     VERBOSITY=$((${VERBOSITY}+1));;
        -d|--disk-format) diskformat=$next; shift;;
        -m|--dsmode)      dsmode=$next; shift;;
        -i|--interfaces)  interfaces=$next; shift;;
        --) shift; break;;
    esac
    shift;
done

## check arguments here
## how many args do you expect?
[ $# -ge 1 ] || bad_Usage "must provide output, userdata"
[ $# -le 3 ] || bad_Usage "confused by additional args"

output=$1
userdata=$2
metadata=$3

[ -n "$metadata" -a "${interfaces}" != "_unset" ] &&
    fail "metadata and --interfaces are incompatible"
[ -n "$metadata" -a -n "$dsmode" ] &&
    fail "metadata and dsmode are incompatible"
[ "$interfaces" = "_unset" -o -r "$interfaces" ] ||
    fail "$interfaces: not a readable file"

TEMP_D=$(mktemp -d "${TMPDIR:-/tmp}/${0##*/}.XXXXXX") ||
    fail "failed to make tempdir"
trap cleanup EXIT

if [ -n "$metadata" ]; then
    cp "$metadata" "$TEMP_D/meta-data" || fail "$metadata: failed to copy"
else
    {
    echo "instance-id: iid-local01"
    [ -n "$dsmode" ] && echo "dsmode: $dsmode"
    [ -n "$interfaces" ] && echo "interfaces: |" &&
        sed 's,^,  ,' "$interfaces"
    } > "$TEMP_D/meta-data"
fi

if [ "$userdata" = "-" ]; then
    cat > "$TEMP_D/user-data" || fail "failed to read from stdin"
else
    cp "$userdata" "$TEMP_D/user-data" || fail "$userdata: failed to copy"
fi

mkdir -p $TEMP_D/fai/fai
find ${pdir} -maxdepth 1 -mindepth 1 \
	| egrep -v "(*raw|*log|*qcow2|*git|var)" \
	| xargs -I IN -n1 cp -a IN $TEMP_D/fai/fai/

img="$TEMP_D/seed.img"
truncate --size 100K "$img" || fail "failed truncate image"

genisoimage \
	-output "$img" \
	-volid cidata \
	-joliet \
	-rock \
	-m '**/*.qcow2' -m '.git' \
	"$TEMP_D/meta-data" "$TEMP_D/user-data" "$TEMP_D/fai" \
		> "$TEMP_D/err" 2>&1 ||
	   { cat "$TEMP_D/err" 1>&2; fail "failed to genisoimage"; }

[ "$output" = "-" ] && output="$TEMP_D/final"
qemu-img convert -f raw -O "$diskformat" "$img" "$output" ||
    fail "failed to convert to disk format $diskformat"

[ "$output" != "$TEMP_D/final" ] || { cat "$output" && output="-"; } ||
    fail "failed to write to -"

error "wrote ${output} with filesystem=$filesystem and diskformat=$diskformat"
# vi: ts=4 noexpandtab
