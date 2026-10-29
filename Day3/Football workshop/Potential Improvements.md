# Potential Improvements — Touchline Football Match Monitor

This document lists possible next steps for improving the Football Match
Monitor. These are recommendations only; they are not included in the current
implementation.

## Recommended priorities

| Priority | Improvement | Why take it onboard? |
|---|---|---|
| **High** | Validate and report incomplete match data | Some calculations currently skip completed matches if a score cannot be converted to a number. Logging a warning with the event ID would make missing or malformed data visible and help users judge whether a table or form is complete. |
| **High** | Write reports atomically | Write to a temporary file and replace the previous report only after the new CSV is complete. This avoids leaving a truncated or partially-written report if the process stops during output. |
| **High** | Add tests for failure paths and edge cases | Existing tests cover key success paths and a simulated timeout. More tests for invalid configuration, malformed ESPN payloads, write failures, expired cache entries, and empty results would catch regressions earlier. |
| **High** | Make data freshness visible | The cache can serve data up to five minutes old. Showing the last successful fetch time and whether data came from cache helps users understand when scores were last refreshed. |
| **Medium** | Improve the source of league tables | Tables are calculated from scoreboard matches and may omit teams that have not played or official deductions. A verified standings provider, or a complete team roster to seed the calculation, would improve completeness and accuracy. |
| **Medium** | Add retry handling for temporary API failures | A small number of bounded retries with a short delay could recover from brief network interruptions. Retries should be limited and logged so a slow or unavailable service does not stall the app. |
| **Medium** | Add structured logging and log rotation | Consistent event fields (such as run ID, league key, and match count) make logs easier to search. Rotation prevents `automation.log` growing without limit during frequent use. |
| **Medium** | Move operational settings into configuration | Cache lifetime, maximum cache entries, and retry count could be configurable if users need different freshness or reliability trade-offs. Keep safe defaults and validate each setting. |
| **Medium** | Add an automated accessibility check | The pages already include labels and responsive layouts. Automated checks for keyboard navigation, contrast, and screen-reader semantics can identify issues before sharing the dashboard more widely. |
| **Low** | Add export options | JSON export, or an option to choose a report location in the interface, could help other tools consume the results without changing the existing CSV workflow. |
| **Low** | Add a scheduled refresh mode | A scheduler could create reports regularly without manual runs. This should only be added if the team needs ongoing monitoring; the current project runs on demand. |
| **Low** | Add deployment and operations guidance | If the site is to be shared beyond a local workshop, document a supported host, production server, environment setup, and safe restart procedure. The built-in Flask server is intended for local development, not production hosting. |

## Suggested order

Start with data validation, safe report writing, and broader automated tests.
These changes improve trust in the current results without changing how users
work. Next, make data freshness and logging easier to understand, then consider
a standings source and deployment improvements if the project will be used
regularly or by a wider team.

## How to decide

Before implementing an improvement, confirm the team's need and agree on a
measurable outcome. For example:

- **Data quality:** every skipped or malformed event is identified in the log.
- **Report reliability:** a failed write leaves the last successful report
  intact.
- **Freshness:** users can see when data was retrieved and whether it is
  cached.
- **Standings:** the table includes all participating teams and clearly states
  the data source and tie-break rules.
- **Operations:** the chosen deployment method is supported, documented, and
  tested for restart and failure recovery.
