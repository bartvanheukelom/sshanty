#!/usr/bin/env python3
import itertools
import os
import subprocess
from collections import defaultdict
from pprint import PrettyPrinter
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
        self.tunnels = [int(x.strip()) for x in props.get("$tunnels", "").split(",") if x.strip()]

    def __repr__(self):
        return self.fullname

    def sortkey(self):
        return self.group.ljust(30) + self.leafname

def open_tunnel(host, port):
    open_terminal(['ssh', host, '-N', '-v', '-L', f"127.0.0.1:{port}:localhost:{port}"], profile="Blue")

def open_shell(host, profile, root=False):
    open_terminal(['ssh', host] + (['-t', 'sudo -i'] if root else []), profile)

def open_terminal(cmd, titlex=None, profile=None):
    title = titlex if titlex else " ".join(cmd)
    gcmd = ['gnome-terminal'] + \
           (['--title', title] if title else []) + \
           (['--profile', profile] if profile else []) + \
            ['--'] + cmd
    print(gcmd)
    proc = subprocess.Popen(gcmd,
                     stdout=open('/dev/null', 'w'),
                     stderr=open('/dev/null', 'w'),
                     preexec_fn=os.setpgrp)
    print(proc)


def gmenu(items):
    menu = Gtk.Menu()
    for i in items:
        menu.append(i)
    return menu


def gmenu_item(title: str, activate=None, sub=None):
    item = Gtk.MenuItem()
    item.set_label(title)

    if activate:
        item.connect("activate", lambda x: activate())

    if sub:
        item.set_submenu(sub)
    return item


if __name__ == '__main__':

    with open(expanduser("~/.ssh/config")) as cf:
        conf = SshConfig(cf.readlines())

    hostlist: List[Host] = []

    hostprops = defaultdict(dict)

    for h in conf.hosts():
        props = conf.host(h)
        if "*" in h:
            if "$expand" in props:
                for e in props["$expand"].split(","):
                    hostprops[h.replace("*", e.strip())].update(props)
            else:
                print(f"Skip {h}")
        else:
            hostprops[h].update(props)

    print(PrettyPrinter().pprint(hostprops))

    hostlist = [Host(h, p) for h, p in hostprops.items()]

    ind = AppIndicator3.Indicator.new(
        "SSHanty",
        "utilities-terminal",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    hostlist.sort(key=Host.sortkey)
    hostsgrouped = itertools.groupby(hostlist, lambda h: h.group)

    menu = gmenu(
            [gmenu_item(
                prefix, sub=
                gmenu(
                    [gmenu_item(
                        gh.leafname, sub=
                        gmenu(
                            [
                                gmenu_item("Shell", activate=lambda h=gh: open_shell(h.dnsname, h.profile)),
                                gmenu_item("Root Shell", activate=lambda h=gh: open_shell(h.dnsname, h.profile, root=True))
                            ] + [gmenu_item(f"Tunnel {p}", activate=lambda h=gh: open_tunnel(h.dnsname, p)) for p in gh.tunnels]
                        )) for gh in grouphosts])
            ) for prefix, grouphosts in hostsgrouped])

    menu.show_all()
    ind.set_menu(menu)

    # Use GLib because Gtk.main() doesn't respond to SIGINT
    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("Bye")
