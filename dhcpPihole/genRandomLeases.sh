#!/bin/bash
# generate 40 random leases, useful for testing
# not meant to be pretty or elegant, just useful
randomMac() {
	printf "%02x:%02x:%02x:%02x:%02x:%02x" $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256)) $(($RANDOM%256))
}

randomIP() {
	printf "192.168.%d.%d" $((1+$RANDOM%254)) $((1+($RANDOM%254)))
}

randomName() {
	printf "host%03d" $(($RANDOM%256))
}

randomTime() {
	now=$(date +%s)
	echo $(($now+$(($RANDOM%3600))))
}


leaseFile=$(mktemp)
for i in $(seq 1 40)
do
	>&2 printf "\033[KGenerating Lease #%02d\r" $i
	expiry=$(randomTime)
	mac=$(randomMac)
	ip=$(randomIP)
	name=$(randomName)
	while egrep -q " $mac " $leaseFile;do # ensure unique mac addresses
		mac=$(randomMac)
	done
	while egrep -q " $ip " $leaseFile;do # ensure unique ip addresses
		ip=$(randomIP)
	done
	while egrep -q " $name " $leaseFile;do # ensure unique hostnames
		name=$(randomName)
	done
	printf "%s %s %s %s *\n" $expiry $mac $ip $name >> $leaseFile
done
>&2 printf "\n"
cat $leaseFile
rm -f $leaseFile
