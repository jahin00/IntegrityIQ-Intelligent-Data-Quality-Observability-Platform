# Architecture

AI Data Quality Detective is organized as a layered quality-investigation pipeline.

```mermaid
flowchart TD
    A[Incoming CSV / Excel / SQLite] --> B[Ingestion]
    B --> C[Data Contract]
    B --> D[Rule Engine]
    B --> E[Statistical Engine]
    B --> F[ML Anomaly Engine]
    B --> G[SQL Quality Checks]
    C --> H[Evidence Layer]
    D --> H
    E --> H
    F --> H
    G --> H
    H --> I[Issue Intelligence]
    I --> J[Quality Scorecard]
    I --> K[Quality Gate]
    I --> L[Investigation Report]
    K --> M[Monitoring History]
    M --> N[Streamlit Trend Dashboard]
    O[GitHub Actions] --> P[Tests + Clean Batch Gate]
```

## Design principles

1. **Deterministic checks remain deterministic.** A domain rule such as `discount ∈ [0, 1]` is not delegated to machine learning.
2. **Statistical and ML findings are signals.** A shift or anomaly is not automatically a data error. Business context is required before remediation.
3. **Evidence is preserved.** Findings include method, severity, affected records, and investigation context.
4. **Rules are configurable.** Data contracts and quality thresholds live outside the Python logic.
5. **The score is transparent.** The quality scorecard is explicitly project-specific rather than presented as an industry standard.
6. **The same analysis can be monitored over time.** Each batch can be persisted and compared with prior runs.
