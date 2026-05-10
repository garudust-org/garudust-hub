#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || -z "$1" ]]; then
    echo "Error: YAML file path argument is required" >&2
    exit 1
fi

if [[ ! -f "$1" ]]; then
    echo "Error: file not found: $1" >&2
    exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -d "$DIR/node_modules" ]]; then
    echo "Installing dependencies..." >&2
    npm install --prefix "$DIR" --silent >&2
fi

node "$DIR/index.js" "$1"
