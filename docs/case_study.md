# Portfolio Case Study: Retail Transaction Quality Incident

## Scenario

A retail analytics team receives a new transaction batch and needs to decide whether it is safe to use for KPI reporting and downstream analysis.

The project intentionally injects realistic quality defects so the investigation workflow can be demonstrated end to end.

## Dataset

- 5,012 transaction rows
- 11 columns
- Reference batch available for distribution comparison
- Deliberate issues include missingness, duplicates, category variants, invalid values, date anomalies, statistical outliers, and distribution shifts

## Investigation result

| Metric | Demo result |
|---|---:|
| Overall quality score | 85.09 / 100 |
| Total findings | 24 |
| Critical / High findings | 8 |
| Quality gate | FAIL |
| Critical contract violations | 1 |
| High contract violations | 4 |

### Quality dimensions

| Dimension | Score |
|---|---:|
| Completeness | 99.68 |
| Consistency | 34.92 |
| Validity | 93.24 |
| Uniqueness | 99.52 |
| Timeliness | 99.66 |

The low consistency score is driven primarily by category inconsistencies and dataset-level distribution-shift signals. Those findings require contextual investigation rather than automatic correction.

## Example findings

### 1. Duplicate primary key

A transaction identifier appears multiple times. This can cause double-counting and unreliable joins.

**Investigation area:** transaction ID generation and ingestion deduplication.

### 2. Invalid discount

Discount values fall outside the configured business domain.

**Investigation area:** source-system validation and transformation logic.

### 3. Distribution shift

The current batch differs statistically from the reference batch for selected fields.

**Investigation area:** determine whether the shift reflects a real change in customer behavior, product mix, source-system behavior, or a pipeline defect.

### 4. ML anomalies

Isolation Forest identifies multivariate records that are unusual relative to the batch.

**Investigation area:** review flagged transactions before deciding whether they are true errors, rare legitimate events, or edge cases.

## Why this is useful

The project demonstrates a complete analytical workflow:

`detect → quantify → explain → prioritize → investigate → monitor`

That is the core story to emphasize in a portfolio or interview, rather than presenting the project as only an anomaly-detection exercise.
