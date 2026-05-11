---
name: log-analyst
description: Analyse log files to find error patterns, detect anomalies, trace requests, and summarise incidents — works on any log format
version: 1.1.0
permissions:
  terminal: true
  files: true
  delegate: true
---

## When to use this skill

Load this skill whenever the user asks to:
- Read, search, or analyse a log file
- Find errors, warnings, or unusual patterns
- Detect anomaly spikes in log volume or error rate
- Trace a specific request, session, or user across log files
- Summarise what went wrong during an incident

## General rules

- **Never read a large file with read_file directly.** Always pre-filter with `run_command` using `grep`, `awk`, `tail`, or `head` first. Log files can be gigabytes — only pass relevant lines to the LLM.
- When the user does not specify a log path, check `~/.garudust/garudust.log` first, then ask.
- When multiple log files need analysis, use `delegate_tasks` to read them in parallel.
- Always report findings in plain language — timestamps, counts, and concrete examples, not vague descriptions.

## Mode 1 — Error pattern analysis

Use when: user wants to know what errors are occurring and how often.

```bash
# Count and rank error types
grep -iE "error|exception|fatal|critical|warn" <logfile> | sort | uniq -c | sort -rn | head -30

# Show context around the most frequent error
grep -m 10 "<error string>" <logfile>

# Errors per hour
grep -iE "error|exception" <logfile> | awk '{print $1, $2}' | cut -c1-13 | sort | uniq -c
```

After running:
1. Identify the top 3–5 error types by frequency
2. Show a concrete example line for each
3. Note if any error is new (first occurrence timestamp) vs recurring

## Mode 2 — Anomaly detection

Use when: user wants to know if anything is unusual — traffic spikes, sudden error rate increase, gaps in logs.

```bash
# Request or log line count per minute
awk '{print $1, $2}' <logfile> | cut -c1-16 | sort | uniq -c

# Error rate per hour (errors vs total lines)
grep -c "ERROR" <logfile>
wc -l <logfile>

# Find gaps longer than N minutes (no log lines)
awk '{print $1"T"$2}' <logfile> | sort | uniq
```

After running:
1. Plot the frequency distribution in text (e.g. "14:00–14:05: 120 lines, 14:05–14:10: 4 lines — gap detected")
2. Flag periods where error rate > 5% of total lines as anomalous
3. Flag any gap > 5 minutes in an otherwise active log as suspicious
4. Compare first-half vs second-half volume if no time range is given

## Mode 3 — Request tracing

Use when: user provides a request ID, session ID, user ID, or IP address and wants to follow it through logs.

```bash
# Trace a specific ID across one file
grep "<id>" <logfile>

# Trace across multiple files
grep -r "<id>" <log_directory>/

# Follow the full lifecycle (sort by timestamp)
grep "<id>" <logfile> | sort -k1,2
```

After running:
1. Show every log line for that ID in chronological order
2. Reconstruct what happened: entry point → processing steps → outcome
3. Highlight any error or timeout in the trace
4. Note if the ID appears in some files but not others (partial trace = potential data loss)

## Mode 4 — Parallel multi-file analysis

Use when: the user has multiple log files (e.g. multiple services, multiple servers) that need analysis together.

Use `delegate_tasks` to analyse each file concurrently:

```
delegate_tasks([
  { task: "analyse errors in /var/log/api.log", context: "look for 5xx errors and exceptions" },
  { task: "analyse errors in /var/log/worker.log", context: "look for job failures and timeouts" },
  { task: "analyse errors in /var/log/db.log", context: "look for slow queries and connection errors" }
])
```

After all sub-agents return:
1. Merge findings by timestamp to find correlated events across services
2. Identify which service showed problems first (likely root cause)
3. Show the chain of failures if applicable

## Mode 5 — Incident summary

Use when: user wants a human-readable summary of what happened during an incident or time window.

Steps:
1. Ask for the time range (start and end) if not provided
2. Filter logs to that window: `awk '$0 >= "2024-01-15 14:00" && $0 <= "2024-01-15 14:30"' <logfile>`
3. Run Mode 1 (errors) and Mode 2 (anomalies) on the filtered window
4. Write a structured incident report:

```
## Incident Summary

**Time window:** 14:00–14:30
**Affected service:** [service name]

**Timeline:**
- 14:02 — first error appeared (DatabaseConnectionError)
- 14:05 — error rate spiked to 80% of requests
- 14:18 — errors stopped

**Root cause (likely):** [based on log evidence]

**Top errors:**
1. DatabaseConnectionError — 342 occurrences
2. TimeoutException — 87 occurrences

**Recommendation:** [next steps]
```

## Output format

Always end with a short **Summary** block:
- What was found (or "no issues found")
- Severity: `INFO` / `WARNING` / `ERROR` / `CRITICAL`
- Recommended next action
