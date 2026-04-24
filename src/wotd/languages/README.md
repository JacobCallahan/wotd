# Adding a language provider

Language support is extension-based. Each language is implemented as its own provider module and registered through the `wotd.languages` entry-point group.

## Provider shape

A provider module should export a `get_provider()` function that returns `wotd.core.LanguageProvider`.

The provider defines:

- `language`: short code exposed in the CLI, such as `en` or `ja`
- `source`: muted source attribution shown in output
- `build_request`: a function that returns a `SourceRequest` for the selected variant
- `parse`: a function that converts fetched bytes into a `WordEntry`
- optional `variants`: extra suffixes such as `n1` through `n5`
- optional `default_variant`: the suffix used when the base language code is requested

## Minimal example

```python
from wotd.core import LanguageProvider, SourceRequest, WordEntry


def get_provider():
    return LanguageProvider(
        language="es",
        source="Example Source",
        build_request=build_request,
        parse=parse_entry,
        variants=("easy", "hard"),
        default_variant="easy",
    )


def build_request(variant):
    difficulty = variant or "easy"
    return SourceRequest(url=f"https://example.com/wotd/{difficulty}")


def parse_entry(source_bytes, variant):
    text = source_bytes.decode("utf-8", errors="replace")
    return WordEntry(
        title="hola",
        definitions=["hello"],
        description=text,
        source="Example Source",
    )
```

## Register the provider

Add the provider to `pyproject.toml`:

```toml
[project.entry-points."wotd.languages"]
es = "wotd.languages.spanish:get_provider"
```

The entry-point name is the language code shown in the CLI help and accepted as the positional argument.

If a provider exposes variants, users can request them with `language-variant`, such as `ja-n3`.

## Output options

Providers can return either:

1. `definitions` plus optional `description`, which fits dictionary-style output
2. `facts`, which fits structured outputs like the Japanese provider (`Kanji`, `Kana`, `Romaji`, `English definition`)

## Implementation notes

- Keep provider-specific parsing inside the provider module
- Reuse helpers from `wotd.core` where it makes sense
- Raise `WOTDError` for provider-specific fetch/parse failures that should surface to the user
- Preserve stable language codes, since they are part of the CLI interface
