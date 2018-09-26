#!/usr/bin/env python3
import itertools
import os
import subprocess
from typing import List
from os.path import expanduser

import gi

from sshconf import SshConfig

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk
from gi.repository import AppIndicator3
from gi.repository import GLib


class Host:
    def __init__(self, dnsname: str):
        self.dnsname = dnsname
        self.name = list(reversed(dnsname.split(".")))
        self.fullname = ".".join(self.name)

    def __repr__(self):
        return self.fullname


def open_terminal(host):
    subprocess.Popen(['gnome-terminal', '--title', f"ssh {host}", '--', 'ssh', host],
                     stdout=open('/dev/null', 'w'),
                     stderr=open('/dev/null', 'w'),
                     preexec_fn=os.setpgrp)


if __name__ == '__main__':

    with open(expanduser("~/.ssh/config")) as cf:
        conf = SshConfig(cf.readlines())

    hostlist: List[Host] = []

    for h in conf.hosts():
        props = conf.host(h)
        if "*" in h:
            if "$expand" in props:
                for e in props["$expand"].split(","):
                    hostlist += [Host(h.replace("*", e.strip()))]
            else:
                print(f"Skip {h}")
        else:
            hostlist += [Host(h)]

    ind = AppIndicator3.Indicator.new(
        "SSHanty",
        "utilities-terminal",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()


    hostsgrouped = itertools.groupby(hostlist, lambda x: x.name[0] if len(x.name) >= 2 else x.name)
    for prefix, grouphosts in hostsgrouped:
        item = Gtk.MenuItem()
        item.set_label(prefix)
        menu.append(item)

        submenu = Gtk.Menu()
        item.set_submenu(submenu)
        for gh in grouphosts:
            ghh: Host = gh
            sitem = Gtk.MenuItem()
            sitem.set_label(ghh.fullname)
            sitem.connect("activate", lambda x, h=ghh: open_terminal(h.dnsname))
            submenu.append(sitem)

    menu.show_all()
    ind.set_menu(menu)

    # Use GLib because Gtk.main() doesn't respond to SIGINT
    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("Bye")
