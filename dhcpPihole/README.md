<!-- https://github.com/tbblake/myScripts/tree/main/dhcpPihole -->
# dhcpPihole
This displays your pihole dhcp lease table in an easy to read format.  A lighttpd configuration is included to restrict what gets logged, to reduce SD card wear & tear.

Additional options can be passed to the php script in the URL for text & json output, date output, and sorting options:

* sortOrder
  * 0 - ascending
  * 1 - descending
* sortField
  * 1 - mac address
  * 3 - name
  * 4 - expiration
  * 5 - ip
* htmlTable - output html table
* textTable - output text table
* jsonTable - output json table
* noDate - supresses date in output


To install, copy dhcpLeases.php to /var/www/html, 10-accesslog-dhcpLeases.conf to /etc/lighttpd/conf-enabled, then restart lighttpd.

Or this:

```
git clone https://github.com/tbblake/myScripts.git
cp myScripts/dhcpPihole/dhcpLeases.php /var/www/html/dhcpLeases.php
cp myScripts/dhcpPihole/10-accesslog-dhcpLeases.conf /var/www/html/dhcpLeases.php 
systemctl restart lighttpd
```

Or this:

```
curl -sLo /var/www/html/dhcpLeases.php https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/dhcpLeases.php
curl -sLo /etc/lighttpd/conf-enabled/10-accesslog-dhcpLeases.conf https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/10-accesslog-dhcpLeases.conf
systemctl restart lighttpd
```

Then browse to the script http://your.pihole.ip.here/dhcpLeases.php

![example](example.png)