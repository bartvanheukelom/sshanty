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
        return str(self.names)


class KeyManager:

    def __init__(self):

        self.hostlist = sshanty.readconfig()

        self.keys = {}

        for key, name in parse_ak(subprocess.check_output(['ssh-add', '-L']).decode("utf8")):
            if key not in self.keys:
                self.keys[key] = KeyInfo(name, key)
            k = self.keys[key]

            k.names.add(name)

    def find_used(self):

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
