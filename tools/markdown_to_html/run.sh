#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || -z "$1" ]]; then
    echo "Error: markdown file path argument is required" >&2
    exit 1
fi

if [[ ! -f "$1" ]]; then
    echo "Error: file not found: $1" >&2
    exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/tmp/garudust_markdown_to_html"

if [[ ! -f "$BINARY" ]]; then
    echo "Building markdown_to_html (first run)..." >&2
    cargo build --release --manifest-path "$DIR/Cargo.toml" >&2
    cp "$DIR/target/release/markdown_to_html" "$BINARY"
fi

"$BINARY" "$1"
