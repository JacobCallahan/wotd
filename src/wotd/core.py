from collections.abc import Callable
from dataclasses import dataclass, field
from html import unescape
from importlib.metadata import entry_points
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

DEFAULT_LANGUAGE = "en"
ENTRY_POINT_GROUP = "wotd.languages"
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "wotd/0.1.0"

THEME = Theme(
    {
        "info": "cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "title": "bold blue",
        "key": "bold magenta",
    }
)

console = Console(theme=THEME, highlight=False)


class WOTDError(Exception):
    """Raised when a word source cannot be fetched or parsed into a usable result."""


@dataclass(frozen=True)
class SourceRequest:
    url: str
    data: dict[str, str] | None = None


@dataclass(frozen=True)
class LanguageProvider:
    language: str
    source: str
    build_request: Callable[[str | None], SourceRequest]
    parse: Callable[[bytes, str | None], "WordEntry"]
    variants: tuple[str, ...] = ()
    default_variant: str | None = None


@dataclass(frozen=True)
class WordEntry:
    title: str
    source: str
    definitions: list[str] = field(default_factory=list)
    description: str = ""
    description_label: str = "Description"
    facts: list[tuple[str, str]] = field(default_factory=list)


def clean_text(text):
    return " ".join(unescape(text).replace("\xa0", " ").split())


def fetch_source(source_request):
    data = None
    if source_request.data:
        data = urlencode(source_request.data).encode()

    request = Request(
        source_request.url,
        data=data,
        headers={
            "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, text/html;q=0.7",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read()
    except HTTPError as exc:
        raise WOTDError(f"Source request failed with HTTP {exc.code}.") from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise WOTDError(f"Could not reach the Word of the Day source: {reason}.") from exc


def load_language_providers():
    providers = {}
    for entry_point in entry_points(group=ENTRY_POINT_GROUP):
        provider_factory = entry_point.load()
        provider = provider_factory()
        providers[provider.language] = provider
    return providers


def get_registered_language_codes():
    providers = load_language_providers()
    codes = []
    for provider in providers.values():
        codes.append(provider.language)
        for variant in provider.variants:
            codes.append(f"{provider.language}-{variant}")
    return sorted(set(codes))


def get_language_provider(language):
    normalized = language.strip().lower()
    if not normalized:
        normalized = DEFAULT_LANGUAGE

    providers = load_language_providers()
    provider = providers.get(normalized)
    if provider is not None:
        return provider, normalized, provider.default_variant

    base_language, separator, variant = normalized.partition("-")
    provider = providers.get(base_language)
    if provider is not None and separator:
        if variant in provider.variants:
            return provider, normalized, variant

        available = ", ".join(get_registered_language_codes())
        raise WOTDError(f"Unsupported language '{language}'. Available languages: {available}.")

    if provider is None:
        available = ", ".join(get_registered_language_codes())
        raise WOTDError(f"Unsupported language '{language}'. Available languages: {available}.")

    return provider, normalized, provider.default_variant


def render_entry(entry):
    body = Table.grid(expand=False)
    body.add_column()

    if entry.facts:
        facts = Table.grid(padding=(0, 1))
        facts.add_column(style="key", justify="right", no_wrap=True)
        facts.add_column()
        for label, value in entry.facts:
            facts.add_row(f"{label}:", value)
        body.add_row(facts)
    elif entry.definitions:
        definitions = Table.grid(padding=(0, 1))
        definitions.add_column(style="key", justify="right", no_wrap=True)
        definitions.add_column()

        for index, definition in enumerate(entry.definitions, start=1):
            definitions.add_row(f"{index}.", definition)

        body.add_row(Text("Short definition", style="key"))
        body.add_row(definitions)

    if entry.description:
        body.add_row("")
        body.add_row(Text(entry.description_label, style="key"))
        body.add_row(entry.description)

    console.print()
    console.print(
        Panel.fit(
            body,
            title=f"[title]{entry.title}[/]",
            border_style="blue",
            padding=(0, 1),
        )
    )
    console.print(f"[dim]source: {entry.source}[/]")
    console.print()


def display_language(language):
    provider, _, variant = get_language_provider(language)
    source_bytes = fetch_source(provider.build_request(variant))
    entry = provider.parse(source_bytes, variant)
    render_entry(entry)
