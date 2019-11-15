#!/bin/bash
set -e
cd $(dirname $0)
exec -a sshanty python3 sshanty.py >> sshanty.log 2>&1
