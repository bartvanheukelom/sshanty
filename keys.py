import subprocess
import pandas as pd

import sshanty


def parse_ak(ak):
    def parse_line(l):
        key, _, name = l.rpartition(" ")
        return key, name
    return [parse_line(l) for l in ak.splitlines()]


class KeyInfo:
    def __init__(self, ref, key):
        self.ref = ref
        self.key = key
        self.names = set()
        self.hosts = set()

    def __repr__(self):
        return str(self.ref)


def make_ak(keys):
    return "".join([f"{k.key} {k.ref}\n" for k in keys])


class KeyManager:

    def __init__(self):

        self.hostlist = sshanty.readconfig()

        self.keys = {}

        for key, name in parse_ak(subprocess.check_output(['ssh-add', '-L']).decode("utf8")):
            if key not in self.keys:
                self.keys[key] = KeyInfo(name, key)
            k = self.keys[key]

            k.names.add(name)

    def put_ak(self, ak):
        for h in self.hostlist:
            print(f"{h.dnsname} put...", end="")
            try:
                subprocess.run(['timeout', '5', 'ssh', h.dnsname, 'cat > .ssh/authorized_keys'],
                               input=ak.encode("utf8"), check=True)
                print(f"{h.dnsname} put X")
            except Exception as e:
                print(f"Error putting to {h.dnsname}: {e}")

    def find_used(self):

        # clear
        for k in self.keys.values():
            k.hosts = set()

        for h in self.hostlist:
            print(f"{h.dnsname}...", end="")
            try:
                for key, name in parse_ak(subprocess.check_output(['timeout', '5', 'scp', f'{h.dnsname}:.ssh/authorized_keys', '/dev/stdout']).decode("utf8")):
                    if key not in self.keys:
                        self.keys[key] = KeyInfo(name, key)
                    k = self.keys[key]
                    k.names.add(name)
                    k.hosts.add(h.dnsname)
                print(f"{h.dnsname} X")
            except Exception as e:
                print(f"Error getting keys installed on host {h.dnsname}: {e}")

    def keysdf(self):
        return pd.DataFrame([(k.ref, k.key, len(k.hosts), k.hosts) for _, k in self.keys.items()])

    def hostsdf(self):
        keys = self.keys.values()

        def hostrow(h):
            return [h.dnsname] + ['X' if h.dnsname in k.hosts else '' for k in keys]
        return pd.DataFrame(
            [hostrow(h) for h in self.hostlist],
            columns=["Host"] + [k.ref for k in keys]
        )

