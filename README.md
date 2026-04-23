# wotd

A small packaged CLI for fetching and displaying a word of the day from pluggable language providers.

## What it does

- Displays the newest word of the day for a selected language
- Supports provider-specific parsing behind a shared CLI
- Loads language providers through Python entry points

## Current languages

| Code | Source |
| --- | --- |
| `en` | Merriam-Webster |
| `ja` | Innovative Language |

## Install and run

With `uv`:

```bash
uv tool install wotd

wotd
wotd en
wotd ja
```

Use the built-in help to see the currently registered language codes:

```bash
uv run wotd --help
```

## Project layout

```text
src/wotd/
  cli.py                 # CLI entrypoint
  core.py                # shared fetching, rendering, and provider discovery
  languages/
    english.py           # English provider
    japanese.py          # Japanese provider
```

## Entry-point based languages

Language providers are registered through the `wotd.languages` entry-point group in `pyproject.toml`.

```toml
[project.entry-points."wotd.languages"]
en = "wotd.languages.english:get_provider"
ja = "wotd.languages.japanese:get_provider"
```

Each provider returns a `LanguageProvider` that defines:

- the language code
- the source attribution text
- the request details
- the parse function that converts raw bytes into a `WordEntry`

For contributor guidance, see `src/wotd/languages/README.md`.
