# Contributing

This project uses a packaged CLI with entry-point based language providers.

## Project layout

```text
src/wotd/
  cli.py                 # CLI entrypoint
  core.py                # shared fetching, rendering, and provider discovery
  languages/
    english.py           # English provider
    japanese.py          # Japanese provider
```

## Language providers

Language providers are registered through the `wotd.languages` entry-point group in `pyproject.toml`.

```toml
[project.entry-points."wotd.languages"]
en = "wotd.languages.english:get_provider"
ja = "wotd.languages.japanese:get_provider"
```

Each provider returns a `LanguageProvider` that defines:

- the language code
- the source attribution text
- how to build the request for the selected language or variant
- the parse function that converts raw bytes into a `WordEntry`
- any supported variants, such as JLPT levels for Japanese

For the provider interface, examples, and guidance on adding a new language, see `src/wotd/languages/README.md`.
