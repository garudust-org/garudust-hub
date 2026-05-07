# garudust-hub

Community tool repository for [Garudust Agent](https://github.com/garudust-org/garudust-agent).

![CI](https://github.com/garudust-org/garudust-hub/actions/workflows/ci.yml/badge.svg)

## Install a tool

```bash
garudust tool install weather
```

## List available tools

```bash
garudust tool list
```

## Available tools

| Tool | Description | Language | Requires |
|---|---|---|---|
| `weather` | Get current weather for a city (wttr.in) | Bash | — |
| `hash_text` | Compute SHA-256 hash of a string | Inline | — |
| `read_qr` | Decode a QR code from an image file | Bash | `zbarimg` (`brew install zbar`) |
| `csv_to_json` | Convert a CSV file to a JSON array of objects | Python | `python3` |
| `token_count` | Count characters, words, and estimated LLM tokens | Rust | `rustc` |

## Writing tools in different languages

Tools can be written in any language. The `command` field in `tool.yaml` is a plain shell command — set the interpreter there, and declare runtime dependencies in `requires`.

### Inline (no script file)

Best for one-liners using standard Unix tools.

```yaml
command: printf '%s' {text} | shasum -a 256 | awk '{print $1}'
```

No `requires` needed if the tools are part of a standard Unix environment.

---

### Bash

```
tools/my_tool/
├── tool.yaml
└── run.sh
```

```yaml
requires: []   # or omit entirely
command: ./run.sh {param}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "$1"
```

**Limitations:** Bash is available everywhere but not ideal for complex data processing or error handling.

---

### Python

```
tools/my_tool/
├── tool.yaml
└── run.py
```

```yaml
requires: [python3]
command: python3 ./run.py {param}
```

```python
#!/usr/bin/env python3
import sys
print(sys.argv[1])
```

**Limitations:** Only Python stdlib — tools must not run `pip install` at runtime. If an external package is truly required, document it clearly in `requires` and the PR description.

---

### Node.js

```
tools/my_tool/
├── tool.yaml
└── run.js
```

```yaml
requires: [node]
command: node ./run.js {param}
```

```js
#!/usr/bin/env node
console.log(process.argv[2]);
```

**Limitations:** Same as Python — only Node.js built-in modules. No `npm install` at runtime.

---

### Rust

```
tools/my_tool/
├── tool.yaml
├── run.sh      ← build wrapper
└── main.rs
```

```yaml
requires: [rustc]
command: ./run.sh {param}
```

`run.sh` compiles `main.rs` on first use and caches the binary:

```bash
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/tmp/garudust_my_tool"
if [[ ! -f "$BINARY" ]]; then
    rustc -O "$DIR/main.rs" -o "$BINARY"
fi
"$BINARY" "$1"
```

**Limitations:**
- Only Rust stdlib — no `cargo` or external crates (single-file `rustc` only)
- First run incurs a compile step (~1–3s)
- Do **not** commit pre-compiled binaries — they are platform-specific and inflate the repo

---

## Contributing a tool

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Quick version:

1. Create a folder under `tools/<tool_name>/`
2. Add `tool.yaml` (validated against [`schemas/tool.schema.json`](schemas/tool.schema.json))
3. Add your script file and make it executable (`chmod +x`)
4. Add an entry to `index.yaml`
5. Open a pull request — CI checks schema, index sync, and executable bits automatically

## License

[MIT](LICENSE)
