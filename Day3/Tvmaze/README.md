# TVMaze Show Finder

TVMaze Show Finder is a Python command-line and Flask web application for
searching TVMaze. It converts API responses into `TVShow` dataclass instances
and displays show information in a responsive discovery interface.

## Requirements and startup

- Python 3.10 or later
- Internet access to `api.tvmaze.com`

In PowerShell, from this project folder:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Visit <http://127.0.0.1:5000>. To search from the command line instead:

```powershell
python tvmaze_api.py
python tvmaze_api.py "The Office" --minimum-rating 7.5
```

The web app provides quick searches, rating and genre filters, alphabetical or
rating sorting, show details, official-site links, and browser-local favorites.
The “Include unrated” checkbox includes shows without a numeric TVMaze rating.

## Configuration

`config.json` is loaded relative to the Python script, so startup does not
depend on the current working directory. For example:

```json
{
  "search_term": "comedy",
  "minimum_rating": 4,
  "genre": "Comedy"
}
```

- `search_term` is the default CLI query.
- `minimum_rating` is the default score threshold, from 0 to 10.
- `genre` is an optional exact, case-insensitive genre requirement applied to
  every query. A show with both Comedy and Romance is included; a Romance-only
  show is excluded when the configured genre is Comedy.

The web controls can adjust the minimum rating for a search. The configured
genre remains enforced. CLI query and rating arguments override their defaults.

## Data flow and API response

The application requests
`https://api.tvmaze.com/search/shows?q=<query>`. TVMaze returns a JSON array.
Each item has a relevance `score` and a `show` object. The application reads
`show.name`, `show.genres`, `show.rating.average`, and fields used by the page
such as `image`, `summary`, `premiered`, `status`, and `officialSite`.

The `score` is TVMaze's search relevance, not the audience rating. `genres` is
a list of strings. `rating.average` can be `null`; such shows are excluded by
default (even when the minimum rating is zero) unless “Include unrated” is
selected in the web interface. The configured genre and minimum score are
applied locally after receiving the API response.

## Logging and error handling

The application writes timestamped `INFO` and `ERROR` entries to
`automation.log` beside the scripts. Successful searches record the number of
results. Search/config/API failures are logged with their traceback; the CLI
also reports failures to stderr, while the web page displays a user-facing
error. The log file is created automatically on startup/use.

To verify error logging, the app's test client can simulate an API timeout:

```powershell
python -c "import sys; from unittest.mock import patch; from urllib.error import URLError; sys.path.insert(0, '.'); import app; client=app.app.test_client(); patcher=patch('app.search_shows', side_effect=URLError('simulated timeout')); patcher.start(); response=client.post('/', data={'query': 'comedy'}); patcher.stop(); print('HTTP', response.status_code)"
Get-Content .\automation.log -Tail 5
```

The generated `automation.log` in this folder includes the resulting
`ERROR` entry as evidence. This simulated timeout verifies error reporting;
it is not a failure of TVMaze itself.

## Files

- `app.py` — Flask routes and web search flow.
- `tvmaze_api.py` — TVMaze client, data conversion, config loading, and CLI.
- `config.json` — default query and result filters.
- `logging_config.py` — shared file logger configuration.
- `templates/index.html`, `static/` — front-end interface and behavior.
- `automation.log` — runtime activity and error evidence.
- `tvmaze_sample_output.txt` — sample CLI output and JSON explanation.

Documentation was drafted with AI assistance and checked against the current
code, configuration, and a controlled error-log test.
