# Day Buckets Photo Organizer

Command-line utility that pulls media from Wikimedia Commons by category, normalizes metadata, and organizes the assets into a dated bucket structure with optional Markdown/JSON reporting. Built as part of the SDI Process Automation coursework and polished here so it can live as a public portfolio piece.

## Project Overview (tracked files only)

- `daybuckets.py` – CLI entry point that wires the `fetch`, `organize`, and `report` commands together and fans work out to the rest of the pipeline.
- `Fetch_Category_Members.py` – Recursively walks Wikimedia categories, respecting `--limit`, de-duping visits, and batching page IDs for metadata hydration.
- `Fetch_File_Info.py` – Calls the MediaWiki API in 50-ID chunks to collect image metadata (url, timestamp, extmetadata) and shields the pipeline from transient response issues.
- `Download_Files.py` – Downloads each asset plus a `*.meta.json`, normalizes timestamps with the resilient `parse_fallback_datetime` helper, and preserves mtimes on disk.
- `Sort_Files.py` – Moves or copies paired assets into `buckets/<year>/<month>/<day>/`, handles collision strategies (`keepboth`, `keepnew`, `keepold`), and keeps mtimes consistent.
- `Report_Generate.py` – Builds Markdown and/or JSON reports that summarise per-day file counts, directory sizes, and mtime spans using a recursive directory walk.
- `Logging_Funct.py` – Central logging setup with timed rotation, `--verbose` console streaming, and a UTC formatter shared across subcommands.
- `ENV/API.py` – Defines the Wikimedia endpoint used across fetch helpers.
- `ENV/HEADER.py` – Houses the User-Agent header required by Wikimedia’s bot policy (feel free to swap the contact email).

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install python-dateutil
python3 daybuckets.py fetch --category Dogs --limit 25 --dest PROJECT --md --json
```

- Output lands beneath `PROJECT/` by default (`incoming/` for freshly downloaded files, `buckets/` for organized assets, `reports/` for generated summaries, `logs/` for rotating logs).
- Replace `Dogs` with any Wikimedia Commons category. Always start with `--limit` while testing—large categories expand recursively into subcategories.

## Commands & Flags

### fetch
Fetches media, optionally sorts it, and builds reports in one pass.

- `--category` *(required)* category slug (e.g., `Cathedrals`).
- `--dest` root directory for all outputs (`PROJECT` if omitted).
- `--limit` cap on files collected (strongly recommended for exploratory runs).
- `--mode` choose `move` (relocate into `buckets/`) or `copy` (leave originals in `incoming/`).
- `--moveType` collision policy: `keepboth` (append hash), `keepnew` (replace existing), `keepold` (discard incoming).
- `--dry-run` skip downloads to preview logging only.
- `--md` / `--json` enable Markdown and/or JSON report generation.
- `--verbose` mirror logs to the terminal; `--debug` elevates log level.
- `--clearLog` wipe existing log files before starting.

### organize
Replays the sort/report phases for an existing `incoming/` directory.

- Shares `--dest`, `--mode`, `--moveType`, `--md`, `--json`, `--verbose`, `--debug`, `--clearLog` with `fetch`.
- Skips network activity—useful after adjusting collision strategy or adding new reports.

### report
Only regenerates Markdown/JSON summaries for the current bucket tree.

- Accepts `--dest`, `--md`, `--json`, `--verbose`, `--debug`, `--clearLog`.
- Ignores fetch/sort-specific switches.

## Logging & Reports

- Logs rotate nightly (`daybuckets.log`, 7 retained) and live at `<dest>/logs/`. `--clearLog` removes historical logs before the next run.
- Markdown reports compile per-day tables with file counts, total size, and earliest/latest mtimes. JSON reports mirror the folder hierarchy and include machine-friendly stats.
- Both report paths skip `logs/` and `reports/` folders to avoid recursion noise.

## Safeguards & Behavioural Notes

- Recursive category fetch keeps a `_seen` set to avoid infinite loops and sleeps 100 ms between requests to respect Wikimedia rate limits.
- Metadata hydration gracefully skips pages without `imageinfo` and returns partial results on API hiccups instead of crashing.
- Timestamp parsing strips HTML cruft, handles fuzzy strings (e.g., “Taken on …”), and falls back to best-effort year inference when needed.
- Sorting pairs each `.meta.json` with its sibling image and preserves timestamps after move/copy operations to keep chronological buckets accurate.
- Reporting ignores empty directories and separates numeric day folders from non-numeric collections so tables stay chronologically sorted.

The repository now reads like your public `CoC_Clan_Bot` project: concise README, tracked source files only, and a clean git history. Push it to GitHub and show it off.
