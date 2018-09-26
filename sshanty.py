#!/usr/bin/env python3
import itertools
import os
import subprocess
from typing import List, Dict
from os.path import expanduser
import re

import gi

from sshconf import SshConfig

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk
from gi.repository import AppIndicator3
from gi.repository import GLib


class Host:
    def __init__(self, dnsname: str, props: Dict[str, str]):
        print(dnsname, props)
        self.dnsname = dnsname
        self.name = list(reversed(dnsname.replace("-dev", ".dev").split(".")))
        self.group = ".".join(self.name[:-1])
        self.leafname = self.name[-1]
        self.fullname = ".".join(self.name)
        self.profile = props.get("$profile")

    def __repr__(self):
        return self.fullname

    def sortkey(self):
        return self.group.ljust(30) + self.leafname


def open_terminal(host, profile):
    cmd = ['gnome-terminal', '--title', f"ssh {host}"] + \
         (['--profile', profile] if profile else []) + \
         ['--', 'ssh', host]
    print(cmd)
    subprocess.Popen(cmd,
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
                    hostlist += [Host(h.replace("*", e.strip()), props)]
            else:
                print(f"Skip {h}")
        else:
            hostlist += [Host(h, props)]

    ind = AppIndicator3.Indicator.new(
        "SSHanty",
        "utilities-terminal",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()

    hostlist.sort(key=Host.sortkey)
    for h in hostlist:
        print(h.sortkey())

    hostsgrouped = itertools.groupby(hostlist, lambda h: h.group)
    for prefix, grouphosts in hostsgrouped:
        item = Gtk.MenuItem()
        item.set_label(prefix)
        menu.append(item)

        submenu = Gtk.Menu()
        item.set_submenu(submenu)
        for gh in grouphosts:
            ghh: Host = gh
            sitem = Gtk.MenuItem()
            sitem.set_label(ghh.name[-1])
            sitem.connect("activate", lambda x, h=ghh: open_terminal(h.dnsname, h.profile))
            submenu.append(sitem)

    menu.show_all()
    ind.set_menu(menu)

    # Use GLib because Gtk.main() doesn't respond to SIGINT
    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("Bye")
