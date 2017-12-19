#!/bin/bash
# This script require the following EC2 APIs:
# DescribeSnapshots
# CreateSnapshot
# RegisterImage

# runtime overridable defaults:
AMI_VIRT_TYPE=hvm
AMI_ARCH=x86_64
AMI_RELEASE=stretch
AMI_VOLTYPE=gp2
AMI_VOLSIZE=8
AMI_ON_TERM=true
AMI_ROOTDEV=xvda
PROFILE=default
DRY_RUN=

command -v 'jq' > /dev/null || {
    echo 'jq is not available. exiting' >&2
    exit 1
}

usage() {
    cat <<EOF
$0 [OPTIONS] VOLUME_ID
OPTIONS:
  -v, --virt-type     EC2 virtualization type (default=hvm)
  -a, --arch          EC2 architecture (default=x86_64)
  -r, --release       Debian release (default=stretch)
  -t, --volume-type   Root volume type (default=gp2)
  -z, --volume-size   Root volume size in GB (default=8)
  -o, --on-terminate  Instance termination behavior (default=delete)
  -d, --root-device   Root device name (default=xvda)
  -p, --profile       Use the given profile for AWS API commands
  -D, --dry-run       Dry run mode, no snapshots or AMIs created
  -F, --final         This AMI build is intended to be public (affects AMI name)
  -h, --help          Print usage
EOF
}

TEMP=$(getopt -o v:a:r:t:z:o:r:d:p:FDh \
              --long virt-type:,arch:,release:,volume-type:,volume-size:,on-terminate:,root-device:,profile:,final,dry-run,help \
              -n "$0" -- "$@")
if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

eval set -- "$TEMP"

while true ; do
    case "$1" in
        -v|--virt-type)
            AMI_VIRT_TYPE="$2" ; shift 2
            ;;
        -a|--arch)
            AMI_ARCH="$2" ; shift 2
            ;;
        -r|--release)
            AMI_RELEASE="$2" ; shift 2
            ;;
        -t|--volume-type)
            AMI_VOLTYPE="$2" ; shift 2
            ;;
        -z|--volume-size)
            AMI_VOLSIZE="$2" ; shift 2
            ;;
        -o|--on-terminate)
            AMI_ON_TERM="$2" ; shift 2
            ;;
        -d|--root-device)
            AMI_ROOTDEV="$2" ; shift 2
            ;;
        -p|--profile)
            PROFILE="$2" ; shift 2
            ;;
        -D|--dry-run)
            DRY_RUN=true ; shift
            ;;
        -F|--final)
            FINAL=true ; shift
            ;;
        -h|--help)
            usage; shift
            exit 0
            ;;
        --)
            shift ; break
            ;;
    esac
done

vol_id=$1; shift

if [ "${vol_id%%-*}" != "vol" ]; then
    echo "First argument must be an EBS volume ID"
    exit 1
fi

if [ "${VIRT_TYPE}" == "paravirtual" ] ; then
    sriov=""
    ena_support="false"
else
    sriov="simple"
    ena_support="true"
fi

awscmd="aws --profile $PROFILE"

snapshot_state() {
    local snapid="$1"
    $awscmd ec2 describe-snapshots \
        --output json \
        --snapshot-id "$snapid" \
        | jq -r '.Snapshots[].State'
}

# Encode the date in the AMI in a form like 2016-11-05-78872. The
# intent is to generate a human-friendly sortable image name while
# also taking reasonable steps to avoid name collisions.
img_stamp=$(date -u +%Y-%m-%d-)$(($(date +%s)%86400))

if [ "${FINAL}" == "true" ]; then
    image_name="debian-${AMI_RELEASE}-${AMI_VIRT_TYPE}-${AMI_ARCH}-${AMI_VOLTYPE}-$img_stamp"
else
    image_name="scratch-${USER}-${AMI_RELEASE}-${AMI_VIRT_TYPE}-${AMI_ARCH}-${AMI_VOLTYPE}-$img_stamp"
fi

cmd="$awscmd --output json ec2 create-snapshot --description \"$image_name\" --volume-id $vol_id"
if [ -n "$DRY_RUN" ]; then
    echo "Dry run: $cmd"
    snap_state="completed"
else
    snap_id=$($cmd | jq -r .SnapshotId)
    echo "Snapshot $snap_id creating. Waiting for it to become available"
    echo EXEC $awscmd ec2 wait snapshot-completed --snapshot-ids "$snap_id"
    $awscmd ec2 wait snapshot-completed --snapshot-ids "$snap_id" || exit 1
    snap_state=$(snapshot_state $snap_id)
fi

if [ "$snap_state" != "completed" ]; then
    echo -n "ERROR: $snap_id is not ready. State is $snap_state"
    exit 1
fi

json_body=$(mktemp) || exit 1
cat > "$json_body" <<EOF 
{
    "DryRun": false,
    "Name": "$image_name",
    "Description": "FAI Debian image", 
    "Architecture": "$AMI_ARCH",
    "RootDeviceName": "$AMI_ROOTDEV",
    "BlockDeviceMappings": [
        {
            "DeviceName": "$AMI_ROOTDEV",
            "Ebs": {
                "SnapshotId": "$snap_id",
                "VolumeSize": 8, 
                "DeleteOnTermination": true, 
                "VolumeType": "$AMI_VOLTYPE"
            }
        }
    ], 
    "VirtualizationType": "$AMI_VIRT_TYPE",
    "SriovNetSupport": "$sriov",
    "EnaSupport": $ena_support
}
EOF

echo "Wrote API request body to $json_body"

cmd="$awscmd ec2 register-image --cli-input-json file://$json_body"
if [ -n "$DRY_RUN" ]; then
    echo "Dry run: $cmd"
    echo "Input data:"
    cat "$json_body"
else
    $cmd
fi

# Local variables:
# mode: shell-script
# tab-width: 4
# indent-tabs-mode: nil
# end:
