# AI Data Quality Detective - Investigation Report

**Dataset:** retail_transactions_dirty.csv
**Rows:** 5,012  
**Columns:** 11  
**Overall quality score:** 85.09 / 100
**Total findings:** 24
**Critical/High findings:** 8

## Executive summary

The report consolidates deterministic validation, statistical detection, and machine-learning anomaly findings into an investigation queue. Statistical shifts and ML anomalies are investigation signals, not proof of incorrect data.

## Quality scorecard

| Dimension | Score | Weight | Interpretation |
|---|---:|---:|---|
| Completeness | 99.68 | 0.200 | Strong |
| Consistency | 34.92 | 0.200 | Needs investigation |
| Validity | 93.24 | 0.250 | Strong |
| Uniqueness | 99.52 | 0.150 | Strong |
| Timeliness | 99.66 | 0.200 | Strong |

## Findings

| ID | Priority | Severity | Dimension | Issue | Column | Affected | Impact |
|---|---|---|---|---|---|---:|---|
| DQ-81A50FE8 | P1 | High | Consistency | Distribution Shift | unit_price | 5,012 (100.00%) | A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift. |
| DQ-5EB001F3 | P1 | High | Consistency | Distribution Shift | total_amount | 4,987 (99.50%) | A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift. |
| DQ-0F5884E8 | P1 | High | Consistency | Distribution Shift | region | 4,963 (99.02%) | A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift. |
| DQ-A7D958C4 | P1 | High | Timeliness | Date Anomaly | transaction_date | 7 (0.14%) | Malformed or future dates can break time-based reporting, period comparisons, and recency calculations. |
| DQ-416EC6BC | P1 | High | Validity | Invalid Value | customer_age | 6 (0.12%) | Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis. |
| DQ-34241D9F | P1 | High | Validity | Invalid Value | discount | 4 (0.08%) | Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis. |
| DQ-4E458C91 | P1 | High | Validity | Invalid Value | discount | 4 (0.08%) | Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis. |
| DQ-7F136391 | P1 | High | Validity | Invalid Value | customer_age | 2 (0.04%) | Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis. |
| DQ-C43DD08A | P2 | Medium | Consistency | Category Inconsistency | region | 1,033 (20.61%) | Multiple representations of the same category can fragment group-by results and produce misleading segment totals. |
| DQ-A6A0B69C | P2 | Medium | Consistency | Category Inconsistency | region | 1,026 (20.47%) | Multiple representations of the same category can fragment group-by results and produce misleading segment totals. |
| DQ-C3CA3D2E | P2 | Medium | Validity | Outlier | total_amount | 115 (2.29%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-5D286008 | P2 | Medium | Validity | Anomaly | quantity, unit_price, discount, customer_age, total_amount | 101 (2.02%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-A677D581 | P2 | Medium | Completeness | Missing Values | customer_age | 100 (2.00%) | Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss. |
| DQ-C5E32765 | P2 | Medium | Validity | Outlier | total_amount | 68 (1.36%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-3047AFD6 | P2 | Medium | Timeliness | Date Anomaly | transaction_date | 10 (0.20%) | Malformed or future dates can break time-based reporting, period comparisons, and recency calculations. |
| DQ-D658B80A | P3 | Low | Completeness | Missing Values | region | 49 (0.98%) | Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss. |
| DQ-515F05C4 | P3 | Low | Completeness | Missing Values | total_amount | 25 (0.50%) | Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss. |
| DQ-2ADFED35 | P3 | Low | Uniqueness | Duplicate Rows | __row__ | 24 (0.48%) | May double-count records, distort aggregates, and create unreliable joins or KPIs. |
| DQ-AF6A4B1C | P3 | Low | Validity | Outlier | quantity | 15 (0.30%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-8E498027 | P3 | Low | Validity | Outlier | quantity | 11 (0.22%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-3EE72DC2 | P3 | Low | Validity | Outlier | discount | 8 (0.16%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-557ED186 | P3 | Low | Validity | Outlier | discount | 8 (0.16%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-A8CE6CEA | P3 | Low | Validity | Outlier | customer_age | 7 (0.14%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |
| DQ-A6ECB533 | P3 | Low | Validity | Outlier | customer_age | 6 (0.12%) | Rare records may be valid events or data errors and should be reviewed before exclusion or correction. |

## Investigation queue

### DQ-81A50FE8 - Distribution Shift
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Reference n=5,000, current n=5,012; KS=0.0980, p=2.30793e-21, PSI=0.0623.
**Potential impact:** A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift.
**Investigation area:** Data pipeline, population mix, and business change
**Recommended action:** Check for genuine business changes, upstream source changes, unit changes, or pipeline regressions.

### DQ-5EB001F3 - Distribution Shift
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Reference n=5,000, current n=4,987; KS=0.0459, p=5.25584e-05, PSI=0.0158.
**Potential impact:** A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift.
**Investigation area:** Data pipeline, population mix, and business change
**Recommended action:** Check for genuine business changes, upstream source changes, unit changes, or pipeline regressions.

### DQ-0F5884E8 - Distribution Shift
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Reference n=5,000, current n=4,963; chi2=81.3266, p=8.8057e-14, PSI=0.1311.
**Potential impact:** A changed distribution may indicate a real business event, source-system change, pipeline issue, or population shift.
**Investigation area:** Data pipeline, population mix, and business change
**Recommended action:** Review category-mix changes and upstream mapping logic before treating the shift as a data defect.

### DQ-A7D958C4 - Date Anomaly
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Non-null records could not be parsed as dates.
**Potential impact:** Malformed or future dates can break time-based reporting, period comparisons, and recency calculations.
**Investigation area:** Timestamp parsing, business dates, and ingestion timing
**Recommended action:** Validate date formatting upstream and quarantine malformed values.

### DQ-416EC6BC - Invalid Value
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Observed values above maximum 120.
**Potential impact:** Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis.
**Investigation area:** Source validation and domain constraints
**Recommended action:** Investigate customer_age values above the permitted maximum and upstream validation.

### DQ-34241D9F - Invalid Value
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Observed values below minimum 0.
**Potential impact:** Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis.
**Investigation area:** Source validation and domain constraints
**Recommended action:** Investigate discount values below the permitted minimum and upstream validation.

### DQ-4E458C91 - Invalid Value
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Observed values above maximum 1.
**Potential impact:** Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis.
**Investigation area:** Source validation and domain constraints
**Recommended action:** Investigate discount values above the permitted maximum and upstream validation.

### DQ-7F136391 - Invalid Value
**Severity:** High | **Priority:** P1 | **Status:** Open
**Evidence:** Observed values below minimum 1.
**Potential impact:** Invalid values can propagate incorrect business metrics and reduce trust in downstream analysis.
**Investigation area:** Source validation and domain constraints
**Recommended action:** Investigate customer_age values below the permitted minimum and upstream validation.

### DQ-C43DD08A - Category Inconsistency
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** Variants map to normalized category 'dhaka': ['DHAKA', 'Dhaka', 'Dhaka ', 'dhaka'].
**Potential impact:** Multiple representations of the same category can fragment group-by results and produce misleading segment totals.
**Investigation area:** Reference data / controlled vocabulary
**Recommended action:** Standardize category values at ingestion and maintain a controlled vocabulary.

### DQ-A6A0B69C - Category Inconsistency
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** Variants map to normalized category 'chattogram': ['CHATTOGRAM', 'Chattogram', 'chattogram'].
**Potential impact:** Multiple representations of the same category can fragment group-by results and produce misleading segment totals.
**Investigation area:** Reference data / controlled vocabulary
**Recommended action:** Standardize category values at ingestion and maintain a controlled vocabulary.

### DQ-C3CA3D2E - Outlier
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** Q1=4169, Q3=2.011e+04, IQR=1.594e+04; 115 values fall outside the IQR fences.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Investigate extreme records and confirm whether they reflect genuine business events or data-entry problems.

### DQ-5D286008 - Anomaly
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** Detected 101 candidate anomalies across 5 numeric features. Lower decision-function scores indicate greater anomaly likelihood.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Multivariate anomaly review and upstream process behavior
**Recommended action:** Investigate the highest-ranked records and determine whether the pattern reflects a real event, data-entry error, pipeline issue, or a previously unseen valid segment.

### DQ-A677D581 - Missing Values
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** 100 missing values (2.00% of records).
**Potential impact:** Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss.
**Investigation area:** Upstream ingestion and source completeness
**Recommended action:** Investigate source completeness and decide whether imputation, correction, or exclusion is appropriate.

### DQ-C5E32765 - Outlier
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** 68 values exceed the absolute z-score threshold of 3.0.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Review extreme standardized deviations alongside business context before removing records.

### DQ-3047AFD6 - Date Anomaly
**Severity:** Medium | **Priority:** P2 | **Status:** Open
**Evidence:** Dates occur after reference date 2026-09-30.
**Potential impact:** Malformed or future dates can break time-based reporting, period comparisons, and recency calculations.
**Investigation area:** Timestamp parsing, business dates, and ingestion timing
**Recommended action:** Confirm whether future-dated records are valid forecasts or ingestion errors.

### DQ-D658B80A - Missing Values
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** 49 missing values (0.98% of records).
**Potential impact:** Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss.
**Investigation area:** Upstream ingestion and source completeness
**Recommended action:** Investigate source completeness and decide whether imputation, correction, or exclusion is appropriate.

### DQ-515F05C4 - Missing Values
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** 25 missing values (0.50% of records).
**Potential impact:** Missing fields may reduce analytical coverage and cause downstream filtering, aggregation, or model-input loss.
**Investigation area:** Upstream ingestion and source completeness
**Recommended action:** Investigate source completeness and decide whether imputation, correction, or exclusion is appropriate.

### DQ-2ADFED35 - Duplicate Rows
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** 24 rows are part of exact duplicate groups.
**Potential impact:** May double-count records, distort aggregates, and create unreliable joins or KPIs.
**Investigation area:** Deduplication and ingestion controls
**Recommended action:** Trace the ingestion path, define the deduplication key, and prevent repeated loads.

### DQ-AF6A4B1C - Outlier
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** Q1=3, Q3=8, IQR=5; 15 values fall outside the IQR fences.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Investigate extreme records and confirm whether they reflect genuine business events or data-entry problems.

### DQ-8E498027 - Outlier
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** 11 values exceed the absolute z-score threshold of 3.0.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Review extreme standardized deviations alongside business context before removing records.

### DQ-3EE72DC2 - Outlier
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** Q1=0.08, Q3=0.23, IQR=0.15; 8 values fall outside the IQR fences.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Investigate extreme records and confirm whether they reflect genuine business events or data-entry problems.

### DQ-557ED186 - Outlier
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** 8 values exceed the absolute z-score threshold of 3.0.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Review extreme standardized deviations alongside business context before removing records.

### DQ-A8CE6CEA - Outlier
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** 7 values exceed the absolute z-score threshold of 3.0.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Review extreme standardized deviations alongside business context before removing records.

### DQ-A6ECB533 - Outlier
**Severity:** Low | **Priority:** P3 | **Status:** Open
**Evidence:** Q1=31, Q3=57, IQR=26; 6 values fall outside the IQR fences.
**Potential impact:** Rare records may be valid events or data errors and should be reviewed before exclusion or correction.
**Investigation area:** Extreme-value handling and business events
**Recommended action:** Investigate extreme records and confirm whether they reflect genuine business events or data-entry problems.

## Methodology note

The quality score is a transparent, project-specific metric. It should be interpreted alongside the underlying evidence and business context rather than treated as a universal industry standard.
