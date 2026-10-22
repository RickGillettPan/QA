"""Search a list of TV shows and report whether a title matches."""

TV_SHOWS = ("Doctor Who", "Sherlock", "Luther")


def search_shows(search_term: str, shows: tuple[str, ...]) -> bool:
    """Return whether any show title contains the search term, ignoring case."""
    # casefold() handles more international letter case variants than lower().
    normalized_term = search_term.strip().casefold()
    return bool(normalized_term) and any(
        normalized_term in show_title.casefold() for show_title in shows
    )


def display_search_result(search_term: str, shows: tuple[str, ...]) -> None:
    """Print whether the search term matches a show title."""
    cleaned_term = search_term.strip()
    if not cleaned_term:
        print("Please enter a search term.")
    elif search_shows(cleaned_term, shows):
        print(f"Found: {cleaned_term}")
    else:
        print(f"Not found: {cleaned_term}")


def main():
    """Prompt for a search term, show the result, and wait before closing."""
    search_term = input("Enter a search term: ")
    display_search_result(search_term, TV_SHOWS)
    try:
        input("Press Enter to close.")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
