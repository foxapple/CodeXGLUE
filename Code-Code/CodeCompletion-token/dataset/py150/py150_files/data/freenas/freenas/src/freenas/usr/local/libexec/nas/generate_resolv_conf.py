#!/usr/local/bin/python

import os
import errno
import sys

sys.path.extend([
    '/usr/local/www',
    '/usr/local/www/freenasUI'
])

os.environ["DJANGO_SETTINGS_MODULE"] = "freenasUI.settings"

from django.db.models.loading import cache
cache.get_apps()

RESOLV_CONF_PATH = "/etc/resolv.conf"

from freenasUI.common.system import domaincontroller_enabled
from freenasUI.network.models import (
    GlobalConfiguration,
    Interfaces
)
from freenasUI.services.models import (
    CIFS,
    DomainController
)


def main():

    domain = None
    nameservers = []

    if domaincontroller_enabled():
        try:
            cifs = CIFS.objects.all()[0]
            dc = DomainController.objects.all()[0]

            domain = dc.dc_realm
            if cifs.cifs_srv_bindip:
                for ip in cifs.cifs_srv_bindip:
                    nameservers.append(ip)
            else:
                nameservers.append("127.0.0.1")

        except Exception as e:
            print >> sys.stderr, "ix-resolv: ERROR: %s" % e
            sys.exit(1)

    else:
        try:
            gc = GlobalConfiguration.objects.all()[0]
            if gc.gc_domain:
                domain = gc.gc_domain
            if gc.gc_nameserver1:
                nameservers.append(gc.gc_nameserver1)
            if gc.gc_nameserver2:
                nameservers.append(gc.gc_nameserver2)
            if gc.gc_nameserver3:
                nameservers.append(gc.gc_nameserver3)

        except Exception as e:
            print >> sys.stderr, "ix-resolv: ERROR: %s" % e
            sys.exit(1)

    if (
        not nameservers and
        (Interfaces.objects.count() == 0 or Interfaces.objects.filter(int_dhcp=True))
       ):
        # since we have set a dhclient hook that disables dhclient from writing to /etc/resolv.conf
        # we should remove it now
        try:
            os.remove("/etc/dhclient-enter-hooks")
        except OSError as e:
            # if this error is not due to the file not existing then we have a problem
            if e.errno != errno.ENOENT:
                raise
            # else we never wrote that file so....moving on
            pass
        sys.exit(0)

    try:
        fd = os.open(RESOLV_CONF_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0x0644)
        if domain:
            os.write(fd, "search %s\n" % domain)
        for ns in nameservers:
            os.write(fd, "nameserver %s\n" % ns)
        os.close(fd)
        with open("/etc/dhclient-enter-hooks", 'w') as f:
            f.write(
                """
                add_new_resolv_conf() {
                    # We don't want /etc/resolv.conf changed
                    # So this is an empty function
                    return 0
                }
                """
            )
        os.chmod("/etc/dhclient-enter-hooks", 0x0744)

    except Exception as e:
        print >> sys.stderr, "can't create %s: %s" % (RESOLV_CONF_PATH, e)
        sys.exit(1)

if __name__ == '__main__':
    main()
