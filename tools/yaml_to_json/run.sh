#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -d "$DIR/node_modules" ]]; then
    echo "Installing dependencies..." >&2
    npm install --prefix "$DIR" --silent >&2
fi

node "$DIR/index.js" "$1"
