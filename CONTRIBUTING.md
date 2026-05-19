# Contributing to garudust-hub

Thanks for helping grow the community tool library!

## Quick overview

Each tool lives in `tools/<tool_name>/` and requires:

```
tools/my_tool/
├── tool.yaml      # required — metadata, schema, command
└── run.sh / run.py / run.js / ...   # optional script referenced by command
```

An entry must also be added to `index.yaml`.

---

## Step-by-step guide

### 1. Fork and clone

```bash
git clone https://github.com/garudust-org/garudust-hub.git
cd garudust-hub
```

### 2. Create the tool folder

Use snake_case for the folder name. The name must match the `name` field in `tool.yaml`.

```bash
mkdir tools/my_tool
```

### 3. Write `tool.yaml`

```yaml
name: my_tool
description: One sentence describing what this tool does.
toolset: hub
destructive: false        # true if the tool writes/deletes external state
requires: [python3]       # optional — runtimes or binaries needed
env_required: [MY_API_KEY]  # optional — secrets forwarded from ~/.garudust/.env
schema:
  type: object
  properties:
    param_name:
      type: string
      description: What this parameter is for
  required: [param_name]
command: python3 ./run.py {param_name}

# Optional — declare default models for vision/LLM tools.
# Users can override these in their config.yaml under tools.<name>.model.
# model: gemini-flash-latest
# fallback_model: openai/gpt-4o-mini
```

**Rules:**
- `name` must be snake_case and match the folder name
- `description` must be at least 10 characters
- `toolset` must be `"hub"`
- `requires` is optional but must be filled when the tool depends on a non-standard binary
- `env_required` lists secrets the tool reads from `~/.garudust/.env`; only those keys are forwarded
- Placeholders in `command` must match keys in `schema.properties`
- Validate against the schema before submitting: see [Validation](#validation)

### LLM-enabled tools — env vars injected by the agent

When a tool declares `model` / `fallback_model` hints in `tool.yaml`, the agent writes skeleton entries into `config.yaml` on install. Users fill in the credentials:

```yaml
# ~/.garudust/config.yaml
tools:
  my_tool:
    vision:                        # slot name — any name without "fallback" = primary
      name: google                 # builtin provider name (inherits base URL)
      key: ${GOOGLE_AI_API_KEY}    # ${ENV_VAR} or literal key
      model: gemini-flash-latest
    vision-fallback:               # slot name containing "fallback" = fallback
      name: openrouter
      key: ${OPENROUTER_API_KEY}
      model: nvidia/nemotron-nano-12b-v2-vl:free
```

The agent injects these env vars into the tool subprocess for each slot:

| Env var | Slot type | Value |
|---|---|---|
| `GARUDUST_MODEL` | primary | Model name from the slot |
| `GARUDUST_BASE_URL` | primary | Provider base URL (from `name:` or `url:`) |
| `GARUDUST_API_KEY` | primary | Resolved API key |
| `GARUDUST_FALLBACK_MODEL` | fallback | Model name from the fallback slot |
| `GARUDUST_FALLBACK_BASE_URL` | fallback | Provider base URL for the fallback |
| `GARUDUST_FALLBACK_API_KEY` | fallback | Resolved API key for the fallback |

**Best practice for tool scripts:** prefer `GARUDUST_API_KEY` over a named env var, and fall back to the named var for standalone/cross-agent portability:

```python
# Python example
import os
api_key = os.environ.get("GARUDUST_API_KEY") or os.environ.get("MY_PROVIDER_API_KEY", "")
model   = os.environ.get("GARUDUST_MODEL", "default-model-name")
```

```bash
# Bash example
API_KEY="${GARUDUST_API_KEY:-${MY_PROVIDER_API_KEY:-}}"
MODEL="${GARUDUST_MODEL:-default-model-name}"
```

### 4. Write your script (any language)

Tools can be written in any language as long as the interpreter is available on the user's system. Reference the script in `command` with the appropriate interpreter.

**Bash**
```bash
#!/usr/bin/env bash
set -euo pipefail
param="$1"
# your logic here
```
```yaml
command: ./run.sh {param}
```

**Python**
```python
#!/usr/bin/env python3
import sys
param = sys.argv[1]
# your logic here
```
```yaml
requires: [python3]
command: python3 ./run.py {param}
```

**Node.js**
```js
#!/usr/bin/env node
const param = process.argv[2];
// your logic here
```
```yaml
requires: [node]
command: node ./run.js {param}
```

**Inline (no script file needed)**
```yaml
command: printf '%s' {text} | shasum -a 256 | awk '{print $1}'
```

Make the script file executable:
```bash
chmod +x tools/my_tool/run.py   # or run.sh, run.js, etc.
```

### 5. Update `index.yaml`

Add an entry at the bottom of the `tools:` list:

```yaml
  - name: my_tool
    description: One sentence describing what this tool does.
    version: "1.0.0"
    files:
      - tool.yaml
      - run.py     # whatever script file you added
```

### 6. Validate your tool.yaml

```bash
pip install check-jsonschema
check-jsonschema --schemafile schemas/tool.schema.json tools/my_tool/tool.yaml
```

### 7. Test manually

```bash
python3 tools/my_tool/run.py "some input"
# or
bash tools/my_tool/run.sh "some input"
```

### 8. Open a pull request

Use the PR template checklist. CI will automatically validate all `tool.yaml` files, check that `index.yaml` is in sync, and verify that script files are executable.

---

## Tool guidelines

| Guideline | Detail |
|---|---|
| No API keys | Tools should work without authentication where possible |
| Non-destructive by default | Set `destructive: true` only if the tool modifies external state |
| Single responsibility | Each tool does one thing well |
| Declare dependencies | List all required runtimes/binaries in `requires` — this is machine-readable and shown to users before install |
| No pip/npm install at runtime | Tools must not install packages on the fly; dependencies must already be present |

---

## CI checks

Every PR runs:
1. **Schema validation** — all `tool.yaml` files must conform to `schemas/tool.schema.json`
2. **Index sync check** — every folder in `tools/` must have a matching entry in `index.yaml`
3. **Name match check** — `name` in `tool.yaml` must match its folder name
4. **Executable check** — script files referenced in `command` must have the executable bit set

Fix any CI failures before requesting a review.

---

## Contributing a skill

Skills are Markdown instruction sets that tell the agent *how* to behave during a workflow. They are different from tools — no code is executed, only natural language instructions loaded into the agent's context.

### Skill structure

```
skills/my-skill/
├── SKILL.md          # required — frontmatter + instructions
└── scripts/          # optional — helper scripts (any language)
    └── helper.sh
```

### Writing `SKILL.md`

```markdown
---
name: my-skill
description: One sentence describing when to use this skill.
version: 1.0.0
permissions:
  terminal: true      # allow terminal tool
  web_fetch: false    # deny web_fetch
---

## Instructions

Write natural language instructions here. Tell the agent exactly
how to behave, what to check, and what output format to use.
```

**Rules:**
- `name` must be lowercase, digits, and hyphens only — no underscores (agentskills.io compatible)
- `description` explains *when* the agent should load this skill
- `permissions` is optional — omit to leave all tools unrestricted
- Use `allowed-tools: terminal read_file` as an alternative to `permissions` (agentskills.io format)

### Adding `scripts/`

Helper scripts in `scripts/` are downloaded and made executable automatically on `skill install`. Name them clearly and make them executable locally before committing:

```bash
chmod +x skills/my-skill/scripts/helper.sh
```

### Update `index.yaml`

Add an entry under `skills:`:

```yaml
  - name: my-skill
    description: One sentence describing when to use this skill.
    version: "1.0.0"
    files:
      - SKILL.md
      - scripts/helper.sh   # only if scripts exist
```

### Install locally to test

```bash
garudust skill install garudust-org/garudust-hub/skills/my-skill
garudust skill list
```
