# garudust-hub

Open tool registry for [Garudust Agent](https://github.com/garudust-org/garudust-agent) — write tools in any language and install them in one command.

Tools can be a single shell one-liner or a full Rust crate. Each tool declares its own schema, command, and dependencies. The agent handles the rest.

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
| `fetch_title` | Fetch the HTML title of a webpage | Python + uv | `uv` |

## Writing tools in different languages

Tools can be written in any language. The `command` field in `tool.yaml` is a plain shell command — set the interpreter there and declare runtime dependencies in `requires`.

### Inline (no script file)

Best for one-liners using standard Unix tools. No script file needed.

```yaml
command: printf '%s' {text} | shasum -a 256 | awk '{print $1}'
```

**Limitations:** Limited to what the shell and standard Unix utilities can express in one line.

---

### Bash

```
tools/my_tool/
├── tool.yaml
└── run.sh
```

```yaml
command: ./run.sh {param}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "$1"
```

**Limitations:** Available everywhere, but not ideal for complex data processing or structured output.

---

### Python (stdlib only)

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

**Limitations:** Restricted to Python stdlib. Tools must not run `pip install` at runtime.

---

### Python with external packages (via uv)

Use [`uv`](https://github.com/astral-sh/uv) when the tool needs third-party packages. Declare each package with `--with` in the command — `uv` resolves, installs, and caches them automatically on first run.

```
tools/my_tool/
├── tool.yaml
└── run.py
```

```yaml
requires: [uv]
command: uv run --with httpx --with beautifulsoup4 ./run.py {param}
```

```python
#!/usr/bin/env python3
import sys, httpx
from bs4 import BeautifulSoup
# ...
```

**Limitations:**
- Requires `uv` to be installed (`brew install uv` / `pip install uv`)
- First run downloads packages (~seconds); subsequent runs use the cache
- No `pyproject.toml` or `requirements.txt` needed — packages live in the `command` line

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

**Limitations:** Only Node.js built-in modules. No `npm install` at runtime.

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

`run.sh` compiles `main.rs` on first use and caches the binary in `/tmp/`:

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
- Rust stdlib only — no `cargo` or external crates (single-file `rustc` compilation)
- First run incurs a compile step (~1–3s)
- Do **not** commit pre-compiled binaries — they are platform-specific and inflate the repo

---

### Quick comparison

| | Inline | Bash | Python stdlib | Python + uv | Node.js | Rust |
|---|---|---|---|---|---|---|
| External packages | — | — | No | Yes | No | No |
| Compile step | — | — | — | — | — | First run |
| Requires install | Nothing | Nothing | `python3` | `uv` | `node` | `rustc` |
| Best for | One-liners | Shell glue | Data, text | Web, APIs | JS tooling | Performance |

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
