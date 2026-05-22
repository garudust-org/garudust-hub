#!/usr/bin/env bash
set -euo pipefail
image_path="$1"
if [[ ! -f "$image_path" ]]; then
  echo "Error: file not found: $image_path" >&2
  exit 1
fi
# zbarimg exits non-zero (code 4) when it finds no barcode. Under `set -e`
# that would abort this script at the assignment, before the empty-result
# check below ever runs — `|| true` keeps it going.
result=$(zbarimg --quiet --raw "$image_path" 2>/dev/null || true)
if [[ -z "$result" ]]; then
  # "No QR code" is a normal outcome, not a failure: exit 0 with the message
  # on stdout so the caller treats it as a result, not a tool error.
  echo "No QR code found in image."
  exit 0
fi
echo "$result"
