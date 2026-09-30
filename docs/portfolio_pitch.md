# Portfolio pitch

## 15-second version

I built a data-quality investigation platform that goes beyond null and duplicate checks. It combines business rules, statistical tests, SQL integrity checks, Isolation Forest anomaly detection, data contracts, quality gates, and historical monitoring in one Streamlit application.

## 45-second version

The idea was to treat data quality as an investigation problem. A new batch is profiled against configurable rules and a data contract, then checked using statistical methods such as IQR, KS, chi-square, and PSI plus Isolation Forest for multivariate anomalies. SQL checks handle relational issues such as duplicate keys, orphan records, and reconciliation mismatches. The findings are consolidated into issue records with severity, evidence, potential impact, and recommended investigation areas. A quality score and PASS/WARNING/FAIL gate are then tracked historically so the user can see whether data quality is getting better or worse across batches.

## Strong interview transition

The most important design decision was not to call every anomaly an error. Known constraints use deterministic rules; statistical and ML signals are treated as evidence that needs investigation and business context.
