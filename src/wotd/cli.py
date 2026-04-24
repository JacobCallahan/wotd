import rich_click as click

from .core import (
    DEFAULT_LANGUAGE,
    WOTDError,
    console,
    display_language,
    get_registered_language_codes,
)

AVAILABLE_LANGUAGE_CODES = get_registered_language_codes()
LANGUAGE_METAVAR = (
    f"[{'|'.join(AVAILABLE_LANGUAGE_CODES)}]" if AVAILABLE_LANGUAGE_CODES else "[LANGUAGE]"
)
LANGUAGE_EPILOG = (
    f"Available languages: {', '.join(AVAILABLE_LANGUAGE_CODES)}. Default: {DEFAULT_LANGUAGE}."
    if AVAILABLE_LANGUAGE_CODES
    else f"Default language: {DEFAULT_LANGUAGE}."
)


@click.command(epilog=LANGUAGE_EPILOG)
@click.argument("language", required=False, default=DEFAULT_LANGUAGE, metavar=LANGUAGE_METAVAR)
def main(language):
    """Display the newest Word of the Day and its definition(s).

    Language variants can be exposed by providers, such as `ja-n3`.
    """
    try:
        display_language(language)
    except WOTDError as exc:
        console.print(f"[error]Error:[/] {exc}")
        raise SystemExit(1)
