# Automation Definition Worksheet — Football Match Monitor

## Purpose

Automate the retrieval of football fixtures and results for a selected league,
apply a team filter, and create a shareable match report for the sports media
team and downstream systems.

## Inputs

| Input | Source | Example / validation |
|---|---|---|
| League | `config.json` | `premier_league`, `scottish_premiership`, `bundesliga`, or `ligue_1` |
| Team filter | `config.json` | Optional, case-insensitive partial team-name match; blank means all teams |
| Output file | `config.json` | CSV path; relative paths are resolved from this project folder |
| Request timeout | `config.json` | Positive integer seconds; defaults to 20 if omitted |

## Processing

1. Load and validate the JSON configuration.
2. Select the corresponding ESPN soccer scoreboard endpoint.
3. Request the current league scoreboard and parse its JSON response.
4. Extract event ID, date, league, home/away names and scores, status, venue,
   and match name.
5. Keep all events if the team filter is blank; otherwise keep events where
   either home or away team contains the configured team text.
6. For the website, retrieve current-season scoreboard events through the
   current date, display completed/live results, and calculate league standings
   from completed scores using three points for a win and one for a draw.
7. Let the user navigate fixture dates with a date picker, a seven-day strip,
   or previous/next-day controls. Retain the selected league and team filter.
8. Calculate the selected team's season totals and latest five completed
   results for a graphical form view.
9. Write matching records to a UTF-8 CSV report with a header row. The report
   is written even when no events match, so downstream consumers receive a
   valid empty report.
10. Allow a user to save a favourite club in browser storage, highlight its
    fixtures/results, and filter match and standings views to that club.
11. Cache identical ESPN scoreboard requests in memory for up to five minutes
   to reduce repeated network calls while navigating the site.
12. Record the script start, selected league, number of matches processed,
    output file created, and any errors in `automation.log`.

## Outputs

- **Match report:** configured CSV output path; one row per matching event.
- **Website:** calendar-based match centre, current-season results, calculated
  league table, and graphical team-form view.
- **Favourite team:** browser-local setting used to filter team views.
- **Log file:** `automation.log`, containing timestamps, script start, selected
  league, processed match count, output file path, and error tracebacks.

## Dependencies and assumptions

- Python 3.10+ and internet connectivity to `site.api.espn.com`.
- ESPN scoreboard data is publicly accessible without an API key for this
  workshop use.
- The endpoint supplies the events available on the current scoreboard. It is
  not a historical archive or a scheduled polling service.
- The league table is calculated from ESPN scoreboard results, rather than a
  dedicated official standings endpoint. It may not include points deductions
  or all league-specific tie-breakers.
- ESPN response fields can vary; malformed or unavailable essential event
  data causes the run to fail visibly and log the traceback.
- Match scores are blank when the fixture has not started or ESPN has not
  provided a score.

## Risks and controls

| Risk | Control |
|---|---|
| Network or ESPN service unavailable | Bounded request timeout; error logged; non-zero process exit |
| Invalid configuration | Validate league, team filter, output path, and timeout before requesting |
| Unexpected API response | Validate response shape and required match structure; log failure |
| Empty result | Still create a header-only CSV and log zero matches |
| Output directory missing | Create parent directories before writing the report |

## Operational run

Run `python football_monitor.py` from this folder. Edit `config.json` to change
the league, team filter, output location, or timeout without editing Python.
Run `python -m unittest -v` to execute automated tests before use.
