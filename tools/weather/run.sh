#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || -z "$1" ]]; then
    echo "Error: city argument is required" >&2
    exit 1
fi

city="$1"
curl -s "wttr.in/${city}?format=3"
