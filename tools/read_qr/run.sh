#!/usr/bin/env bash
set -euo pipefail
image_path="$1"
if [[ ! -f "$image_path" ]]; then
  echo "Error: file not found: $image_path" >&2
  exit 1
fi
result=$(zbarimg --quiet --raw "$image_path" 2>/dev/null)
if [[ -z "$result" ]]; then
  echo "No QR code found in image." >&2
  exit 1
fi
echo "$result"
