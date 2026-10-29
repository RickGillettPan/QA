import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import web_app
from football_monitor import MonitorConfig


CONFIG = MonitorConfig(
    league="premier_league",
    league_code="eng.1",
    league_name="English Premier League",
    team_filter="",
    output_file=Path("unused.csv"),
    request_timeout_seconds=20,
)

SEASON_MATCHES = [
    {
        "event_id": "1",
        "league": "English Premier League",
        "match_date": "2026-10-25T16:30Z",
        "home_team": "Arsenal",
        "home_score": "2",
        "away_team": "Chelsea",
        "away_score": "1",
        "status": "Final",
        "venue": "Emirates Stadium",
        "match_name": "Arsenal vs Chelsea",
    },
    {
        "event_id": "2",
        "league": "English Premier League",
        "match_date": "2026-10-28T19:00Z",
        "home_team": "Liverpool",
        "home_score": "",
        "away_team": "Everton",
        "away_score": "",
        "status": "Scheduled",
        "venue": "Anfield",
        "match_name": "Liverpool vs Everton",
    },
]


class FootballWebTests(unittest.TestCase):
    def setUp(self):
        """Create an isolated Flask test client for each test."""
        self.client = web_app.app.test_client()

    def test_league_table_route_calculates_standings_and_accepts_league_filter(self):
        """Check the table page renders standings for its selected league."""
        with (
            patch.object(web_app, "get_selected_league", return_value=CONFIG),
            patch.object(web_app, "fetch_season_matches", return_value=SEASON_MATCHES),
        ):
            response = self.client.get("/table?league=premier_league")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"League table", response.data)
        self.assertIn(b"Arsenal", response.data)
        self.assertIn(b"Chelsea", response.data)
        self.assertIn(b"Favourite club", response.data)

    def test_results_route_shows_completed_matches_and_team_filter(self):
        """Check results include matching teams and exclude unrelated teams."""
        with (
            patch.object(web_app, "get_selected_league", return_value=CONFIG),
            patch.object(web_app, "fetch_season_matches", return_value=SEASON_MATCHES),
        ):
            response = self.client.get("/results?team=chelsea")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Arsenal", response.data)
        self.assertIn(b"Chelsea", response.data)
        self.assertNotIn(b"Liverpool", response.data)
        self.assertNotIn(b"Anfield", response.data)

    def test_build_team_form_calculates_recent_results_and_season_stats(self):
        """Check recent form and season totals use completed team matches."""
        recent, stats = web_app.build_team_form(SEASON_MATCHES, "Arsenal")

        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["result"], "W")
        self.assertEqual(recent[0]["opponent"], "Chelsea")
        self.assertEqual(recent[0]["venue_role"], "Home")
        self.assertEqual(stats["played"], 1)
        self.assertEqual(stats["points"], 3)
        self.assertEqual(stats["goals_for"], 2)

    def test_team_form_route_renders_selected_team_and_graph(self):
        """Check the team-form page renders a selected club and its results."""
        with (
            patch.object(web_app, "get_selected_league", return_value=CONFIG),
            patch.object(web_app, "fetch_season_matches", return_value=SEASON_MATCHES),
        ):
            response = self.client.get("/form?team=Arsenal")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Team form", response.data)
        self.assertIn(b"Arsenal", response.data)
        self.assertIn(b"Last five results", response.data)
        self.assertIn(b"3 points", response.data)
        self.assertIn(b'data-team-form', response.data)

    def test_team_form_rejects_team_not_in_selected_league(self):
        """Reject a team name that is absent from the selected league feed."""
        with (
            patch.object(web_app, "get_selected_league", return_value=CONFIG),
            patch.object(web_app, "fetch_season_matches", return_value=SEASON_MATCHES),
        ):
            response = self.client.get("/form?team=Imaginary%20FC")

        self.assertEqual(response.status_code, 400)

    def test_dashboard_exposes_shared_league_and_favourite_filter(self):
        """Check dashboard rows expose league and team data for browser filters."""
        matches = [
            {
                "event_id": "1",
                "league": "English Premier League",
                "match_date": "2026-10-25T16:30Z",
                "home_team": "Arsenal",
                "home_score": "2",
                "away_team": "Chelsea",
                "away_score": "1",
                "status": "Final",
                "venue": "Emirates Stadium",
                "match_name": "Arsenal vs Chelsea",
            }
        ]
        with patch.object(
            web_app,
            "get_dashboard_data",
            return_value=(CONFIG, matches, date(2026, 10, 25)),
        ):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-current-league="premier_league"', response.data)
        self.assertIn(b'data-favorite-filter', response.data)
        self.assertIn(b'data-teams="arsenal|chelsea"', response.data)

    def test_dashboard_fetches_selected_calendar_date_and_preserves_filters(self):
        """Check calendar selection is passed to ESPN with the team filter."""
        events = []
        with (
            patch.object(web_app, "load_config", return_value=CONFIG),
            patch.object(web_app, "fetch_scoreboard", return_value=events) as fetch,
        ):
            response = self.client.get(
                "/?league=premier_league&team=Arsenal&date=2026-10-25"
            )

        self.assertEqual(response.status_code, 200)
        fetch.assert_called_once()
        selected_config = fetch.call_args.args[0]
        self.assertEqual(selected_config.team_filter, "Arsenal")
        self.assertEqual(fetch.call_args.kwargs["dates"], "20261025")
        self.assertIn(b"2026-10-25", response.data)
        self.assertIn(b"2026-10-24", response.data)
        self.assertIn(b"2026-10-26", response.data)

    def test_dashboard_rejects_invalid_calendar_date(self):
        """Return a client error for an invalid calendar date."""
        with patch.object(web_app, "load_config", return_value=CONFIG):
            response = self.client.get("/?date=not-a-date")

        self.assertEqual(response.status_code, 400)

    def test_invalid_league_shows_error_instead_of_fetching(self):
        """Reject unsupported leagues before calling the data provider."""
        with patch.object(web_app, "load_config", return_value=CONFIG):
            response = self.client.get("/table?league=not-a-league")

        self.assertEqual(response.status_code, 400)

    def test_dashboard_shows_logged_error_when_scoreboard_is_unavailable(self):
        """Show a safe error banner and log network failures on the dashboard."""
        with (
            patch.object(
                web_app,
                "get_dashboard_data",
                side_effect=TimeoutError("simulated timeout"),
            ),
            patch.object(web_app.LOGGER, "exception") as log_error,
        ):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 502)
        self.assertIn(b"Scoreboard unavailable", response.data)
        self.assertIn(b"Please try again", response.data)
        log_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
