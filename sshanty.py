#!/usr/bin/env python3
import sys
from collections import defaultdict
from os.path import expanduser
from pprint import PrettyPrinter
from typing import Dict

import indicator
from sshconf import SshConfig


class Host:
    def __init__(self, dnsname: str, props: Dict[str, str]):
        # print(dnsname, props)
        self.dnsname = dnsname
        self.name = list(reversed(dnsname.replace("-dev", ".dev").split(".")))
        self.group = ".".join(self.name[:-1])
        self.leafname = self.name[-1]
        self.fullname = ".".join(self.name)
        self.profile = props.get("$profile")

        def parse_tunnel(x: str):
            f, _, t = [u.strip() for u in x.partition("=")]
            pf = int(f)
            pt = int(t) if t else pf
            return pf, pt
        self.tunnels = [parse_tunnel(x) for x in props.get("$tunnels", "").split(",") if x.strip()]

    def __repr__(self):
        return self.fullname

    def sortkey(self):
        return self.group.ljust(30) + self.leafname


def readconfig(p=False):
    configfile = expanduser("~/.ssh/config")
    with open(configfile) as cf:
        conf = SshConfig(cf.readlines())

    hostprops = defaultdict(dict)

    for h in conf.hosts():
        props = conf.host(h)
        if "*" in h:
            if "$expand" in props:
                for e in props["$expand"].split(","):
                    hostprops[h.replace("*", e.strip())].update(props)
            else:
                if p:
                    print(f"Skip {h}")
        else:
            hostprops[h].update(props)

    if p:
        print(PrettyPrinter().pprint(hostprops))

    hostlist = [Host(h, p) for h, p in hostprops.items()]
    hostlist.sort(key=Host.sortkey)
    return hostlist


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = "indicator"

    if cmd == "indicator":
        indicator.start()
    else:
        print(f"Unknown command {cmd}")
        exit(1)
