<!-- https://github.com/tbblake/myScripts/tree/main/dhcpPihole -->
# dhcpPihole
Displays your pihole dhcp lease table in an easy to read format.  To install, copy dhcpLeases.php to /var/www/html, 10-accesslog-dhcpLeases.conf to /etc/lighttpd/conf-enabled, then restart lighttpd.

Or you can do this:

```
# Download php script
curl -sLo /var/www/html/dhcpLeases.php https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/dhcpLeases.php

# Download lighttpd config to disable logging for php script
curl -sLo /etc/lighttpd/conf-enabled/10-accesslog-dhcpLeases.conf https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/10-accesslog-dhcpLeases.conf

# restart httpd
systemctl restart lighttpd

```
Then browse to the script http://your.pihole.ip.here/dhcpLeases.php
