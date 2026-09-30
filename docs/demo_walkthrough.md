# Demo Walkthrough

## 1. Install

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## 2. Generate demo data

```bash
python src/utils/generate_dirty_data.py
python src/utils/generate_sql_demo.py
python -m src.monitoring_demo
```

## 3. Launch

```bash
streamlit run app/streamlit_app.py
```

## 4. Tell the story in this order

1. Start on **Overview** and show the 85.09 quality score.
2. Open **Investigation Report** and filter to Critical/High.
3. Open **Quality Score** and explain the five dimensions.
4. Open **Statistical Detection** and show the reference-vs-current workflow.
5. Open **Record Evidence** and explain that findings retain evidence instead of only labels.
6. Open **SQL Monitoring** and show primary-key, orphan, null, and reconciliation checks.
7. Open **Data Contract** and show why the dirty batch fails the gate.
8. Open **Monitoring & Trends** and show the six-run degradation history.

## 5. Close with the production story

The interesting part is not the number of detectors. The system creates a repeatable quality gate and a traceable investigation path for every batch.
