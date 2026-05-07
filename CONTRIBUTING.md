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
schema:
  type: object
  properties:
    param_name:
      type: string
      description: What this parameter is for
  required: [param_name]
command: python3 ./run.py {param_name}
```

**Rules:**
- `name` must be snake_case and match the folder name
- `description` must be at least 10 characters
- `toolset` must be `"hub"`
- `requires` is optional but must be filled when the tool depends on a non-standard binary
- Placeholders in `command` must match keys in `schema.properties`
- Validate against the schema before submitting: see [Validation](#validation)

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
