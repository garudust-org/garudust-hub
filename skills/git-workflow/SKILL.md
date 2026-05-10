---
name: git-workflow
description: Conventional commits, branch naming, and PR best practices for every git operation
version: 1.0.0
permissions:
  terminal: true
---

## Commit messages

Always use conventional commits format:

```
<type>(<scope>): <short summary>
```

**Types:**
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or updating tests
- `chore` — build process, tooling, dependencies

**Rules:**
- Summary in lowercase, no period at the end
- Keep under 72 characters
- Use imperative mood ("add" not "added", "fix" not "fixed")
- Add body if the why is non-obvious, separated by a blank line

**Examples:**
```
feat(auth): add JWT refresh token support
fix(csv): handle rows with quoted commas correctly
docs: update contributing guide with skill authoring section
```

## Branch naming

```
<type>/<short-description>
```

Examples: `feat/add-weather-tool`, `fix/csv-quoted-commas`, `docs/skill-guide`

## Before committing

1. Run the project's test suite if one exists
2. Check that CI-relevant files have not introduced obvious issues
3. Stage only the files relevant to this change — avoid `git add .` when unrelated files are modified
4. Do not skip hooks (`--no-verify`) unless explicitly instructed

## Pull requests

- Title follows the same convention as commit messages
- Body explains **why**, not just what changed
- Link related issues with `Closes #N` if applicable
- Keep PRs focused — one concern per PR
- Do not force-push to shared branches

## When the user says "commit" or "push"

1. Run `git status` to understand what has changed
2. Run `git diff` to review unstaged changes
3. Draft a commit message following the rules above
4. Stage relevant files explicitly
5. Confirm with the user before pushing to a remote if the branch is shared
