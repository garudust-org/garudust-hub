## Tool name

`tool_name`

## Description

<!-- What does this tool do? Why is it useful? -->

## Checklist

- [ ] Folder name matches `name` field in `tool.yaml`
- [ ] `tool.yaml` passes schema validation (`check-jsonschema --schemafile schemas/tool.schema.json tools/<name>/tool.yaml`)
- [ ] `run.sh` is executable (`chmod +x`) if present
- [ ] Entry added to `index.yaml`
- [ ] Tested manually with at least one real input
- [ ] `destructive` flag is set correctly
- [ ] No API key or credentials required (or clearly documented if unavoidable)

## Dependencies

<!-- List any non-standard binaries your tool requires (e.g. zbarimg, ffmpeg) -->
None

## Example

```bash
# command and output
```
