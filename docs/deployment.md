# Deployment Guide

The project is designed to run locally, inside Docker, or on a Streamlit-compatible hosting environment.

## Local

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python src/utils/generate_dirty_data.py
python src/utils/generate_sql_demo.py
python -m src.monitoring_demo
streamlit run app/streamlit_app.py
```

The application listens on Streamlit's default local port, `8501`.

## Docker

Build the image:

```bash
docker build -t ai-data-quality-detective .
```

Run it:

```bash
docker run --rm -p 8501:8501 ai-data-quality-detective
```

Or use Compose:

```bash
docker compose up --build
```

The Docker image generates the included demo assets during the image build, so the first launch is immediately usable.

## Portfolio demo sequence

1. Open **Overview** and show the score, gate status, and priority mix.
2. Open **Investigation Report** and drill into a Critical/High incident.
3. Open **Quality Score** to explain the transparent dimensions.
4. Open **Statistical Detection** to show evidence for a distribution shift.
5. Open **SQL Monitoring** to demonstrate relational checks.
6. Open **Monitoring & Trends** to show historical degradation.
7. Use the export buttons to demonstrate how findings can leave the dashboard as an analyst report.
