# dhcpPihole
Copy dhcpLeases.php to /var/www/html and 10-accesslog-dhcpLeases.conf to /etc/lighttpd/conf-enabled.  Then restart lighttpd (systemctl restart lighttpd)

```
# Download php script
curl -sLo /var/www/html/dhcpLeases.php https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/dhcpLeases.php

# Download lighttpd config to disable logging for php script
curl -sLo /etc/lighttpd/conf-enabled/10-accesslog-dhcpLeases.conf https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/10-accesslog-dhcpLeases.conf

# restart httpd
systemctl restart lighttpd

```
