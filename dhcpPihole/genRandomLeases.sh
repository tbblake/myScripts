#!/bin/bash
# generate 40 random leases, useful for testing
# not meant to be pretty or elegant, just useful
randomMac() {
	printf "%02x:%02x:%02x:%02x:%02x:%02x" $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256))
}

randomIP() {
	printf "192.168.%d.%d" $(($RANDOM%256)) $(($RANDOM%256))
}

randomName() {
	printf "host%02d" $(($RANDOM%41))
}

randomTime() {
	now=$(date +%s)
	echo $(($now+$(($RANDOM%3600))))
}


leaseFile=$(mktemp)
for i in $(seq 1 40)
do
	>&2 echo -n "$i.."
	expiry=$(randomTime)
	mac=$(randomMac)
	ip=$(randomIP)
	name=$(randomName)
	while egrep -q " $mac " $leaseFile;do
		mac=$(randomMac)
	done
	while egrep -q " $ip " $leaseFile;do
		ip=$(randomIP)
	done
	while egrep -q " $name " $leaseFile;do
		name=$(randomName)
	done
	printf "%s %s %s %s *\n" $expiry $mac $ip $name >> $leaseFile
done
>&2 echo
cat $leaseFile
rm -f $leaseFile
