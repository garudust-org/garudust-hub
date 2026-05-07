#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/tmp/garudust_token_count"

if [[ ! -f "$BINARY" ]]; then
    echo "Compiling token_count..." >&2
    rustc -O "$DIR/main.rs" -o "$BINARY"
fi

"$BINARY" "$1"
