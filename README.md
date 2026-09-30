# 🔎 AI Data Quality Detective

> **A production-inspired data observability and investigation platform for messy tabular and relational data.**

**Detect → quantify → explain → prioritize → gate → monitor**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-18%20passing-16a34a)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-64748b)](LICENSE)

## Why this project?

Data-quality work is rarely just "find the nulls." A useful analyst needs to answer:

- **What is wrong?**
- **How much data is affected?**
- **What evidence supports the finding?**
- **Could the change be legitimate?**
- **What should be investigated next?**
- **Did quality deteriorate compared with the previous batch?**

This project turns those questions into a repeatable workflow combining deterministic rules, statistical tests, SQL integrity checks, unsupervised ML, data contracts, quality gates, reporting, and historical monitoring.

## Demo at a glance

The included dirty retail dataset intentionally contains realistic quality failures:

| Metric | Demo result |
|---|---:|
| Records | **5,012** |
| Columns | **11** |
| Consolidated findings | **24** |
| Critical / High findings | **8** |
| Data quality score | **85.09 / 100** |
| Quality gate | **FAIL** |

> The score is a project-specific transparent metric, not a universal industry standard. Statistical shifts and ML anomalies are investigation signals, not automatic proof of bad data.

## Architecture

![System architecture](docs/assets/architecture.svg)

## What the platform checks

| Layer | Examples |
|---|---|
| **Profiling** | nulls, duplicates, dtypes, cardinality, summary statistics |
| **Rules** | ranges, allowed categories, dates, required fields |
| **Statistics** | IQR, Z-score, KS test, chi-square, PSI |
| **ML** | Isolation Forest for multivariate anomaly detection |
| **SQL** | duplicate keys, orphan rows, required nulls, reconciliation |
| **Governance** | data contracts and configurable quality gates |
| **Issue intelligence** | severity, priority, evidence, impact, next investigation |
| **Monitoring** | historical runs, batch comparison, quality trends |
| **Delivery** | Streamlit dashboard, exports, Pytest, GitHub Actions, Docker |

## A real investigation looks like this

```text
Incoming batch
      ↓
Contract + profiling
      ↓
24 consolidated findings
      ↓
8 Critical/High findings
      ↓
Evidence + affected records
      ↓
Quality score: 85.09
      ↓
Gate: FAIL
      ↓
Investigation report
      ↓
Historical monitoring
```

Example finding:

```text
Issue: Duplicate transaction identifiers
Severity: High
Priority: P1
Evidence: multiple records share the same transaction_id
Potential impact: transaction-level aggregation may be double-counted
Next investigation: check upstream ingestion/deduplication logic
```

## Quick start

### Local

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Generate the included demo assets:

```bash
python src/utils/generate_dirty_data.py
python src/utils/generate_sql_demo.py
python -m src.monitoring_demo
```

Launch the application:

```bash
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501`.

### Docker

```bash
docker compose up --build
```

Then open `http://localhost:8501`.

### Tests

```bash
pytest -q
```

Expected baseline:

```text
18 passed
```

## Recommended demo flow

For a 3–5 minute portfolio walkthrough:

1. **Overview**: show the 85.09 quality score and the Critical/High count.
2. **Investigation Report**: open one high-priority issue and explain the evidence.
3. **Statistical Detection**: show how a distribution shift is measured, not simply labeled.
4. **SQL Monitoring**: demonstrate duplicate keys, orphan rows, or reconciliation failures.
5. **Data Contract**: show why the dirty batch fails the quality gate.
6. **Monitoring & Trends**: show how quality changes across batches.

Full walkthrough: [`docs/demo_walkthrough.md`](docs/demo_walkthrough.md)

## Project structure

```text
ai-data-quality-detective/
├── app/                    # Streamlit application
├── data/                   # demo data and monitoring assets
├── docs/                   # architecture, case study, deployment, interview material
├── portfolio/              # recruiter-facing artifacts
├── src/
│   ├── anomaly/            # Isolation Forest
│   ├── ingestion/          # CSV / Excel loaders
│   ├── monitoring/         # batch history and comparisons
│   ├── profiling/          # rule + statistical detectors
│   ├── reporting/          # issue intelligence and reports
│   ├── scoring/            # quality scorecard
│   ├── sql/                # relational checks
│   └── utils/              # demo-data generation
├── tests/                  # automated tests
├── .github/workflows/      # CI quality checks
├── data_contract.yaml      # schema + quality gate policy
└── config.yaml             # detector configuration
```

## Engineering choices worth discussing

### Rules vs. ML

Known business constraints are explicit rules. Isolation Forest is reserved for unusual multivariate patterns. That keeps the system explainable and avoids labeling every unusual observation as an error.

### Statistical shifts

KS/chi-square and PSI compare a reference distribution with a current batch. A statistically significant shift can be legitimate, so the application reports it as investigation evidence rather than a verdict.

### Data contracts

Schema expectations and business constraints live in YAML. The same engine can therefore be configured for another dataset without rewriting the detectors.

### Quality gates

The pipeline converts evidence into a repeatable **PASS / WARNING / FAIL** decision using configurable thresholds and contract violations.

## Documentation

- [`docs/assets/architecture.svg`](docs/assets/architecture.svg) — system architecture
- [`docs/case_study.md`](docs/case_study.md) — end-to-end retail incident
- [`docs/demo_walkthrough.md`](docs/demo_walkthrough.md) — presentation sequence
- [`docs/interview_guide.md`](docs/interview_guide.md) — likely interview questions
- [`docs/deployment.md`](docs/deployment.md) — Docker and deployment notes
- [`docs/cv_bullets.md`](docs/cv_bullets.md) — CV-ready wording
- [`portfolio/project_summary.md`](portfolio/project_summary.md) — recruiter-facing summary
- [`portfolio/github_description.md`](portfolio/github_description.md) — repository description / About text

## CV version

**AI Data Quality Detective | Python, Pandas, SQL, Statistics, Streamlit, Scikit-learn**

- Built an automated data-quality investigation platform for CSV, Excel, and SQLite sources, detecting completeness, validity, uniqueness, category/date anomalies, distribution shifts, contract violations, and multivariate anomalies.
- Designed a transparent five-dimension quality scorecard and PASS/WARNING/FAIL gate with record-level evidence, severity prioritization, impact context, investigation recommendations, and historical batch monitoring.
- Combined SQL integrity checks, IQR/Z-score, KS, chi-square, PSI, and Isolation Forest in a Streamlit dashboard with automated tests, GitHub Actions CI, Docker support, and exportable investigation reports.

## Limitations and next improvements

This repository is intentionally production-inspired rather than a claim of a full enterprise data-observability stack. A production rollout would typically add a managed warehouse, orchestration, authentication/authorization, persistent monitoring storage, alerting, and stronger data lineage.

## License

MIT. See [`LICENSE`](LICENSE).
