import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import football_monitor as monitor


SCOREBOARD = [
    {
        "id": "1001",
        "name": "Arsenal vs Chelsea",
        "date": "2026-10-28T19:00Z",
        "status": {"type": {"detail": "Scheduled"}},
        "competitions": [
            {
                "competitors": [
                    {
                        "homeAway": "home",
                        "team": {"displayName": "Arsenal"},
                        "score": "",
                    },
                    {
                        "homeAway": "away",
                        "team": {"displayName": "Chelsea"},
                        "score": "",
                    },
                ],
                "venue": {"fullName": "Emirates Stadium"},
            }
        ],
    },
    {
        "id": "1002",
        "name": "Liverpool vs Everton",
        "date": "2026-10-29T20:00Z",
        "status": {"type": {"detail": "Final"}},
        "competitions": [
            {
                "competitors": [
                    {
                        "homeAway": "home",
                        "team": {"displayName": "Liverpool"},
                        "score": "2",
                    },
                    {
                        "homeAway": "away",
                        "team": {"displayName": "Everton"},
                        "score": "1",
                    },
                ]
            }
        ],
    },
]


class FootballMonitorTests(unittest.TestCase):
    def test_config_loads_league_filter_and_output(self):
        """Check valid JSON options are converted into normalized settings."""
        config_data = {
            "league": "scottish_premiership",
            "team_filter": "Celtic",
            "output_file": "reports/weekly.csv",
            "request_timeout_seconds": 12,
        }
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")
            config = monitor.load_config(config_path)

        self.assertEqual(config.league_code, "sco.1")
        self.assertEqual(config.league_name, "Scottish Premiership")
        self.assertEqual(config.team_filter, "Celtic")
        self.assertEqual(config.request_timeout_seconds, 12)

    def test_process_events_filters_for_either_team(self):
        """Check that a partial team name matches either side of a fixture."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="eng.1",
            league_name="English Premier League",
            team_filter="chel",
            output_file=Path("unused.csv"),
            request_timeout_seconds=20,
        )

        matches = monitor.process_events(SCOREBOARD, config)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["home_team"], "Arsenal")
        self.assertEqual(matches[0]["away_team"], "Chelsea")
        self.assertEqual(matches[0]["status"], "Scheduled")

    def test_report_contains_headers_and_fixture_result_data(self):
        """Check reports include fixture fields and create missing folders."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="eng.1",
            league_name="English Premier League",
            team_filter="",
            output_file=Path("unused.csv"),
            request_timeout_seconds=20,
        )
        matches = monitor.process_events(SCOREBOARD, config)

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "reports" / "matches.csv"
            monitor.write_report(matches, report_path)
            with report_path.open(encoding="utf-8-sig", newline="") as report_file:
                rows = list(csv.DictReader(report_file))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["home_score"], "2")
        self.assertEqual(rows[1]["away_score"], "1")
        self.assertEqual(rows[0]["venue"], "Emirates Stadium")

    def test_fetch_uses_selected_league_endpoint_and_parses_events(self):
        """Check the selected league code is used for the ESPN request."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="eng.1",
            league_name="English Premier League",
            team_filter="",
            output_file=Path("unused.csv"),
            request_timeout_seconds=20,
        )
        response = type(
            "Response",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, *args: None,
                "read": lambda self: json.dumps({"events": SCOREBOARD}).encode(),
            },
        )()

        with patch.object(monitor, "urlopen", return_value=response) as urlopen_mock:
            events = monitor.fetch_scoreboard(config)

        self.assertEqual(len(events), 2)
        self.assertIn("eng.1/scoreboard", urlopen_mock.call_args.args[0].full_url)

    def test_scoreboard_response_is_cached_for_repeated_page_requests(self):
        """Check repeated identical requests reuse a successful cached response."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="test-cache-league",
            league_name="Test League",
            team_filter="",
            output_file=Path("unused.csv"),
            request_timeout_seconds=20,
        )
        response = type(
            "Response",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, *args: None,
                "read": lambda self: json.dumps({"events": SCOREBOARD}).encode(),
            },
        )()
        monitor._scoreboard_cache.pop((config.league_code, None), None)

        with patch.object(monitor, "urlopen", return_value=response) as urlopen_mock:
            first = monitor.fetch_scoreboard(config)
            second = monitor.fetch_scoreboard(config)

        self.assertEqual(first, second)
        urlopen_mock.assert_called_once()

    def test_run_logs_required_success_events(self):
        """Check success logs cover startup, league, processed count, and output."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="eng.1",
            league_name="English Premier League",
            team_filter="",
            output_file=Path("test-report.csv"),
            request_timeout_seconds=20,
        )
        with (
            patch.object(monitor, "fetch_scoreboard", return_value=SCOREBOARD),
            patch.object(monitor, "process_events", return_value=[{"event_id": "1"}]),
            patch.object(monitor, "write_report") as write_report,
            self.assertLogs(monitor.LOGGER, level="INFO") as logs,
        ):
            result = monitor.run(config)

        self.assertEqual(result, 0)
        write_report.assert_called_once()
        messages = "\n".join(logs.output)
        self.assertIn("Script started", messages)
        self.assertIn("League selected: English Premier League", messages)
        self.assertIn("Number of matches processed: 1", messages)
        self.assertIn("Output file created: test-report.csv", messages)

    def test_run_logs_errors_when_api_fetch_fails(self):
        """Check a failed operation is recorded with its error traceback."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="eng.1",
            league_name="English Premier League",
            team_filter="",
            output_file=Path("unused.csv"),
            request_timeout_seconds=20,
        )
        with (
            patch.object(monitor, "fetch_scoreboard", side_effect=TimeoutError("timeout")),
            self.assertLogs(monitor.LOGGER, level="ERROR") as logs,
            patch("sys.stderr"),
        ):
            result = monitor.run(config)

        self.assertEqual(result, 1)
        self.assertIn("Error encountered while running", logs.output[0])
        self.assertTrue(any("TimeoutError: timeout" in line for line in logs.output))

    def test_calculate_standings_orders_points_and_goal_difference(self):
        """Check completed scores produce correctly ranked 3/1/0 standings."""
        matches = [
            {
                "status": "Final",
                "home_team": "Arsenal",
                "home_score": "2",
                "away_team": "Chelsea",
                "away_score": "0",
            },
            {
                "status": "Final",
                "home_team": "Chelsea",
                "home_score": "3",
                "away_team": "Liverpool",
                "away_score": "0",
            },
            {
                "status": "Final",
                "home_team": "Arsenal",
                "home_score": "1",
                "away_team": "Liverpool",
                "away_score": "1",
            },
            {
                "status": "Scheduled",
                "home_team": "Liverpool",
                "home_score": "",
                "away_team": "Arsenal",
                "away_score": "",
            },
        ]

        table = monitor.calculate_standings(matches)

        self.assertEqual([row["team"] for row in table], ["Arsenal", "Chelsea", "Liverpool"])
        self.assertEqual(table[0]["points"], 4)
        self.assertEqual(table[0]["gd"], 2)
        self.assertEqual(table[2]["played"], 2)

    def test_fetch_season_matches_uses_year_and_excludes_future_dates(self):
        """Check season fetch parameters and cutoff-date filtering."""
        config = monitor.MonitorConfig(
            league="premier_league",
            league_code="eng.1",
            league_name="English Premier League",
            team_filter="",
            output_file=Path("unused.csv"),
            request_timeout_seconds=20,
        )
        response = type(
            "Response",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, *args: None,
                "read": lambda self: json.dumps({"events": SCOREBOARD}).encode(),
            },
        )()

        with patch.object(monitor, "urlopen", return_value=response) as urlopen_mock:
            matches = monitor.fetch_season_matches(config, through_date=date(2026, 10, 28))

        self.assertTrue(urlopen_mock.call_args.args[0].full_url.endswith("dates=2026&limit=1000"))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["home_team"], "Arsenal")


if __name__ == "__main__":
    unittest.main()
