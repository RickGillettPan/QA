import argparse
import csv
import json
import logging
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LOG_PATH = BASE_DIR / "automation.log"

LEAGUES = {
    "premier_league": ("eng.1", "English Premier League"),
    "scottish_premiership": ("sco.1", "Scottish Premiership"),
    "bundesliga": ("ger.1", "German Bundesliga"),
    "ligue_1": ("fra.1", "French Ligue 1"),
}

REPORT_FIELDS = [
    "event_id",
    "league",
    "match_date",
    "home_team",
    "home_score",
    "away_team",
    "away_score",
    "status",
    "venue",
    "match_name",
]
OPERATION_ERRORS = (
    URLError,
    TimeoutError,
    OSError,
    UnicodeDecodeError,
    json.JSONDecodeError,
    ValueError,
)
SEASON_CACHE_SECONDS = 300
MAX_SCOREBOARD_CACHE_ENTRIES = 64
_scoreboard_cache: dict[
    tuple[str, str | None],
    tuple[float, tuple[dict[str, object], ...]],
] = {}
_scoreboard_cache_lock = threading.Lock()


def configure_logging() -> logging.Logger:
    """Create the shared UTF-8 file logger used by the CLI and web app."""
    logger = logging.getLogger("football_monitor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.propagate = False
    return logger


LOGGER = configure_logging()


@dataclass(frozen=True)
class MonitorConfig:
    """Validated settings shared by the API client, report writer, and website."""

    league: str
    league_code: str
    league_name: str
    team_filter: str
    output_file: Path
    request_timeout_seconds: int


def load_config(path: Path = CONFIG_PATH) -> MonitorConfig:
    """Load and validate runtime options without relying on the shell's cwd."""
    try:
        with path.open(encoding="utf-8") as config_file:
            data = json.load(config_file)
    except OSError as error:
        raise ValueError(f"Cannot read config file {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Config file {path} is not valid JSON: {error}") from error

    if not isinstance(data, dict):
        raise ValueError("Config must contain a JSON object.")

    league = data.get("league")
    if not isinstance(league, str) or league not in LEAGUES:
        choices = ", ".join(LEAGUES)
        raise ValueError(f"'league' must be one of: {choices}.")

    team_filter = data.get("team_filter", "")
    if not isinstance(team_filter, str):
        raise ValueError("'team_filter' must be a string.")

    output_file = data.get("output_file")
    if not isinstance(output_file, str) or not output_file.strip():
        raise ValueError("'output_file' must be a non-empty path.")
    output_path = Path(output_file.strip())
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path

    timeout = data.get("request_timeout_seconds", 20)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError("'request_timeout_seconds' must be a positive integer.")

    league_code, league_name = LEAGUES[league]
    return MonitorConfig(
        league=league,
        league_code=league_code,
        league_name=league_name,
        team_filter=team_filter.strip(),
        output_file=output_path,
        request_timeout_seconds=timeout,
    )


def fetch_scoreboard(
    config: MonitorConfig,
    dates: str | None = None,
) -> list[dict[str, object]]:
    """Fetch ESPN events, reusing a short-lived response for identical queries."""
    cache_key = (config.league_code, dates)
    now = time.monotonic()
    with _scoreboard_cache_lock:
        cached = _scoreboard_cache.get(cache_key)
        if cached and now - cached[0] < SEASON_CACHE_SECONDS:
            return list(cached[1])
        if cached:
            _scoreboard_cache.pop(cache_key, None)

    url = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer/"
        f"{config.league_code}/scoreboard"
    )
    if dates is not None:
        url = f"{url}?{urlencode({'dates': dates, 'limit': 1000})}"
    request = Request(url, headers={"User-Agent": "FootballMatchMonitor/1.0"})
    with urlopen(request, timeout=config.request_timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError("ESPN returned an unexpected scoreboard response.")
    events = payload["events"]
    if any(not isinstance(event, dict) for event in events):
        raise ValueError("ESPN returned a malformed event in its scoreboard.")
    # Keep successful responses briefly so page navigation doesn't repeatedly
    # download the same season's large scoreboard payload.
    with _scoreboard_cache_lock:
        expired_keys = [
            key
            for key, (created_at, _events) in _scoreboard_cache.items()
            if time.monotonic() - created_at >= SEASON_CACHE_SECONDS
        ]
        for key in expired_keys:
            _scoreboard_cache.pop(key, None)
        if len(_scoreboard_cache) >= MAX_SCOREBOARD_CACHE_ENTRIES:
            oldest_key = min(
                _scoreboard_cache,
                key=lambda key: _scoreboard_cache[key][0],
            )
            _scoreboard_cache.pop(oldest_key)
        _scoreboard_cache[cache_key] = (time.monotonic(), tuple(events))
    return events


def _text(value: object, default: str = "") -> str:
    """Return a trimmed string field or its fallback for malformed API data."""
    return value.strip() if isinstance(value, str) else default


def extract_match(event: dict[str, object], league_name: str) -> dict[str, str]:
    """Flatten ESPN's nested event/competition/team JSON into report fields."""
    competitions = event.get("competitions")
    if not isinstance(competitions, list) or not competitions:
        raise ValueError("Scoreboard event is missing its competition data.")
    competition = competitions[0]
    if not isinstance(competition, dict):
        raise ValueError("Scoreboard event has malformed competition data.")

    competitors = competition.get("competitors")
    if not isinstance(competitors, list):
        raise ValueError("Scoreboard competition is missing its teams.")

    teams: dict[str, dict[str, object]] = {}
    for competitor in competitors:
        if not isinstance(competitor, dict):
            continue
        home_away = competitor.get("homeAway")
        team = competitor.get("team")
        if home_away in {"home", "away"} and isinstance(team, dict):
            teams[home_away] = {**competitor, "team": team}

    if "home" not in teams or "away" not in teams:
        raise ValueError("Scoreboard event must have a home and away team.")

    home = teams["home"]
    away = teams["away"]
    home_team = home["team"]
    away_team = away["team"]
    if not isinstance(home_team, dict) or not isinstance(away_team, dict):
        raise ValueError("Scoreboard event contains malformed team details.")

    status_text = "Scheduled"
    status = event.get("status")
    if isinstance(status, dict):
        status_type = status.get("type")
        if isinstance(status_type, dict):
            state = _text(status_type.get("state")).casefold()
            if status_type.get("completed") is True or state == "post":
                status_text = "Final"
            elif state == "in":
                status_text = "Live"
            elif state == "pre":
                status_text = "Scheduled"
            else:
                status_text = (
                    _text(status_type.get("description"))
                    or _text(status_type.get("detail"))
                    or status_text
                )

    venue_name = ""
    venue = competition.get("venue")
    if isinstance(venue, dict):
        venue_name = _text(venue.get("fullName"))

    event_id = event.get("id")
    return {
        "event_id": str(event_id) if event_id is not None else "",
        "league": league_name,
        "match_date": _text(event.get("date")),
        "home_team": _text(home_team.get("displayName"), "Unknown"),
        "home_score": _text(home.get("score")),
        "away_team": _text(away_team.get("displayName"), "Unknown"),
        "away_score": _text(away.get("score")),
        "status": status_text,
        "venue": venue_name,
        "match_name": _text(event.get("name")),
    }


def process_events(
    events: list[dict[str, object]],
    config: MonitorConfig,
) -> list[dict[str, str]]:
    """Convert events once, then apply the optional case-insensitive team filter."""
    matches = [extract_match(event, config.league_name) for event in events]
    if config.team_filter:
        filter_text = config.team_filter.casefold()
        matches = [
            match
            for match in matches
            if filter_text in match["home_team"].casefold()
            or filter_text in match["away_team"].casefold()
        ]
    return matches


def fetch_season_matches(
    config: MonitorConfig,
    through_date: date | None = None,
) -> list[dict[str, str]]:
    """Load this season's ESPN feed and discard dates outside the current season."""
    cutoff = through_date or date.today()
    season_year = cutoff.year if cutoff.month >= 8 else cutoff.year - 1
    season_start = date(season_year, 8, 1)
    events = fetch_scoreboard(config, dates=str(season_year))
    matches = process_events(events, config)
    return [
        match
        for match in matches
        if match["match_date"][:10]
        and season_start.isoformat() <= match["match_date"][:10] <= cutoff.isoformat()
    ]


def calculate_standings(matches: list[dict[str, str]]) -> list[dict[str, object]]:
    """Calculate standard 3/1/0 standings from completed matches only."""
    table: dict[str, dict[str, object]] = {}
    for match in matches:
        if match["status"].casefold() != "final":
            continue
        try:
            home_score = int(match["home_score"])
            away_score = int(match["away_score"])
        except ValueError:
            continue

        home_name = match["home_team"]
        away_name = match["away_team"]
        home = table.setdefault(home_name, _new_standing_row(home_name))
        away = table.setdefault(away_name, _new_standing_row(away_name))

        home["played"] = int(home["played"]) + 1
        away["played"] = int(away["played"]) + 1
        home["gf"] = int(home["gf"]) + home_score
        home["ga"] = int(home["ga"]) + away_score
        away["gf"] = int(away["gf"]) + away_score
        away["ga"] = int(away["ga"]) + home_score

        if home_score > away_score:
            home["won"] = int(home["won"]) + 1
            away["lost"] = int(away["lost"]) + 1
            home["points"] = int(home["points"]) + 3
        elif away_score > home_score:
            away["won"] = int(away["won"]) + 1
            home["lost"] = int(home["lost"]) + 1
            away["points"] = int(away["points"]) + 3
        else:
            home["drawn"] = int(home["drawn"]) + 1
            away["drawn"] = int(away["drawn"]) + 1
            home["points"] = int(home["points"]) + 1
            away["points"] = int(away["points"]) + 1

    for row in table.values():
        row["gd"] = int(row["gf"]) - int(row["ga"])

    # Apply the standard table tie-break order after all match totals are known.
    return sorted(
        table.values(),
        key=lambda row: (
            -int(row["points"]),
            -int(row["gd"]),
            -int(row["gf"]),
            str(row["team"]).casefold(),
        ),
    )


def _new_standing_row(team_name: str) -> dict[str, object]:
    """Create a zeroed standings record for a team not seen yet."""
    return {
        "team": team_name,
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "points": 0,
    }


def write_report(matches: list[dict[str, str]], output_file: Path) -> None:
    """Write all filtered matches to a UTF-8 CSV, creating parent folders."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8-sig") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(matches)


def run(config: MonitorConfig) -> int:
    """Run one fetch-filter-report cycle and return a process exit code."""
    LOGGER.info("Script started")
    LOGGER.info("League selected: %s", config.league_name)
    try:
        events = fetch_scoreboard(config)
        matches = process_events(events, config)
        LOGGER.info("Number of matches processed: %d", len(matches))
        write_report(matches, config.output_file)
    except OPERATION_ERRORS:
        LOGGER.exception("Error encountered while running the football monitor")
        print(
            f"Football monitor failed. See {LOG_PATH} for details.",
            file=sys.stderr,
        )
        return 1

    LOGGER.info("Output file created: %s", config.output_file)
    print(f"Report created: {config.output_file} ({len(matches)} matches)")
    return 0


def main() -> int:
    """Parse command-line options, validate configuration, and run the monitor."""
    parser = argparse.ArgumentParser(
        description="Retrieve ESPN football fixtures/results and create a CSV report."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to JSON configuration file (default: config.json beside this script)",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ValueError:
        LOGGER.exception("Error encountered while loading configuration")
        print(f"Could not load config. See {LOG_PATH} for details.", file=sys.stderr)
        return 2
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
