# Debris Data Explorer

Starter platform for the TAMU debris-data project. It pulls disaster-debris data from
public ArcGIS REST APIs, saves it locally, and shows it in a Streamlit app.

| Source | What | Records |
|---|---|---|
| `la_tickets` | Louisiana DOTD debris load tickets, Hurricane Laura 2020 (one row per truckload) | ~44k |
| `houston_dms` | City of Houston debris management sites (polygons) | 7 |

## Setup (once)

```bash
cd debriProject
python3 -m venv venv               # skip if venv/ already exists
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# Optional: refresh data from the APIs (full pull -> data/raw/, 5k sample -> data/sample/)
python -m pipeline.ingest --source la_tickets --sample
python -m pipeline.ingest --source houston_dms --sample

streamlit run app/Home.py           # opens http://localhost:8501
pytest                              # tests run on data/sample/
```

You do **not** need to run ingest to start working. `data/sample/` is committed and the
app falls back to it when `data/raw/` is missing. The sidebar toggle switches between
the full data and the sample.

## Project layout

```
pipeline/
  sources.py   URLs + which fields to keep / which are private, per source
  arcgis.py    paginated ArcGIS REST client
  ingest.py    CLI: fetch a source and save it to data/raw (+ data/sample)
  load.py      load_la_tickets(), load_houston_dms(): use these everywhere
app/Home.py    Streamlit starter page
tests/         pytest smoke tests on the sample data
data/raw/      full pulls (gitignored)
data/sample/   small committed sample
```

**Adding a field:** add it to `keep_fields` in `pipeline/sources.py`, then re-run ingest.
**Adding a page:** create `app/pages/1_Something.py`. Streamlit picks it up automatically.
Load data through `pipeline.load`.

## Privacy

Personal fields are never downloaded. Ingest requests only the fields listed in `keep_fields`.
It also checks `private_fields` before saving and fails if one is present.

- Louisiana: `Load_Monitor`, `Disposal_Monitor`
- Houston: `Owner`, `OwnerFullAddress`, `OwnerPhone`, `OwnerEmail`, `created_user`, `last_edited_user`

Never add these to `keep_fields`, and never commit them.

## Deploy (Streamlit Community Cloud, free)

1. Push the repo to GitHub (team repo).
2. At https://share.streamlit.io choose **Create app**, then pick the repo, branch `main`
   and main file `app/Home.py`.
3. Under **Advanced settings**, choose Python **3.13** to match the local venv.
4. Deploy. Every push to `main` redeploys automatically. The deployed app uses
   `data/sample/` because `data/raw/` is not committed.

Secrets (e.g. an LLM API key later) go in the app's **Settings → Secrets** on Streamlit
Cloud, and locally in `.streamlit/secrets.toml`, which is gitignored.

## Team workflow

- `main` is protected: no direct pushes.
- One feature branch per task, e.g. `feature/kpi-fill-rate`.
- Open a PR into `main`. It needs one teammate's review, and `pytest` must pass.
- Keep PRs small. Pull `main` often.
