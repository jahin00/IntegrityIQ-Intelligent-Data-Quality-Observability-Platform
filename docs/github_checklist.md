# GitHub publication checklist

## Before pushing

- [ ] Replace any local-only paths or personal references.
- [ ] Confirm `.env`, credentials, notebooks outputs, and large generated files are ignored.
- [ ] Run `pytest -q` and confirm the baseline suite passes.
- [ ] Regenerate demo data from the repository instructions.
- [ ] Launch Streamlit locally and verify the polished UI.
- [ ] Open the Overview page first and confirm the quality score and findings render.
- [ ] Verify the Investigation Report export works.
- [ ] Verify the Docker path with `docker compose up --build` when Docker is available.

## Repository presentation

Recommended order for a recruiter visiting the repository:

1. README hero + demo result
2. Architecture diagram
3. Detection coverage table
4. Investigation example
5. Quick start
6. Documentation links
7. Tests / CI

## Screenshots

Take 3 screenshots from the running Streamlit app and store them in `docs/assets/`:

- `overview.png`
- `investigation-report.png`
- `monitoring-trends.png`

Add them below the architecture section in the README once available.

## GitHub Actions

The workflow in `.github/workflows/quality.yml` should run on push and pull request. Keep the test output visible in the repository so visitors can see that the project is maintained as a software system, not only as a notebook.
