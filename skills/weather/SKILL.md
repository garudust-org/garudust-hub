---
name: weather
description: Get current weather for any city via wttr.in — no API key required. Use http_request instead of the weather hub tool.
version: 1.0.0
---

## When to use this skill

Load this skill whenever the user asks about current weather, temperature, or conditions for a specific city or location.

## How to get weather

Call `http_request` with:

```
method: GET
url: https://wttr.in/{city}?format=3
```

Replace `{city}` with the city name from the user's request (URL-encode spaces as `+`, e.g. `New+York`).

The response is a single line in this format:
```
Bangkok: 🌦 +32°C
```

Return that line directly to the user.

## Edge cases

- **City not found** — wttr.in returns `Unknown location` or an error message. Tell the user the city wasn't recognised and ask them to try a different spelling.
- **City name with spaces** — replace spaces with `+` in the URL (e.g. `New+York`, `Chiang+Mai`).
- **Country disambiguation** — if the user gives an ambiguous city name, append the country code (e.g. `Springfield+US`).
- **Non-English city names** — pass the name as-is; wttr.in handles transliteration.

## Do not

- Do not use the `weather` hub tool — this skill replaces it with no subprocess dependency.
- Do not call any other weather API or use `run_command` with `curl`.
