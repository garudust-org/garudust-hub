#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/tmp/garudust_markdown_to_html"

if [[ ! -f "$BINARY" ]]; then
    echo "Building markdown_to_html (first run)..." >&2
    cargo build --release --manifest-path "$DIR/Cargo.toml" >&2
    cp "$DIR/target/release/markdown_to_html" "$BINARY"
fi

"$BINARY" "$1"
