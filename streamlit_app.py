from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.anomaly.detector import detect_isolation_forest_anomalies
from src.ingestion.loaders import load_file
from src.profiling.basic import detect_exact_duplicates, detect_missing_values, profile_dataframe
from src.profiling.rules import (
    detect_category_inconsistencies,
    detect_date_anomalies,
    detect_domain_violations,
)
from src.profiling.statistics import (
    detect_distribution_shift,
    detect_iqr_outliers,
    detect_zscore_outliers,
)
from src.reporting.intelligence import (
    build_markdown_report,
    build_issue_register,
)
from src.scoring.quality_score import calculate_quality_scorecard
from src.contracts import load_contract, quality_gate, validate_contract
from src.monitoring.history import (
    compare_latest_runs,
    fingerprint_dataframe,
    load_quality_history,
    record_quality_run,
)
from src.monitoring.pipeline import run_quality_analysis
from src.sql.quality_checks import (
    create_sqlite_engine,
    fetch_table,
    list_tables,
    null_violations,
    orphan_records,
    primary_key_duplicates,
    reconciliation_check,
    value_rule_violations,
)

st.set_page_config(
    page_title="IntegrityIQ",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Visual system
# -----------------------------------------------------------------------------
CSS = """
<style>
:root {
    --bg: #0b1220;
    --panel: #111a2b;
    --panel-2: #162238;
    --border: rgba(148, 163, 184, 0.16);
    --muted: #94a3b8;
    --text: #f8fafc;
    --blue: #5b8def;
    --cyan: #38bdf8;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
    --purple: #a78bfa;
}

.stApp {
    background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(139, 92, 246, 0.10), transparent 24%),
                #0a101c;
    color: var(--text);
}

[data-testid="stHeader"] {
    background: rgba(10, 16, 28, 0.78);
}

[data-testid="stSidebar"] {
    background: #0b1322;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.2rem;
}

[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(22,34,56,0.96), rgba(17,26,43,0.96));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 12px 14px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}

[data-testid="stMetricLabel"] {
    color: var(--muted);
}

[data-testid="stMetricValue"] {
    color: var(--text);
    font-weight: 700;
}

div[data-testid="stTabs"] button {
    border-radius: 10px 10px 0 0;
}

.stButton > button, .stDownloadButton > button {
    border-radius: 10px;
    border: 1px solid rgba(148,163,184,0.22);
    background: #15233a;
    color: #f8fafc;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: rgba(91,141,239,0.55);
    background: #1b2d4a;
}

.section-title {
    font-size: 1.18rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0.55rem 0 0.35rem;
}

.section-subtitle {
    color: #94a3b8;
    font-size: 0.90rem;
    margin-bottom: 0.8rem;
}

.hero {
    background: linear-gradient(135deg, rgba(18,32,54,0.96), rgba(22,34,56,0.92));
    border: 1px solid rgba(91,141,239,0.20);
    border-radius: 22px;
    padding: 24px 26px;
    margin-bottom: 18px;
    box-shadow: 0 18px 42px rgba(0,0,0,0.18);
}

.hero-kicker {
    color: #7dd3fc;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    font-weight: 700;
}

.hero-title {
    font-size: 2.1rem;
    line-height: 1.08;
    font-weight: 800;
    margin-top: 7px;
    color: #ffffff;
}

.hero-copy {
    color: #b6c2d4;
    max-width: 780px;
    margin-top: 9px;
    font-size: 0.98rem;
}

.badge {
    display: inline-block;
    padding: 0.22rem 0.58rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 750;
    letter-spacing: 0.02em;
    border: 1px solid rgba(255,255,255,0.10);
}

.badge-pass { background: rgba(34,197,94,0.13); color: #86efac; }
.badge-warning { background: rgba(245,158,11,0.13); color: #fcd34d; }
.badge-fail { background: rgba(239,68,68,0.13); color: #fca5a5; }
.badge-critical { background: rgba(239,68,68,0.13); color: #fecaca; }
.badge-high { background: rgba(249,115,22,0.13); color: #fdba74; }
.badge-medium { background: rgba(245,158,11,0.13); color: #fde68a; }
.badge-low { background: rgba(34,197,94,0.10); color: #bbf7d0; }

.card {
    background: linear-gradient(180deg, rgba(17,26,43,0.98), rgba(15,24,40,0.98));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 18px;
    box-shadow: 0 10px 26px rgba(0,0,0,0.12);
}

.card-title {
    color: #cbd5e1;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-weight: 700;
}

.card-value {
    color: #ffffff;
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 7px;
}

.card-note {
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 2px;
}

.score-panel {
    background: linear-gradient(135deg, rgba(17,26,43,0.98), rgba(20,31,50,0.98));
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.16);
}

.score-gauge {
    width: 168px;
    height: 168px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    margin: 4px auto 10px;
    position: relative;
}

.score-gauge::before {
    content: "";
    width: 124px;
    height: 124px;
    border-radius: 50%;
    background: #0b1220;
    position: absolute;
}

.score-gauge-inner {
    position: relative;
    text-align: center;
    z-index: 1;
}

.score-value {
    color: #fff;
    font-size: 2rem;
    font-weight: 850;
    line-height: 1;
}

.score-label {
    color: #94a3b8;
    font-size: 0.72rem;
    margin-top: 5px;
}

.small-muted { color: #94a3b8; font-size: 0.82rem; }

.issue-card {
    background: linear-gradient(180deg, rgba(20,31,50,0.95), rgba(15,24,40,0.95));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    margin: 8px 0;
}

.issue-id {
    color: #7dd3fc;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.04em;
}

.issue-title {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 750;
    margin: 4px 0 8px;
}

.issue-meta {
    color: #94a3b8;
    font-size: 0.78rem;
}

.divider {
    height: 1px;
    background: var(--border);
    margin: 16px 0;
}

[data-testid="stFileUploader"] {
    background: rgba(17,26,43,0.68);
    border-radius: 12px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def badge(label: str, kind: str) -> str:
    cls = {
        "PASS": "badge-pass",
        "WARNING": "badge-warning",
        "FAIL": "badge-fail",
        "Critical": "badge-critical",
        "High": "badge-high",
        "Medium": "badge-medium",
        "Low": "badge-low",
    }.get(label, "badge-warning")
    return f'<span class="badge {cls}">{label}</span>'


def score_label(score: float) -> tuple[str, str]:
    if score >= 90:
        return "Strong", "PASS"
    if score >= 75:
        return "Watch", "WARNING"
    return "Needs investigation", "FAIL"


def score_gauge(score: float) -> str:
    score = max(0.0, min(100.0, float(score)))
    color = "#22c55e" if score >= 90 else "#f59e0b" if score >= 75 else "#ef4444"
    degrees = score * 3.6
    return f"""
    <div class="score-panel">
      <div class="score-gauge" style="background: conic-gradient({color} 0deg {degrees:.1f}deg, rgba(148,163,184,0.12) {degrees:.1f}deg 360deg);">
        <div class="score-gauge-inner">
          <div class="score-value">{score:.1f}</div>
          <div class="score-label">QUALITY SCORE</div>
        </div>
      </div>
      <div style="text-align:center;">{badge(score_label(score)[1], '')}<div class="small-muted" style="margin-top:7px;">{score_label(score)[0]}</div></div>
    </div>
    """


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Sidebar: data, navigation, controls
# -----------------------------------------------------------------------------
with open(ROOT / "config.yaml", "r", encoding="utf-8") as fh:
    config = yaml.safe_load(fh)
with open(ROOT / "config_sql.yaml", "r", encoding="utf-8") as fh:
    sql_config = yaml.safe_load(fh)

st.sidebar.markdown(
    "<div style='font-size:0.72rem;color:#7dd3fc;font-weight:750;letter-spacing:0.12em;'>DATA OBSERVABILITY</div>"
    "<div style='font-size:1.35rem;color:#fff;font-weight:850;margin-top:4px;'>AI Data Quality<br>Detective</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown('<div class="divider"></div>', unsafe_allow_html=True)

with st.sidebar.expander("📂 Data Sources", expanded=True):
    uploaded = st.file_uploader("Current dataset", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
    reference_uploaded = st.file_uploader(
        "Reference / historical dataset",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )
    sql_uploaded = st.file_uploader(
        "SQLite database",
        type=["db", "sqlite", "sqlite3"],
        label_visibility="collapsed",
    )

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Overview",
        "Investigation Report",
        "Quality Score",
        "Monitoring & Trends",
        "Data Profile",
        "Statistical Detection",
        "Record Evidence",
        "SQL Monitoring",
        "Data Contract",
    ],
)

with st.sidebar.expander("ℹ️ Project Notes"):
    st.caption("Rule-based validation + statistical tests + ML anomaly detection + SQL monitoring")
    st.caption("Use the demo data first, then replace it with your own batch.")

# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------
if uploaded is None:
    demo_path = ROOT / "data" / "raw" / "retail_transactions_dirty.csv"
    dataset_name = demo_path.name
    if demo_path.exists():
        df = pd.read_csv(demo_path, low_memory=False)
    else:
        st.error("Demo dataset not found. Run: python src/utils/generate_dirty_data.py")
        st.stop()
else:
    temp_path = ROOT / "data" / "processed" / uploaded.name
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(uploaded.getbuffer())
    dataset_name = uploaded.name
    df = load_file(temp_path)

if reference_uploaded is not None:
    reference_path = ROOT / "data" / "processed" / f"reference_{reference_uploaded.name}"
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_bytes(reference_uploaded.getbuffer())
    reference_df = load_file(reference_path)
else:
    demo_reference = ROOT / "data" / "raw" / "retail_transactions_reference.csv"
    reference_df = pd.read_csv(demo_reference, low_memory=False) if demo_reference.exists() else None

contract_default = load_contract(ROOT / "data_contract.yaml")
analysis = run_quality_analysis(
    df,
    config,
    reference_df=reference_df,
    contract=contract_default,
    dataset_name=dataset_name,
)

profile = analysis["profile"]
missing = analysis["missing"]
duplicates = analysis["duplicates"]
iqr_summary = analysis["iqr_summary"]
z_summary = analysis["z_summary"]
shift_summary = analysis["shift_summary"]
ml_summary = analysis["ml_summary"]
evidence = analysis["evidence"]
scorecard = analysis["scorecard"]
overall_quality_score = analysis["overall_quality_score"]
issue_register = analysis["issue_register"]
summary = analysis["summary"]
contract_results_default = analysis["contract_results"]
gate_default = analysis["gate"]
report_markdown = build_markdown_report(
    issue_register,
    scorecard,
    overall_quality_score,
    dataset_name,
    len(df),
    len(df.columns),
)

# -----------------------------------------------------------------------------
# Global context header
# -----------------------------------------------------------------------------
gate_text = str(gate_default["status"])
score_name, score_status = score_label(overall_quality_score)

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">Data Observability / Quality Intelligence</div>
      <div class="hero-title">Your dataset, under investigation.</div>
      <div class="hero-copy">Detect, quantify, prioritize, and explain data-quality problems across files and SQL tables. The dashboard combines deterministic rules, statistical evidence, and machine-learning anomaly signals in one workflow.</div>
      <div style="margin-top:13px;">{badge(gate_text, '')}&nbsp;&nbsp;<span class="small-muted">{dataset_name} · {len(df):,} rows · {len(df.columns):,} columns</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Overview
# -----------------------------------------------------------------------------
if page == "Overview":
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Quality score", f"{overall_quality_score:.1f}/100")
    m2.metric("Open findings", f"{summary['open_findings']:,}")
    m3.metric("Critical / High", f"{summary['critical_high_findings']:,}")
    m4.metric("Evidence rows", f"{len(evidence):,}")
    m5.metric("Contract violations", f"{len(contract_results_default):,}")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    left, mid, right = st.columns([1.05, 1.65, 1.65])
    with left:
        st.markdown(score_gauge(overall_quality_score), unsafe_allow_html=True)
    with mid:
        section("Investigation snapshot", "Where the current batch needs attention")
        if issue_register.empty:
            st.success("No configured quality issues detected.")
        else:
            critical = issue_register[issue_register["severity"].isin(["Critical", "High"])]
            medium = issue_register[issue_register["severity"] == "Medium"]
            low = issue_register[issue_register["severity"] == "Low"]
            st.markdown(
                f"<div class='card'><div class='card-title'>Priority mix</div>"
                f"<div class='card-value'>{len(critical)} critical/high</div>"
                f"<div class='card-note'>{len(medium)} medium · {len(low)} low findings</div></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='card' style='margin-top:10px;'><div class='card-title'>ML signal</div>"
                f"<div class='card-value'>{len(ml_summary):,}</div>"
                f"<div class='card-note'>configured anomaly groups flagged by Isolation Forest</div></div>",
                unsafe_allow_html=True,
            )
    with right:
        section("Quality dimensions", "Current score by dimension")
        for _, row in scorecard.iterrows():
            dim = str(row.iloc[0])
            val = float(row.iloc[1])
            st.progress(min(max(val / 100, 0), 1), text=f"{dim.replace('_', ' ').title()} · {val:.1f}")

    section("Top investigation items", "Highest-severity findings first")
    if issue_register.empty:
        st.info("No findings to investigate.")
    else:
        for _, row in issue_register.sort_values(["severity", "affected_count"], ascending=[True, False]).head(6).iterrows():
            severity = str(row["severity"])
            st.markdown(
                f"""
                <div class="issue-card">
                  <div class="issue-id">{row['issue_id']} · {row['priority']}</div>
                  <div class="issue-title">{row['issue_type']} <span style='color:#64748b;'>·</span> {row['column']}</div>
                  <div>{badge(severity, '')}</div>
                  <div class="issue-meta" style='margin-top:7px;'>{row['affected_count']:,} affected · {float(row['affected_pct']):.2f}% · {row['method']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("Preview current dataset"):
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Investigation report
# -----------------------------------------------------------------------------
elif page == "Investigation Report":
    section("Investigation Report", "Turn detector output into prioritized incidents with evidence and next actions")
    col_a, col_b, col_c = st.columns(3)
    severities = ["Critical", "High", "Medium", "Low"]
    dimensions = sorted(issue_register["dimension"].dropna().unique().tolist()) if not issue_register.empty else []
    with col_a:
        severity_filter = st.multiselect("Severity", severities, default=severities)
    with col_b:
        dimension_filter = st.multiselect("Dimension", dimensions, default=dimensions)
    with col_c:
        max_items = st.number_input("Items to show", min_value=5, max_value=50, value=15, step=5)

    filtered = issue_register.copy()
    if not filtered.empty:
        filtered = filtered[filtered["severity"].isin(severity_filter)]
        filtered = filtered[filtered["dimension"].isin(dimension_filter)]
        filtered = filtered.head(int(max_items))

    st.markdown(f"**{len(filtered):,} findings** match the current filters.")
    if filtered.empty:
        st.info("No findings match the current filters.")
    else:
        for _, row in filtered.iterrows():
            with st.expander(f"{row['issue_id']}  ·  {row['issue_type']}  ·  {row['column']}"):
                a, b, c, d = st.columns(4)
                a.metric("Severity", str(row["severity"]))
                b.metric("Priority", str(row["priority"]))
                c.metric("Affected", f"{int(row['affected_count']):,}")
                d.metric("Affected %", f"{float(row['affected_pct']):.2f}%")
                st.write(f"**Evidence:** {row['evidence']}")
                st.write(f"**Potential impact:** {row['potential_impact']}")
                st.write(f"**Investigation area:** {row['investigation_area']}")
                st.write(f"**Recommended action:** {row['recommendation']}")

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("Export issue register", issue_register.to_csv(index=False).encode(), "data_quality_issue_register.csv", "text/csv")
    with dl2:
        st.download_button("Export investigation report", report_markdown.encode(), "data_quality_investigation_report.md", "text/markdown")

# -----------------------------------------------------------------------------
# Scorecard
# -----------------------------------------------------------------------------
elif page == "Quality Score":
    left, right = st.columns([1, 2])
    with left:
        st.markdown(score_gauge(overall_quality_score), unsafe_allow_html=True)
    with right:
        section("Quality scorecard", "Transparent, configurable scoring across five dimensions")
        st.dataframe(scorecard, use_container_width=True, hide_index=True)
        st.caption("90–100: Strong · 75–89.99: Watch · below 75: Needs investigation")
        st.info("The score is a project-specific metric. It is intended for monitoring and comparison, not as a universal industry standard.")

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------
elif page == "Monitoring & Trends":
    section("Historical Quality Monitoring", "Track batch quality over time and spot regressions")
    history_path = ROOT / "data" / "monitoring" / "quality_history.db"
    history = load_quality_history(history_path, limit=100)

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Record current batch", type="primary", use_container_width=True):
            run_id = record_quality_run(
                history_path,
                dataset_name=dataset_name,
                dataset_hash=fingerprint_dataframe(df),
                row_count=len(df),
                column_count=len(df.columns),
                quality_score=overall_quality_score,
                gate_status=gate_default["status"],
                total_findings=summary["total_findings"],
                critical_high_findings=summary["critical_high_findings"],
                p0_findings=int((issue_register["priority"] == "P0").sum()) if not issue_register.empty else 0,
                contract_violations=len(contract_results_default),
                scorecard=scorecard,
            )
            st.success(f"Recorded run {run_id}")
            history = load_quality_history(history_path, limit=100)
    with c2:
        st.caption("Run history is stored locally in data/monitoring/quality_history.db")

    if history.empty:
        st.info("No historical runs recorded yet.")
    else:
        latest = history.sort_values("run_at").iloc[-1]
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Latest score", f"{float(latest['quality_score']):.1f}")
        h2.metric("Latest gate", str(latest["gate_status"]))
        h3.metric("Latest findings", f"{int(latest['total_findings']):,}")
        h4.metric("Recorded runs", f"{len(history):,}")

        comparison = compare_latest_runs(history)
        if comparison.get("available"):
            st.metric("Score change vs previous run", f"{comparison['score_delta']:+.2f}")
            if comparison["gate_changed"]:
                st.warning(f"Quality gate changed from {comparison['previous_gate']} to {comparison['latest_gate']}.")

        section("Quality trend")
        trend = history.sort_values("run_at").set_index("run_at")[[
            "quality_score", "completeness_score", "consistency_score", "validity_score", "uniqueness_score", "timeliness_score"
        ]]
        st.line_chart(trend)
        section("Run history")
        st.dataframe(history[[
            "run_id", "run_at", "dataset_name", "quality_score", "gate_status",
            "total_findings", "critical_high_findings", "p0_findings", "contract_violations",
        ]], use_container_width=True, hide_index=True)
        st.download_button("Export monitoring history", history.to_csv(index=False).encode(), "quality_monitoring_history.csv", "text/csv")

# -----------------------------------------------------------------------------
# Profile
# -----------------------------------------------------------------------------
elif page == "Data Profile":
    section("Data Profile", "A compact view of structure, completeness, and duplication")
    st.dataframe(profile, use_container_width=True, hide_index=True)
    a, b = st.columns(2)
    with a:
        section("Missing values")
        st.dataframe(missing, use_container_width=True, hide_index=True)
    with b:
        section("Exact duplicate summary")
        st.json(duplicates)
    section("Dataset preview")
    st.dataframe(df.head(30), use_container_width=True, hide_index=True)
    with st.expander("Full descriptive statistics"):
        st.dataframe(df.describe(include="all").transpose(), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Statistical detection
# -----------------------------------------------------------------------------
elif page == "Statistical Detection":
    section("Statistical Detection", "Robust outliers, distribution shift, and multivariate anomaly signals")
    a, b = st.columns(2)
    with a:
        section("Point anomalies")
        outlier_view = pd.concat([iqr_summary, z_summary], ignore_index=True)
        if outlier_view.empty:
            st.success("No configured statistical outliers detected.")
        else:
            st.dataframe(outlier_view, use_container_width=True, hide_index=True)
    with b:
        section("Distribution shift")
        if reference_df is None:
            st.info("Upload a historical/reference dataset to enable shift detection.")
        elif shift_summary.empty:
            st.success("No configured distribution shifts exceeded thresholds.")
        else:
            st.dataframe(shift_summary, use_container_width=True, hide_index=True)
    section("Machine-learning anomaly signal")
    st.caption("Isolation Forest identifies unusual multivariate numeric patterns. Treat these as candidate anomalies, not automatic data errors.")
    if ml_summary.empty:
        st.success("No ML anomaly groups detected.")
    else:
        st.dataframe(ml_summary, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Evidence
# -----------------------------------------------------------------------------
elif page == "Record Evidence":
    section("Record-Level Evidence", "Rows associated with deterministic or statistical findings")
    if evidence.empty:
        st.info("No record-level evidence to display.")
    else:
        st.caption(f"Showing up to 1,000 of {len(evidence):,} evidence records")
        st.dataframe(evidence.head(1000), use_container_width=True, hide_index=True, height=560)
        st.download_button("Export evidence", evidence.to_csv(index=False).encode(), "data_quality_record_evidence.csv", "text/csv")

# -----------------------------------------------------------------------------
# SQL
# -----------------------------------------------------------------------------
elif page == "SQL Monitoring":
    section("SQL Data Quality Monitoring", "Run relational integrity checks directly against a SQLite database")
    if sql_uploaded is not None:
        sql_db_path = ROOT / "data" / "processed" / sql_uploaded.name
        sql_db_path.parent.mkdir(parents=True, exist_ok=True)
        sql_db_path.write_bytes(sql_uploaded.getbuffer())
    else:
        demo_db = ROOT / "data" / "sql" / "retail_quality_demo.db"
        sql_db_path = demo_db if demo_db.exists() else None

    if sql_db_path is None:
        st.info("Generate the SQL demo database with: python src/utils/generate_sql_demo.py")
    else:
        engine = create_sqlite_engine(str(sql_db_path))
        tables = list_tables(engine)
        if not tables:
            st.warning("No user tables were found in the SQLite database.")
        else:
            selected_table = st.selectbox("Table", tables)
            table_df = fetch_table(engine, selected_table, limit=1000)
            full_table = fetch_table(engine, selected_table)
            row_count = len(full_table)
            st.caption(f"{selected_table} · {row_count:,} rows")
            st.dataframe(table_df, use_container_width=True, hide_index=True, height=380)

            sql_spec = sql_config.get("sql", {})
            primary_key = sql_spec.get("primary_keys", {}).get(selected_table)
            required_columns = sql_spec.get("required_columns", {}).get(selected_table, [])
            value_rules = sql_spec.get("value_rules", {}).get(selected_table, {})
            health = [{"check": "Row count", "affected_count": 0, "affected_pct": 0.0, "severity": "Info"}]
            sql_register_rows = []

            if primary_key:
                pk_dupes = primary_key_duplicates(engine, selected_table, [primary_key])
                affected = int(pk_dupes["occurrences"].sum()) if not pk_dupes.empty else 0
                pct = round(affected / row_count * 100, 2) if row_count else 0.0
                health.append({"check": f"Duplicate primary-key records ({primary_key})", "affected_count": affected, "affected_pct": pct, "severity": "High" if affected else "None"})
                if affected:
                    sql_register_rows.append({"issue_type": "Duplicate Primary Key", "method": "SQL GROUP BY", "column": primary_key, "severity": "High", "affected_count": affected, "affected_pct": pct, "evidence": f"{len(pk_dupes):,} duplicated {primary_key} values account for {affected:,} records.", "recommendation": "Trace the key-generation and ingestion process and enforce uniqueness at the target layer."})
            else:
                pk_dupes = None

            nulls = null_violations(engine, selected_table, required_columns) if required_columns else pd.DataFrame()
            for _, row in nulls.iterrows():
                affected = int(row["null_or_blank_count"])
                pct = round(affected / row_count * 100, 2) if row_count else 0.0
                health.append({"check": f"Required-field nulls ({row['column']})", "affected_count": affected, "affected_pct": pct, "severity": "High" if affected else "None"})
                if affected:
                    sql_register_rows.append({"issue_type": "Required Field Null", "method": "SQL null/blank check", "column": row["column"], "severity": "High", "affected_count": affected, "affected_pct": pct, "evidence": f"{affected:,} required-field records are null or blank.", "recommendation": "Validate required fields before loading into the target table."})

            rule_violations = value_rule_violations(engine, selected_table, value_rules) if value_rules else pd.DataFrame()
            for _, row in rule_violations.iterrows():
                affected = int(row["violation_count"])
                pct = round(affected / row_count * 100, 2) if row_count else 0.0
                health.append({"check": f"Value-rule violations ({row['column']})", "affected_count": affected, "affected_pct": pct, "severity": "High" if affected else "None"})
                if affected:
                    sql_register_rows.append({"issue_type": "Rule Violation", "method": "SQL value rule", "column": row["column"], "severity": "High", "affected_count": affected, "affected_pct": pct, "evidence": f"{affected:,} records violate the configured SQL value rule.", "recommendation": "Validate the source domain and enforce the rule before downstream reporting."})

            foreign_keys = [x for x in sql_spec.get("foreign_keys", []) if x.get("child_table") == selected_table]
            orphan_results = []
            for fk in foreign_keys:
                orphan_df = orphan_records(engine, fk["child_table"], fk["child_key"], fk["parent_table"], fk["parent_key"])
                orphan_results.append((fk, orphan_df))
                affected = len(orphan_df)
                pct = round(affected / row_count * 100, 2) if row_count else 0.0
                if affected:
                    sql_register_rows.append({"issue_type": "Referential Integrity", "method": "SQL LEFT JOIN", "column": fk["child_key"], "severity": "High", "affected_count": affected, "affected_pct": pct, "evidence": f"{affected:,} child records have no matching parent key in {fk['parent_table']}.{fk['parent_key']}.", "recommendation": "Investigate missing master-data records or broken ETL joins before downstream use."})

            reconciliation_results = []
            for rec in [x for x in sql_spec.get("reconciliation", []) if x.get("table") == selected_table]:
                recon_df = reconciliation_check(engine, selected_table, rec["expected_column"], rec["actual_column"], rec.get("tolerance", 0.01))
                reconciliation_results.append((rec, recon_df))
                affected = len(recon_df)
                pct = round(affected / row_count * 100, 2) if row_count else 0.0
                if affected:
                    sql_register_rows.append({"issue_type": "Reconciliation", "method": "Expected vs actual", "column": f"{rec['expected_column']} vs {rec['actual_column']}", "severity": "High", "affected_count": affected, "affected_pct": pct, "evidence": f"{affected:,} records exceed the configured reconciliation tolerance of {rec.get('tolerance', 0.01)}.", "recommendation": "Trace transformation, calculation, and aggregation logic between expected and actual values."})

            section("SQL health", "Configured checks against the selected relational table")
            st.dataframe(pd.DataFrame(health), use_container_width=True, hide_index=True)

            sql_register = build_issue_register(pd.DataFrame(sql_register_rows))
            section("SQL investigation queue")
            if sql_register.empty:
                st.success("No configured SQL quality issues detected in the selected table.")
            else:
                st.dataframe(sql_register, use_container_width=True, hide_index=True)
                st.download_button("Export SQL issue register", sql_register.to_csv(index=False).encode(), f"sql_quality_issue_register_{selected_table}.csv", "text/csv")

            with st.expander("Detailed SQL evidence"):
                if pk_dupes is not None:
                    st.markdown("**Duplicate keys**")
                    st.dataframe(pk_dupes, use_container_width=True, hide_index=True)
                if not nulls.empty:
                    st.markdown("**Required-field nulls**")
                    st.dataframe(nulls, use_container_width=True, hide_index=True)
                if not rule_violations.empty:
                    st.markdown("**Value-rule violations**")
                    st.dataframe(rule_violations, use_container_width=True, hide_index=True)
                for fk, orphan_df in orphan_results:
                    st.markdown(f"**Referential integrity: {fk['child_key']} → {fk['parent_table']}.{fk['parent_key']}**")
                    st.dataframe(orphan_df.head(500), use_container_width=True, hide_index=True)
                for rec, recon_df in reconciliation_results:
                    st.markdown(f"**Reconciliation: {rec['expected_column']} vs {rec['actual_column']}**")
                    st.dataframe(recon_df.head(500), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# Contract
# -----------------------------------------------------------------------------
elif page == "Data Contract":
    section("Data Contract & Quality Gate", "Validate a batch against explicit schema and quality expectations before downstream use")
    contract_path = st.text_input("Contract file", "data_contract.yaml")
    try:
        contract_cfg = load_contract(contract_path)
        contract_results = validate_contract(df, contract_cfg)
        gate = quality_gate(
            overall_quality_score,
            contract_results,
            issue_df=issue_register,
            thresholds=contract_cfg.get("quality_gate", {}),
        )
        g1, g2, g3 = st.columns(3)
        g1.metric("Quality gate", gate["status"])
        g2.metric("Contract violations", len(contract_results))
        g3.metric("Quality score", f"{overall_quality_score:.2f}/100")
        if gate["status"] == "PASS":
            st.success("PASS: " + " ".join(gate["reasons"]))
        elif gate["status"] == "WARNING":
            st.warning("WARNING: " + " ".join(gate["reasons"]))
        else:
            st.error("FAIL: " + " ".join(gate["reasons"]))
        if contract_results.empty:
            st.success("No contract violations detected.")
        else:
            st.dataframe(contract_results, use_container_width=True, hide_index=True)
            st.download_button("Export contract violations", contract_results.to_csv(index=False).encode(), "data_contract_violations.csv", "text/csv")
    except FileNotFoundError:
        st.warning(f"Contract file not found: {contract_path}")
