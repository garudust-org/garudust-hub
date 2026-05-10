#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || -z "$1" ]]; then
    echo "Error: file path argument is required" >&2
    exit 1
fi

if [[ ! -f "$1" ]]; then
    echo "Error: file not found: $1" >&2
    exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/tmp/garudust_token_count"

if [[ ! -f "$BINARY" ]]; then
    echo "Compiling token_count..." >&2
    rustc -O "$DIR/main.rs" -o "$BINARY"
fi

"$BINARY" "$1"
