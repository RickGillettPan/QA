import argparse
import json
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from logging_config import get_logger


API_URL = "https://api.tvmaze.com/search/shows"
CONFIG_PATH = Path(__file__).with_name("config.json")
logger = get_logger()


@dataclass(frozen=True)
class SearchConfig:
    search_term: str
    minimum_rating: float
    genre: str | None


def load_config() -> SearchConfig:
    try:
        with CONFIG_PATH.open(encoding="utf-8") as config_file:
            data = json.load(config_file)
    except OSError as error:
        raise ValueError(f"Could not read configuration file {CONFIG_PATH}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Configuration file {CONFIG_PATH} is not valid JSON: {error}") from error

    if not isinstance(data, dict):
        raise ValueError("Configuration must be a JSON object.")

    search_term = data.get("search_term")
    if not isinstance(search_term, str) or not search_term.strip():
        raise ValueError("'search_term' must be a non-empty string.")

    minimum_rating = data.get("minimum_rating")
    if (
        not isinstance(minimum_rating, (int, float))
        or isinstance(minimum_rating, bool)
        or not 0 <= minimum_rating <= 10
    ):
        raise ValueError("'minimum_rating' must be a number from 0 to 10.")

    genre = data.get("genre")
    if genre is not None and (not isinstance(genre, str) or not genre.strip()):
        raise ValueError("'genre' must be a non-empty string when provided.")

    return SearchConfig(
        search_term.strip(),
        float(minimum_rating),
        genre.strip() if isinstance(genre, str) else None,
    )


@dataclass(frozen=True)
class TVShow:
    name: str
    genres: tuple[str, ...]
    rating: float | None
    premiered: str | None = None
    status: str | None = None
    summary: str = ""
    image_url: str | None = None
    official_url: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, object]) -> "TVShow":
        name = data.get("name")
        if not isinstance(name, str):
            raise ValueError("A TVMaze show is missing its name.")

        raw_genres = data.get("genres")
        genres = (
            tuple(genre for genre in raw_genres if isinstance(genre, str))
            if isinstance(raw_genres, list)
            else ()
        )

        raw_rating = data.get("rating")
        average = raw_rating.get("average") if isinstance(raw_rating, dict) else None
        rating = (
            float(average)
            if isinstance(average, (int, float)) and not isinstance(average, bool)
            else None
        )

        raw_image = data.get("image")
        image_url = raw_image.get("medium") if isinstance(raw_image, dict) else None
        official_url = data.get("officialSite")
        premiered = data.get("premiered")
        status = data.get("status")
        raw_summary = data.get("summary")

        return cls(
            name=name,
            genres=genres,
            rating=rating,
            premiered=premiered if isinstance(premiered, str) else None,
            status=status if isinstance(status, str) else None,
            summary=_plain_text(raw_summary) if isinstance(raw_summary, str) else "",
            image_url=image_url if isinstance(image_url, str) else None,
            official_url=official_url if isinstance(official_url, str) else None,
        )


class _SummaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def _plain_text(summary: str) -> str:
    parser = _SummaryParser()
    parser.feed(summary)
    return " ".join(parser.parts)


def search_shows(
    query: str | None = None,
    minimum_rating: float | None = None,
    include_unrated: bool = False,
    genre: str | None = None,
) -> list[TVShow]:
    config = load_config()
    query = query.strip() if query is not None else config.search_term
    if not query:
        raise ValueError("Search term must not be empty.")
    if minimum_rating is None:
        minimum_rating = config.minimum_rating
    if genre is None:
        genre = config.genre

    url = f"{API_URL}?{urlencode({'q': query})}"
    with urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("TVMaze returned an unexpected response format.")

    shows = []
    for result in payload:
        if not isinstance(result, dict) or not isinstance(result.get("show"), dict):
            raise ValueError("TVMaze returned a malformed search result.")
        shows.append(TVShow.from_api(result["show"]))

    return [
        show for show in shows
        if (
            (genre is None or any(item.casefold() == genre.casefold() for item in show.genres))
            and (
                (show.rating is None and include_unrated)
                or (show.rating is not None and show.rating >= minimum_rating)
            )
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Search TVMaze for TV shows.")
    parser.add_argument(
        "query", nargs="?", help="Show title to search for (defaults to config.json)"
    )
    parser.add_argument(
        "--minimum-rating",
        type=float,
        help="Minimum rating from 0 to 10 (defaults to config.json)",
    )
    args = parser.parse_args()

    try:
        config = load_config()
        query = args.query if args.query is not None else config.search_term
        minimum_rating = (
            args.minimum_rating
            if args.minimum_rating is not None
            else config.minimum_rating
        )
        if not 0 <= minimum_rating <= 10:
            raise ValueError("Minimum rating must be a number from 0 to 10.")
        shows = search_shows(query, minimum_rating)
        logger.info("CLI search completed; returned %d results", len(shows))
    except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
        logger.exception("CLI search failed")
        print(f"TVMaze search failed: {error}", file=sys.stderr)
        return 1

    if not shows:
        print(f"No shows found for {query!r} with a rating of at least {minimum_rating:g}.")
        return 0

    for show in shows:
        genres = ", ".join(show.genres) or "Not listed"
        rating = f"{show.rating:.1f}/10" if show.rating is not None else "Not rated"
        print(f"Name: {show.name}")
        print(f"Genres: {genres}")
        print(f"Rating: {rating}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
