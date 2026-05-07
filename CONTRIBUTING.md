# Contributing to garudust-hub

Thanks for helping grow the community tool library!

## Quick overview

Each tool lives in `tools/<tool_name>/` and requires:

```
tools/my_tool/
├── tool.yaml   # required — metadata, schema, command
└── run.sh      # optional — script referenced by command
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
schema:
  type: object
  properties:
    param_name:
      type: string
      description: What this parameter is for
  required: [param_name]
command: some-binary {param_name}
```

**Rules:**
- `name` must be snake_case and match the folder name
- `description` must be at least 10 characters
- `toolset` must be `"hub"`
- Placeholders in `command` must match keys in `schema.properties`
- Validate against the schema before submitting: see [Validation](#validation)

### 4. Write `run.sh` (if needed)

Use `run.sh` when the command is more than a one-liner. Reference it as `./run.sh {param}` in `tool.yaml`.

```bash
#!/usr/bin/env bash
set -euo pipefail
# your logic here
```

Make it executable:

```bash
chmod +x tools/my_tool/run.sh
```

### 5. Update `index.yaml`

Add an entry at the bottom of the `tools:` list:

```yaml
  - name: my_tool
    description: One sentence describing what this tool does.
    version: "1.0.0"
    files:
      - tool.yaml
      - run.sh     # only if run.sh exists
```

### 6. Validate your tool.yaml

```bash
pip install check-jsonschema
check-jsonschema --schemafile schemas/tool.schema.json tools/my_tool/tool.yaml
```

### 7. Test manually

Run your tool locally before opening a PR:

```bash
# example
bash tools/my_tool/run.sh "some input"
```

### 8. Open a pull request

Use the PR template checklist. CI will automatically validate all `tool.yaml` files and check that `index.yaml` is in sync.

---

## Tool guidelines

| Guideline | Detail |
|---|---|
| No API keys | Tools should work without authentication where possible |
| Non-destructive by default | Set `destructive: true` only if the tool modifies external state |
| Single responsibility | Each tool does one thing well |
| Dependency disclosure | If your tool requires a non-standard binary (e.g. `zbarimg`), note it in the PR description |

---

## CI checks

Every PR runs:
1. **Schema validation** — all `tool.yaml` files must conform to `schemas/tool.schema.json`
2. **Index sync check** — every folder in `tools/` must have a matching entry in `index.yaml`

Fix any CI failures before requesting a review.
