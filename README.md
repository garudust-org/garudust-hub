# garudust-hub

Open registry of **tools** and **skills** for [Garudust Agent](https://github.com/garudust-org/garudust-agent) — install in one command, write in any language.

- **Tools** — executable scripts the agent can call (Bash, Python, Node.js, Rust)
- **Skills** — Markdown instruction sets that shape how the agent behaves in a workflow

![CI](https://github.com/garudust-org/garudust-hub/actions/workflows/ci.yml/badge.svg)

## Install a tool

```bash
garudust tool install weather
```

## Install a skill

```bash
garudust skill install git-workflow
```

Skills from this hub can be installed by short name. Other sources are also accepted:

```bash
# Short name — resolved via the hub index (default: garudust-org/garudust-hub)
garudust skill install git-workflow

# Short name from a custom hub
garudust skill install git-workflow --hub myorg/my-hub

# Full GitHub path
garudust skill install garudust-org/garudust-hub/skills/git-workflow

# Direct URL
garudust skill install https://example.com/skills/SKILL.md

# Well-known endpoint
garudust skill install well-known:https://example.com
```

## Available tools

| Tool | Description | Language | Requires |
|---|---|---|---|
| `weather` | Get current weather for a city (wttr.in) | Bash | — |
| `hash_text` | Compute SHA-256 hash of a string | Inline | — |
| `read_qr` | Decode a QR code from an image file | Bash | `zbarimg` |
| `csv_to_json` | Convert a CSV file to a JSON array of objects | Python | `python3` |
| `token_count` | Count characters, words, and estimated LLM tokens | Rust | `rustc` |
| `fetch_title` | Fetch the HTML title of a webpage | Python + uv | `uv` |
| `markdown_to_html` | Convert a Markdown file to HTML | Rust + cargo | `cargo` |
| `yaml_to_json` | Convert a YAML file to formatted JSON | Node.js + npm | `node`, `npm` |
| `file_info` | Return size, MIME type, encoding, and line count of a file | Python | `python3` |
| `extract_urls` | Extract all URLs from an HTML or plain text file | Python + uv | `uv` |
| `facebook_post` | Post text or photo to a Facebook Page via Graph API | Python + uv | `uv`, `FACEBOOK_ACCESS_TOKEN` |

## Available skills

Skills load natural language instructions into the agent's context — they shape *how* the agent behaves, not what it can run.

| Skill | Description | Install |
|---|---|---|
| `git-workflow` | Conventional commits, branch naming, and PR best practices | `garudust skill install git-workflow` |
| `code-review` | Systematic PR review checklist — correctness, security, readability, and tests | `garudust skill install code-review` |
| `facebook-workflow` | Prepare and publish content to a Facebook Page (text or photo) | `garudust skill install facebook-workflow` |

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

**Limitations:** Restricted to Python stdlib. Tools must not run `pip install` at runtime.

---

### Python with external packages (via uv)

Use [`uv`](https://github.com/astral-sh/uv) when the tool needs third-party packages. Declare each package with `--with` in the command — `uv` resolves, installs, and caches them automatically on first run. No `pyproject.toml` or `requirements.txt` needed.

```
tools/my_tool/
├── tool.yaml
└── run.py
```

```yaml
requires: [uv]
command: uv run --with httpx --with beautifulsoup4 ./run.py {param}
```

**Limitations:** Requires `uv` (`brew install uv`). First run downloads packages; subsequent runs use the cache.

---

### Node.js (built-in modules only)

```
tools/my_tool/
├── tool.yaml
└── index.js
```

```yaml
requires: [node]
command: node ./index.js {param}
```

**Limitations:** Only Node.js built-in modules. No `npm install` at runtime.

---

### Node.js with external packages (via npm)

Use a `package.json` when the tool needs npm packages. `run.sh` installs `node_modules` on first use and reuses them on subsequent runs.

```
tools/my_tool/
├── tool.yaml
├── run.sh
├── package.json
└── index.js
```

```yaml
requires: [node, npm]
command: ./run.sh {param}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ ! -d "$DIR/node_modules" ]]; then
    npm install --prefix "$DIR" --silent >&2
fi
node "$DIR/index.js" "$1"
```

**Limitations:** `node_modules/` lives in the tool folder (gitignored). First run runs `npm install`.

---

### Rust (stdlib only)

Single-file compilation with `rustc`. No external crates.

```
tools/my_tool/
├── tool.yaml
├── run.sh
└── main.rs
```

```yaml
requires: [rustc]
command: ./run.sh {param}
```

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

**Limitations:** Rust stdlib only. First run compiles (~1–3s); binary is cached at `/tmp/`.

---

### Rust with external crates (via cargo)

Use a Cargo project when the tool needs external crates. `run.sh` runs `cargo build --release` on first use and caches the binary at `/tmp/`.

```
tools/my_tool/
├── tool.yaml
├── run.sh
├── Cargo.toml
├── Cargo.lock
└── src/
    └── main.rs
```

```yaml
requires: [cargo]
command: ./run.sh {param}
```

```bash
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/tmp/garudust_my_tool"
if [[ ! -f "$BINARY" ]]; then
    cargo build --release --manifest-path "$DIR/Cargo.toml" >&2
    cp "$DIR/target/release/my_tool" "$BINARY"
fi
"$BINARY" "$1"
```

**Limitations:** First build downloads crates and compiles (~10–60s). `target/` is gitignored. Do **not** commit pre-compiled binaries.

---

### Quick comparison

| | Inline | Bash | Python | Python + uv | Node.js | Node.js + npm | Rust | Rust + cargo |
|---|---|---|---|---|---|---|---|---|
| External packages | — | — | No | Yes | No | Yes | No | Yes |
| First-run overhead | — | — | — | pkg download | — | npm install | compile | compile + pkg |
| Requires | Nothing | Nothing | `python3` | `uv` | `node` | `node`, `npm` | `rustc` | `cargo` |
| Best for | One-liners | Shell glue | Data, text | Web, APIs | JS tooling | JS ecosystem | Performance | Performance + crates |

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
