# Interview Guide

## 30-second explanation

> I built an automated data-quality investigation platform for retail transaction data. It combines deterministic validation, statistical tests, SQL checks, Isolation Forest anomaly detection, configurable data contracts, a quality scorecard, and historical monitoring. The goal is not just to flag bad rows, but to explain why a finding matters, what evidence supports it, and where the analyst should investigate next.

## Questions you should be ready for

### Why use rules and ML together?

Rules are appropriate for known business constraints. ML is useful for detecting unusual combinations or patterns that are difficult to encode as explicit rules. Keeping both layers separate makes the system easier to explain and reduces false confidence.

### Why use KS test and PSI?

The KS test provides a statistical test for differences between numeric distributions, while PSI provides a practical shift measure. Using both gives a richer view than relying on one number.

### Why can a statistically significant shift be acceptable?

A distribution can change because the business changed. Statistical significance says that the distributions differ, not that the new distribution is wrong.

### How did you calculate the quality score?

The project uses five dimensions: completeness, consistency, validity, uniqueness, and timeliness. Each has a configurable weight and a transparent penalty formula. It is explicitly a portfolio metric, not an industry-standard universal score.

### What is a data contract?

A data contract defines the expected structure and constraints of an incoming dataset, such as required fields, accepted types, uniqueness, allowed ranges, and categories. The quality gate then uses those results to return PASS, WARNING, or FAIL.

### Why Isolation Forest?

It is an unsupervised method that works well for high-dimensional tabular anomaly screening. In this project it is used as an investigation aid, not as a final truth oracle.

### What happens when the gate fails?

The system preserves the evidence, identifies severity and priority, records the batch result in monitoring history, and presents an investigation queue. The next step is root-cause analysis in the upstream pipeline or source system.
