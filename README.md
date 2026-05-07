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

| Tool | Description | Requires |
|---|---|---|
| `weather` | Get current weather for a city (wttr.in) | — |
| `hash_text` | Compute SHA-256 hash of a string | — |
| `read_qr` | Decode a QR code from an image file | `zbarimg` (`brew install zbar`) |

## Contributing a tool

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Quick version:

1. Create a folder under `tools/<tool_name>/`
2. Add `tool.yaml` (validated against [`schemas/tool.schema.json`](schemas/tool.schema.json))
3. Add `run.sh` if the command is more than a one-liner
4. Add an entry to `index.yaml`
5. Open a pull request — CI will check schema validity and index sync automatically

```
tools/my_tool/
├── tool.yaml   # name, description, schema, command
└── run.sh      # optional script (reference as ./run.sh in command)
```

## License

[MIT](LICENSE)
