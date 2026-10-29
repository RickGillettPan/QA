# Touchline | Football Match Monitor

Touchline retrieves football fixtures and results from ESPN, applies league
and team filters, and creates a shareable CSV report. It includes a web
dashboard for browsing matchdays, results, league tables, and team form.

## Contents

- [Get started](#get-started)
- [Use the dashboard](#use-the-dashboard)
- [Configuration](#configuration)
- [Reports and logging](#reports-and-logging)
- [Tests](#tests)
- [Data notes](#data-notes)
- [Potential improvements](#potential-improvements)
- [Project files](#project-files)

## Get started

**Requirements:** Python 3.10+ and internet access to `site.api.espn.com`.

From this project folder, install the dependency and start the website:

```powershell
python -m pip install -r requirements.txt
python web_app.py
```

Open <http://127.0.0.1:5000> in your browser. To generate a CSV report without
opening the website, run this in a second terminal:

```powershell
python football_monitor.py
```

The default settings monitor the English Premier League and write
`match_report.csv`.

## Use the dashboard

| Page | What you can do |
|---|---|
| **Match centre** | Choose a league and date, filter by team or match status, and download that day's report. |
| **Results** | Browse completed and in-progress matches from the current season. |
| **League table** | View calculated standings and save a favourite club. |
| **Team form** | View a club's season record and its five latest completed results. |

The selected league is shared across pages. Your favourite club is saved in
your browser, highlighted in match lists, and can be used to filter results.
These preferences are local to the browser and are not shared across devices.

On the Match centre, use the date picker, the seven-day strip, or the previous
and next buttons to browse fixtures. Match times are displayed in your local
time zone. Select **Download report** to generate and download the report for
the chosen date.

## Configuration

Edit `config.json` to change the default league, team filter, report location,
or request timeout. No code changes are needed.

| Setting | Description |
|---|---|
| `league` | League key from the table below. |
| `team_filter` | Optional, case-insensitive partial match against either team. Use `""` for all teams. |
| `output_file` | CSV destination. Relative paths start from this project folder; missing folders are created. |
| `request_timeout_seconds` | Maximum time to wait for an ESPN request. |

| `league` value | Competition | ESPN code |
|---|---|---|
| `premier_league` | English Premier League | `eng.1` |
| `scottish_premiership` | Scottish Premiership | `sco.1` |
| `bundesliga` | German Bundesliga | `ger.1` |
| `ligue_1` | French Ligue 1 | `fra.1` |

Example:

```json
{
  "league": "premier_league",
  "team_filter": "Arsenal",
  "output_file": "reports/arsenal_matches.csv",
  "request_timeout_seconds": 20
}
```

To run with a different configuration file:

```powershell
python football_monitor.py --config .\config.json
```

## Reports and logging

The CSV report includes the event ID, league, match date, teams and scores,
status, venue, and match name. It includes a header even when no matches meet
the selected filters. Scores remain blank when ESPN has not supplied them.

`automation.log` records each run's start, selected league, number of matches
processed, and report path after the file is successfully written. Failures
are recorded as errors with tracebacks, including configuration errors.
The command-line script returns:

| Exit code | Meaning |
|---:|---|
| `0` | Report created successfully. |
| `1` | ESPN, data, or output error. |
| `2` | Invalid configuration. |

Errors are also summarized in the terminal.

## Tests

Run all unit tests from this folder:

```powershell
python -m unittest -v
```

The tests cover configuration, ESPN response parsing and caching, filtering,
CSV output, standings, team form, and web-page routes.

Python functions and browser-side helpers include docstrings or concise
comments describing their purpose. Generated data files (`automation.log` and
`match_report.csv`) and configuration files are kept free of code comments.

## Data notes

- ESPN scoreboard data is publicly accessible for this workshop and does not
  require an API key.
- Results, fixtures, and tables depend on the data available from ESPN.
- Standings are calculated from completed matches using three points for a
  win, one for a draw, and zero for a loss. They are sorted by points, goal
  difference, then goals scored. They may not reflect official deductions or
  every competition-specific tie-break rule.
- ESPN responses are cached in memory for up to five minutes, with a maximum
  of 64 entries. Data shown while browsing may therefore be up to five minutes
  old. The cache clears when the application restarts.
- The matchday calendar queries one date at a time; it is not a background
  polling service or a complete historical archive.

## Potential improvements

`Potential Improvements.md` describes optional next steps, their benefits, and
a suggested order for considering them. It is a proposal, not a list of
features already implemented.

## Project files

| File or folder | Purpose |
|---|---|
| `football_monitor.py` | ESPN client, configuration, filtering, CSV report, and command-line runner. |
| `web_app.py` | Flask application and dashboard routes. |
| `templates/`, `static/` | Web pages, styles, and browser-side controls. |
| `config.json` | Default runtime settings. |
| `requirements.txt` | Python dependencies. |
| `automation.log` | Run history and error details. |
| `match_report.csv` | Generated example report. |
| `test_football_monitor.py`, `test_web_app.py` | Automated tests. |
| `Automation Definition Worksheet.md` | Workflow inputs, processing, outputs, assumptions, and risks. |
| `Potential Improvements.md` | Prioritized improvement ideas and reasons to consider them. |

Documentation was prepared with AI assistance and checked against the project
configuration and implementation.
