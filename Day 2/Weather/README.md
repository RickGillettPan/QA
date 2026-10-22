# Weather and clinical research dashboards

This folder contains two independent, browser-based dashboards. Both use public APIs and run locally without a build step, package installation, sign-in, or API keys.

## Run the dashboards

From this folder, run:

```powershell
python main.py
```

Then open either page in a browser:

- Weather forecast: <http://127.0.0.1:8000/>
- Clinical research landscape: <http://127.0.0.1:8000/clinical.html>

Press `Ctrl+C` in the terminal to stop the local server. Python 3 and an internet connection are required. Serving the pages over HTTP lets the browser request their public APIs.

## Weather forecast

`index.html` displays the current local conditions and a seven-day forecast for a choice of UK and international cities. Select a day to see its high and low temperatures, precipitation probability, maximum wind, sunrise and sunset, and an hourly temperature/rain-probability chart. The weekly chart compares the high and low temperature trends and shows precipitation probabilities.

The page requests current, daily, and hourly forecasts from the [Open-Meteo Forecast API](https://open-meteo.com/en/docs). It uses the API-provided timezone for each location and WMO weather codes for condition descriptions. No API key is required for this demonstration. Check Open-Meteo's terms and attribution requirements before adapting the app for commercial or production use.

## Clinical research landscape

`clinical.html` searches a condition or intervention against two independent public data sources:

- [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/about-api) supplies trial records, registry status, phase, sponsor, condition, intervention, and locations. Results are sorted by latest update, can be filtered by status, and can be paged through.
- [Europe PMC REST API](https://europepmc.org/RestfulWebService) supplies publication counts and recent related literature, with links to publication records.
- [NCBI PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25500/) supplies a fallback list of publications indexed as clinical trials when the ClinicalTrials.gov API cannot be reached.

The sources load independently, so an unavailable API does not prevent results from the others. If trial records cannot be fetched, the left panel falls back to PubMed-indexed clinical-trial publications and provides a link to search the registry directly. These fallback papers are not registry entries; they do not provide current recruitment status or study locations. The status filter is disabled in fallback mode.

### Known network limitation

In the development environment, requests to both `clinicaltrials.gov` and the NCI trial API host were blocked with an HTTP 403 HTML page from the network's FortiGuard web filter; the responses were not trial JSON. Alternative WHO and ISRCTN hosts were also blocked. Europe PMC and NCBI PubMed E-utilities were reachable and returned results. The dashboard therefore uses PubMed's clinical-trial publication type as its fallback, while clearly identifying the different data and limitations. The direct registry link may also be restricted by the same network.

## Important limitations

These pages are lightweight examples for exploration, not validated operational or clinical systems. Public records can be incomplete, delayed, or changed by their source. Trial status and publication listings are not a substitute for reviewing the original registry entries and papers; they do not establish treatment effectiveness, safety, eligibility, or medical advice. No patient-level information is collected or stored.

## Files

- `main.py` — starts a small Python standard-library HTTP server for both pages.
- `index.html` — weather forecast dashboard, styles, and client-side API integration.
- `clinical.html` — clinical-trial and publication dashboard, styles, and client-side API integration.
