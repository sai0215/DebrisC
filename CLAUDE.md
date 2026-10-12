# CLAUDE.md

Context for Claude Code sessions on this repo.

## What this is
Internal prototype for a 5-person Texas A&M research team. It interprets disaster-debris data.
Everything must run on free tiers. Current state is a **starter platform**: data ingest + loading +
one simple Streamlit page. The team builds features on top of it.

## Stack
- Python 3.13 in `./venv` (team decision; keep code 3.11-compatible anyway).
- pandas, pyarrow, requests, Streamlit, Plotly, pydeck. Pinned in `requirements.txt`.
- Data lives as files in the repo (Parquet / GeoJSON). No database server.
- Hosting: Streamlit Community Cloud, auto-deploy from GitHub `main`, entry `app/Home.py`.

## Data sources (`pipeline/sources.py`)
- `la_tickets`: Louisiana DOTD debris tickets, Hurricane Laura 2020, ~44k rows, max 10k per
  request. Paginated by `resultOffset`, ordered by OBJECTID, `returnGeometry=false`. Points come from
  `Begin_Lat`/`Begin_Long`. `Load_Date`/`Disposal_Date` are epoch ms; `load.py` converts
  them to America/Chicago. `Capacity_L` = truck capacity (CY), `Haul_Vol` = CY hauled,
  `Pay_Item` = debris type.
- `houston_dms`: City of Houston debris management site polygons, 7 rows, `f=geojson`.
  Saved as GeoJSON. `PropertySize` unit is not documented by the source.

## PRIVACY (hard rule)
Ingest requests only `keep_fields`. `private_fields` must never be saved or committed:
LA `Load_Monitor`, `Disposal_Monitor`; Houston `Owner*`, `created_user`, `last_edited_user`.
`ingest.assert_no_private_fields` enforces this, and a test covers it.

## Commands
```bash
./venv/bin/python -m pipeline.ingest --source la_tickets|houston_dms [--sample]
./venv/bin/streamlit run app/Home.py
./venv/bin/python -m pytest
```

## Conventions
- Always load data via `pipeline/load.py`. It prefers `data/raw/` and falls back to `data/sample/`.
  `data/raw/` is gitignored; `data/sample/` (5k LA rows, seed 42, plus all Houston sites) is committed.
- Type hints, small functions, docstrings on public functions. No secrets in code.
- Wrap data loads in the app with `st.cache_data`.
- Do not run git commands unless the user asks.

## Planned direction (not built yet)
Data dictionary + term mapping to standardize field names across states, with Pandera validation.
Pure, tested KPI functions (`kpis/`), e.g. CY hauled per day, loads and trucks per day, fill %
(`Haul_Vol/Capacity_L`), load→disposal hours, volume by site/parish/debris type, loads per truck per day.
Rule-based suggestions with configurable thresholds. An LLM layer (TAMU AI API, assumed OpenAI-compatible,
`openai` package with `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY`). The LLM never computes numbers;
it only writes text and calls KPI functions as tools. The app must work without a key.
No LangChain, dbt or vector DB.
