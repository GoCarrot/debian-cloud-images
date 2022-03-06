#!/bin/sh
PREREQ=""
prereqs()
{
    echo "$PREREQ"
}

case $1 in
    prereqs)
	prereqs
	exit 0
	;;
esac

. /scripts/functions

echo 0 > /proc/sys/net/ipv6/conf/all/accept_dad
echo 0 > /proc/sys/net/ipv6/conf/default/accept_dad

log_success_msg "Disabled IPv6 DAD"
