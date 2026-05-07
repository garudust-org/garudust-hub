#!/usr/bin/env bash
set -euo pipefail
city="$1"
curl -s "wttr.in/${city}?format=3"
