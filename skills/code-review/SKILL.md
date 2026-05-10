---
name: code-review
description: Systematic checklist for reviewing pull requests — correctness, security, readability, and tests
version: 1.0.0
permissions:
  terminal: true
  web_fetch: false
---

## How to approach a code review

When asked to review code or a PR, work through the following checklist in order. Report findings grouped by severity: **critical** → **warning** → **suggestion**.

## 1. Understand the intent

- Read the PR description or commit message first
- Identify what problem this change is solving
- Check if the approach makes sense before reading line by line

## 2. Correctness

- Does the code do what it claims to do?
- Are edge cases handled? (empty input, null/nil, zero, negative numbers, large values)
- Are error paths handled and do they fail clearly?
- Are there off-by-one errors, race conditions, or incorrect assumptions?

## 3. Security

- Is any user input validated before use?
- Are there SQL injection, command injection, or XSS risks?
- Are secrets or credentials accidentally included?
- Are file paths sanitized against traversal attacks?
- Are permissions or authorization checks correct?

## 4. Tests

- Are there tests for the new behavior?
- Do the tests cover the happy path AND edge cases?
- Are tests actually asserting meaningful things (not just that code runs)?
- Would a future refactor break the tests even if behavior is preserved? (over-specified tests)

## 5. Readability

- Can you understand what each function does from its name and signature?
- Are variables named clearly?
- Is there complex logic that would benefit from a short comment explaining *why*?
- Is dead code, debug output, or TODOs left in?

## 6. Scope

- Does the change do only what it claims? (no unrelated refactors bundled in)
- Are there changes that should be split into a separate PR?

## Output format

Summarize findings as:

```
## Review Summary

**Critical** (must fix before merge):
- [file:line] description

**Warning** (should fix):
- [file:line] description

**Suggestion** (optional improvement):
- [file:line] description

**Verdict:** Approve / Request changes / Needs discussion
```

If there are no issues, say so explicitly — an empty review is not helpful.
