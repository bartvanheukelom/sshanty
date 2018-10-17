#!/usr/bin/env python3
import getpass
import itertools
import os
import subprocess
from threading import Timer

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib

import sshanty


def open_tunnel(host, port):
    open_terminal(['ssh', host, '-N', '-v', '-L', f"127.0.0.1:{port}:localhost:{port}"], profile="Blue")


def open_shell(host, profile, root=False, screen=False):
    user = getpass.getuser().replace(' ', '_')
    sessname = f"sshanty-{user}"
    cmd = ["ssh", host]
    if screen:
        if root:
            sessname += "-as-root"
        cmd += ['-t', f'sudo screen -DR {sessname}']
    else:
        if root:
            cmd += ['-t', 'sudo -i']
    open_terminal(cmd, profile)


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


def start():

    ind = AppIndicator3.Indicator.new(
        "SSHanty",
        "utilities-terminal",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    def setup():

        hostlist = sshanty.readconfig()
        hostsgrouped = itertools.groupby(hostlist, lambda h: h.group)

        menu = gmenu(
                [gmenu_item(
                    prefix, sub=
                    gmenu(
                        [gmenu_item(
                            gh.leafname, sub=
                            gmenu(
                                [
                                    gmenu_item("Shell",
                                               activate=lambda h=gh: open_shell(h.dnsname, h.profile)),
                                    gmenu_item("Screen",
                                               activate=lambda h=gh: open_shell(h.dnsname, h.profile, screen=True)),
                                    gmenu_item("Root Shell",
                                               activate=lambda h=gh: open_shell(h.dnsname, h.profile, root=True)),
                                    gmenu_item("Root Screen",
                                               activate=lambda h=gh: open_shell(h.dnsname, h.profile, root=True, screen=True))
                                ] + [gmenu_item(f"Tunnel {p}",
                                                activate=lambda gh=gh, p=p: open_tunnel(gh.dnsname, p)) for p in gh.tunnels]
                            )) for gh in grouphosts])
                ) for prefix, grouphosts in hostsgrouped] + [
                    Gtk.SeparatorMenuItem(),
                    gmenu_item("Reload", activate=lambda: Timer(0.25, setup).start())
                ])

        menu.show_all()
        ind.set_menu(menu)

    setup()
    # def change():
    #     print("Config changed")
    # file = Gio.File.new_for_path(configfile)
    # file.monitor_file(Gio.FileMonitorFlags.NONE, None).connect("changed", change)

    # Use GLib because Gtk.main() doesn't respond to SIGINT
    try:
        GLib.MainLoop().run()
    except KeyboardInterrupt:
        print("Bye")
