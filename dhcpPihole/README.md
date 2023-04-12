# dhcpPihole
Copy dhcpLeases.php to /var/www/html and 10-accesslog-dhcpLeases.conf to /etc/lighttpd/conf-enabled.  Then restart lighttpd (systemctl restart lighttpd)

```
curl -Lo /var/www/html/dhcpLeases.php https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/dhcpLeases.php
curl -Lo /etc/lighttpd/conf-enabled/10-accesslog-dhcpLeases.conf https://raw.githubusercontent.com/tbblake/myScripts/main/dhcpPihole/10-accesslog-dhcpLeases.conf
systemctl restart lighttpd
```
