#!/bin/bash

command -v 'jq' > /dev/null || {
    echo 'jq is not available. exiting' >&2
    exit 1
}

vol_id=$1; shift

if [ "${vol_id%%-*}" != "vol" ]; then
    echo "First argument must be an EBS volume ID"
    exit 1
fi

snapshot_state() {
    local snapid="$1"
    aws ec2 describe-snapshots \
        --output json \
        --snapshot-id "$snapid" \
        | jq -r '.Snapshots[].State'
}

snap_id=$(aws --output json ec2 create-snapshot --volume-id "$vol_id" | jq -r .SnapshotId)
echo "Snapshot $snap_id creating. Waiting for it to become available"
deadline=$(date -d "now+1 hour" +%s)
snap_start=$(date +%s)
while [ $(date +%s) -lt $deadline ]; do
    snap_state=$(snapshot_state $snap_id)
    if [ "$snap_state" == "completed" ]; then
        snap_done=$(date +%s)
        echo "Snapshot ready after $(($snap_done-$snap_start))s"
        echo
        break
    else
        echo -n .
        sleep 30
    fi
done

if [ "$snap_state" != "completed" ]; then
    echo -n "ERROR: After ${deadline}s, $snap_id is not ready. State is $snap_state"
    exit 1
fi

# Encode the date in the AMI in a form like 2016-11-05-78872. The
# intent is to generate a human-friendly sortable image name while
# also taking reasonable steps to avoid name collisions.
img_stamp=$(date -u +%Y-%m-%d-)$(($(date +%s)%86400))

json_body=$(mktemp) || exit 1
cat > "$json_body" <<EOF 
{
    "DryRun": false, 
    "Name": "debian-jessie-$img_stamp",
    "Description": "FAI Debian image", 
    "Architecture": "x86_64", 
    "RootDeviceName": "xvda", 
    "BlockDeviceMappings": [
        {
            "DeviceName": "xvda", 
            "Ebs": {
                "SnapshotId": "$snap_id",
                "VolumeSize": 8, 
                "DeleteOnTermination": true, 
                "VolumeType": "gp2"
            }
        }
    ], 
    "VirtualizationType": "hvm"
}
EOF

echo "Wrote API request body to $json_body"

aws ec2 register-image --cli-input-json "file://$json_body"

# Local variables:
# mode: shell-script
# tab-width: 4
# indent-tabs-mode: nil
# end:
