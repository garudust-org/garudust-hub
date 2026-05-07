# garudust-hub

Community tool repository for [Garudust Agent](https://github.com/garudust-org/garudust-agent).

## Install a tool

```bash
garudust tool install weather
```

## List available tools

```bash
garudust tool list
```

## Available tools

| Tool | Description |
|---|---|
| `weather` | Get current weather for a city (wttr.in, no API key) |
| `hash_text` | Compute SHA-256 hash of a string |

## Contributing a tool

Each tool is a folder under `tools/` containing:

```
tools/my_tool/
├── tool.yaml   # name, description, schema, command
└── run.sh      # optional script (reference as ./run.sh in command)
```

Add an entry to `index.yaml` and open a pull request.
