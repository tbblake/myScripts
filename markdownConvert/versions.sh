#!/bin/bash
# what version of marked.min.js are we running
D=$(dirname $0)
cd $D
(echo File Date Checksum Version
echo '---- ---- -------- -------'
for i in $(ls -t marked.min.js*)
do
	v=$(sed -n 's/.*marked \(v[[:digit:]]\.[[:digit:]]\.[[:digit:]]\) .*/\1/gp' $i)
	cksum=$(md5sum $i | awk '{print $1}')
	mtime=$(stat -c "%y" $i | sed 's/ /X/g')
	echo $i $mtime $cksum $v
done ) | column -t | sed 's/X/ /g'
