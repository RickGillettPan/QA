from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, abort, render_template, request, send_file

from football_monitor import (
    LEAGUES,
    LOGGER,
    MonitorConfig,
    OPERATION_ERRORS,
    calculate_standings,
    fetch_scoreboard,
    fetch_season_matches,
    load_config,
    process_events,
    write_report,
)


app = Flask(__name__)


def get_dashboard_data() -> tuple[MonitorConfig, list[dict[str, str]], date]:
    """Resolve dashboard filters and fetch only the requested calendar day."""
    config = load_config()
    league = request.args.get("league", config.league)
    if league not in LEAGUES:
        abort(400, description="Select a supported league.")

    team_filter = request.args.get("team", config.team_filter).strip()
    selected_date_text = request.args.get("date", date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_text)
    except ValueError:
        abort(400, description="Choose a valid calendar date.")

    selected_config = replace(
        config,
        league=league,
        league_code=LEAGUES[league][0],
        league_name=LEAGUES[league][1],
        team_filter=team_filter,
    )
    events = fetch_scoreboard(selected_config, dates=selected_date.strftime("%Y%m%d"))
    matches = process_events(events, selected_config)
    LOGGER.info(
        "Dashboard refreshed: league=%s date=%s team_filter=%r fetched=%d matched=%d",
        selected_config.league_name,
        selected_date.isoformat(),
        selected_config.team_filter,
        len(events),
        len(matches),
    )
    return selected_config, matches, selected_date


def get_selected_league() -> MonitorConfig:
    """Apply a page's league override, falling back to the configured default."""
    config = load_config()
    league = request.args.get("league", config.league)
    if league not in LEAGUES:
        abort(400, description="Select a supported league.")
    return replace(
        config,
        league=league,
        league_code=LEAGUES[league][0],
        league_name=LEAGUES[league][1],
        team_filter="",
    )


def summarize_matches(matches: list[dict[str, str]]) -> dict[str, int]:
    """Count live, completed, and scheduled matches for the dashboard cards."""
    live = sum(match["status"].casefold() == "live" for match in matches)
    completed = sum(match["status"].casefold() == "final" for match in matches)
    scheduled = sum(match["status"].casefold() == "scheduled" for match in matches)
    return {
        "total": len(matches),
        "live": live,
        "completed": completed,
        "scheduled": scheduled,
    }


def build_team_form(
    matches: list[dict[str, str]],
    team_name: str,
) -> tuple[list[dict[str, object]], dict[str, int]]:
    """Return the team's five newest results and season-to-date statistics."""
    team_key = team_name.casefold()
    team_matches = []
    for match in matches:
        if match["status"].casefold() != "final":
            continue
        is_home = match["home_team"].casefold() == team_key
        is_away = match["away_team"].casefold() == team_key
        if not is_home and not is_away:
            continue
        try:
            team_score = int(match["home_score"] if is_home else match["away_score"])
            opponent_score = int(match["away_score"] if is_home else match["home_score"])
        except ValueError:
            continue

        result = "W" if team_score > opponent_score else (
            "D" if team_score == opponent_score else "L"
        )
        team_matches.append(
            {
                **match,
                "result": result,
                "team_score": team_score,
                "opponent_score": opponent_score,
                "opponent": match["away_team"] if is_home else match["home_team"],
                "venue_role": "Home" if is_home else "Away",
                "points": 3 if result == "W" else 1 if result == "D" else 0,
            }
        )

    # Keep full-season totals separate from the five-result visual form strip.
    team_matches.sort(key=lambda match: str(match["match_date"]), reverse=True)
    stats = {
        "played": len(team_matches),
        "won": sum(match["result"] == "W" for match in team_matches),
        "drawn": sum(match["result"] == "D" for match in team_matches),
        "lost": sum(match["result"] == "L" for match in team_matches),
        "points": sum(int(match["points"]) for match in team_matches),
        "goals_for": sum(int(match["team_score"]) for match in team_matches),
        "goals_against": sum(int(match["opponent_score"]) for match in team_matches),
    }
    return team_matches[:5], stats


def calendar_days(selected_date: date) -> list[dict[str, object]]:
    """Build the seven-day navigation strip centered on the selected date."""
    today = date.today()
    days = []
    for offset in range(-3, 4):
        day = selected_date + timedelta(days=offset)
        days.append(
            {
                "date": day.isoformat(),
                "weekday": day.strftime("%a"),
                "day": day.day,
                "is_selected": day == selected_date,
                "is_today": day == today,
            }
        )
    return days


def dashboard_error(error: Exception) -> tuple[str, int]:
    """Log a page failure and choose a safe, user-facing message and status."""
    LOGGER.exception("Dashboard request failed")
    if isinstance(error, ValueError):
        message = str(error)
    else:
        message = "The ESPN scoreboard is unavailable right now. Please try again."
    return message, 502


def render_error_page(
    template_name: str,
    error: Exception,
    **template_context: object,
) -> tuple[str, int]:
    """Render a page's normal error state without repeating route boilerplate."""
    message, status = dashboard_error(error)
    try:
        config = get_selected_league()
    except ValueError:
        LOGGER.exception("Could not load configuration while rendering an error page")
        config = None

    return (
        render_template(
            template_name,
            config=config,
            leagues=LEAGUES,
            error_message=message,
            **template_context,
        ),
        status,
    )


@app.get("/")
def index():
    """Show fixtures for the selected league, team filter, and calendar date."""
    try:
        config, matches, selected_date = get_dashboard_data()
    except OPERATION_ERRORS as error:
        selected_date = date.today()
        return render_error_page(
            "index.html",
            error,
            matches=[],
            summary=summarize_matches([]),
            team_filter=request.args.get("team", ""),
            selected_date=selected_date,
            calendar_days=calendar_days(selected_date),
            today=selected_date,
            previous_date=selected_date - timedelta(days=1),
            next_date=selected_date + timedelta(days=1),
        )

    return render_template(
        "index.html",
        config=config,
        leagues=LEAGUES,
        matches=matches,
        summary=summarize_matches(matches),
        error_message="",
        team_filter=config.team_filter,
        selected_date=selected_date,
        calendar_days=calendar_days(selected_date),
        today=date.today(),
        previous_date=selected_date - timedelta(days=1),
        next_date=selected_date + timedelta(days=1),
    )


@app.get("/table")
def league_table():
    """Calculate and display standings for the selected competition."""
    try:
        config = get_selected_league()
        season_matches = fetch_season_matches(config)
        table = calculate_standings(season_matches)
    except OPERATION_ERRORS as error:
        return render_error_page("league_table.html", error, table=[])

    LOGGER.info(
        "League table calculated: league=%s teams=%d",
        config.league_name,
        len(table),
    )
    return render_template(
        "league_table.html",
        config=config,
        leagues=LEAGUES,
        table=table,
        error_message="",
    )


@app.get("/results")
def results():
    """Show current-season completed and live matches with optional filters."""
    try:
        config = get_selected_league()
        season_matches = fetch_season_matches(config)
        matches = [
            match for match in season_matches
            if match["status"].casefold() in {"final", "live"}
        ]
        team_filter = request.args.get("team", "").strip()
        if team_filter:
            term = team_filter.casefold()
            matches = [
                match for match in matches
                if term in match["home_team"].casefold()
                or term in match["away_team"].casefold()
            ]
        matches.sort(key=lambda match: match["match_date"], reverse=True)
    except OPERATION_ERRORS as error:
        return render_error_page(
            "results.html",
            error,
            matches=[],
            team_filter=request.args.get("team", ""),
        )

    LOGGER.info(
        "Results page loaded: league=%s matches=%d team_filter=%r",
        config.league_name,
        len(matches),
        team_filter,
    )
    return render_template(
        "results.html",
        config=config,
        leagues=LEAGUES,
        matches=matches,
        error_message="",
        team_filter=team_filter,
    )


@app.get("/form")
def team_form():
    """Display a selected club's recent results and season statistics."""
    try:
        config = get_selected_league()
        season_matches = fetch_season_matches(config)
        team_names = sorted(
            {
                name
                for match in season_matches
                for name in (match["home_team"], match["away_team"])
            },
            key=str.casefold,
        )
        selected_team = request.args.get("team", "").strip()
        if selected_team and selected_team.casefold() not in {
            name.casefold() for name in team_names
        }:
            abort(400, description="Choose a team from the selected league.")

        recent_matches: list[dict[str, object]] = []
        stats = {
            "played": 0, "won": 0, "drawn": 0, "lost": 0,
            "points": 0, "goals_for": 0, "goals_against": 0,
        }
        if selected_team:
            selected_team = next(
                name for name in team_names
                if name.casefold() == selected_team.casefold()
            )
            recent_matches, stats = build_team_form(season_matches, selected_team)
    except OPERATION_ERRORS as error:
        return render_error_page(
            "team_form.html",
            error,
            team_names=[],
            selected_team="",
            recent_matches=[],
            stats={},
        )

    LOGGER.info(
        "Team form loaded: league=%s team=%r matches=%d",
        config.league_name,
        selected_team,
        stats["played"],
    )
    return render_template(
        "team_form.html",
        config=config,
        leagues=LEAGUES,
        team_names=team_names,
        selected_team=selected_team,
        recent_matches=recent_matches,
        stats=stats,
        error_message="",
    )


@app.get("/download")
def download():
    """Generate and return a CSV report for the selected matchday filters."""
    try:
        config, matches, _selected_date = get_dashboard_data()
        write_report(matches, config.output_file)
    except OPERATION_ERRORS as error:
        message, status = dashboard_error(error)
        return message, status

    return send_file(
        config.output_file,
        as_attachment=True,
        download_name=Path(config.output_file).name,
        mimetype="text/csv",
    )


if __name__ == "__main__":
    app.run(debug=False)
