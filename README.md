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
| `en-hard` | Wordsmith.org |
| `en-idiom` | EnglishClub |
| `ja` | Kanji of the Day (`ja` defaults to `ja-n5`) |
| `ja-n1` to `ja-n5` | Kanji of the Day JLPT feeds |

## Install and run

With `uv`:

```bash
uv tool install wotd

wotd
wotd en
wotd en-hard
wotd en-idiom
wotd ja
wotd ja-n3
```

Use the built-in help to see the currently registered language codes:

```bash
wotd --help
```

## Contributing

Contributor-facing implementation details, project layout, and extension guidance live in `CONTRIBUTING.md`.
