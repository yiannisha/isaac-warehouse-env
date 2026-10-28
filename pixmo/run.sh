#!/usr/bin/env bash
# Inside the existing dell-rack-sim container. run.py preserves source/config.
set -euo pipefail
cd /workspace
exec /isaac-sim/python.sh -u /workspace/pixmo/run.py --allow-root "$@"
