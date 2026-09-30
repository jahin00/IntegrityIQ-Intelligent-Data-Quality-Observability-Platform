# 5-minute demo script

## 0:00–0:30 · Set the context

"This is an automated data-quality investigation platform. I designed it around a simple workflow: detect, quantify, explain, prioritize, gate, and monitor."

## 0:30–1:15 · Overview

Show:
- quality score
- total findings
- Critical/High findings
- key dimension scores

Say:

"The included dataset is intentionally dirty. The important point is that the system does not stop at a count of errors. It turns those findings into evidence and prioritization."

## 1:15–2:15 · Investigation Report

Open a high-priority incident.

Explain:
- issue type
- affected records
- statistical / rule evidence
- impact context
- recommended investigation

Say:

"This is meant to support an analyst's next decision, not replace it."

## 2:15–3:00 · Statistics + ML

Show a distribution-shift or anomaly finding.

Explain the method and its limitation:

"A statistically significant shift is not automatically bad data. It can represent a real business change, so the platform flags it as an investigation signal."

## 3:00–3:45 · SQL + contract

Show duplicate keys / orphan rows / reconciliation and then the data-contract violation list.

Say:

"The quality gate combines these different sources of evidence and turns them into PASS, WARNING, or FAIL."

## 3:45–4:30 · Monitoring

Show batch history and score trend.

Explain:

"Each run is fingerprinted and stored, so we can compare the current batch with previous runs and detect regression."

## 4:30–5:00 · Engineering close

Show repository structure and tests.

Close with:

"I built this as a small production-inspired system rather than a single notebook, so it includes configuration, tests, CI, Docker support, and a Streamlit investigation interface."
