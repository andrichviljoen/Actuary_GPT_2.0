from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ai_assistant import query_openai_compatible, is_ai_enabled
from src.ai_context import build_context_payload, save_context_json
from src.config import DEFAULT_CONFIG
from src.data_ingestion import DataIngestionError, MappingConfig, load_demo_dataset
from src.diagnostics import bootstrap_histogram, calendar_effect_series, triangle_heatmap, trend_by_origin
from src.outlier_detection import compute_link_ratio_table, flag_outliers, selected_factors
from src.reporting import generate_markdown_report
from src.reserving import run_bootstrap_odp, run_chain_ladder
from src.triangle_builder import build_triangle, triangle_to_dataframe
from src.validation import prepare_and_validate_data

st.set_page_config(page_title="IBNR Reserving Tool", layout="wide")
st.title("IBNR Reserving Tool")
st.caption("Accident Year reserving MVP with Chain Ladder, ODP Bootstrap, diagnostics, and AI-assisted reporting.")

if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "clean_df" not in st.session_state:
    st.session_state.clean_df = None
if "results" not in st.session_state:
    st.session_state.results = {}
if "context" not in st.session_state:
    st.session_state.context = {}

with st.sidebar:
    st.header("Data and Settings")
    load_mode = st.radio("Data source", ["Demo dataset", "Upload file"])
    uploaded_file = None
    if load_mode == "Upload file":
        uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx", "xls"])

    st.subheader("Model settings")
    n_sims = st.number_input("Bootstrap simulations", min_value=100, max_value=5000, value=DEFAULT_CONFIG.bootstrap_sims, step=100)
    run_bootstrap = st.checkbox("Run ODP Bootstrap", value=True)

if load_mode == "Demo dataset":
    raw_df = load_demo_dataset()
else:
    raw_df = pd.read_csv(uploaded_file) if uploaded_file and uploaded_file.name.endswith(".csv") else (pd.read_excel(uploaded_file) if uploaded_file else None)

st.session_state.raw_df = raw_df

if raw_df is not None:
    st.sidebar.subheader("Column Mapping")
    cols = raw_df.columns.tolist()
    ay_col = st.sidebar.selectbox("Accident Year", cols, index=0)
    dev_col = st.sidebar.selectbox("Development age/period", cols, index=1 if len(cols) > 1 else 0)
    val_col = st.sidebar.selectbox("Value", cols, index=2 if len(cols) > 2 else 0)

    if st.sidebar.button("Build Triangle and Run Reserving", type="primary"):
        try:
            mapping = MappingConfig(accident_year_col=ay_col, development_col=dev_col, value_col=val_col)
            clean_df = prepare_and_validate_data(raw_df, mapping)
            tri = build_triangle(clean_df, cumulative=True)
            tri_df = triangle_to_dataframe(tri)
            lr = compute_link_ratio_table(tri_df)
            flagged = flag_outliers(lr)

            exclusions_ui = []
            cl_results = run_chain_ladder(tri)
            bootstrap_results = run_bootstrap_odp(tri, n_sims=int(n_sims), random_state=DEFAULT_CONFIG.bootstrap_seed) if run_bootstrap else None

            cal = calendar_effect_series(tri_df)
            diagnostics_summary = {
                "calendar_summary": f"{int(cal['flagged'].sum())} potential calendar-year anomalies flagged (heuristic).",
                "outlier_summary": f"{int(flagged['flagged'].sum())} link-ratio candidates flagged.",
            }

            payload = build_context_payload(
                mapping={"accident_year": ay_col, "development": dev_col, "value": val_col},
                settings={"bootstrap_sims": int(n_sims), "run_bootstrap": run_bootstrap},
                diagnostics={**diagnostics_summary, "calendar": cal, "link_ratio_flags": flagged},
                chain_ladder={
                    "summary": cl_results["summary"],
                    "total_reserve": cl_results["total_reserve"],
                    "selected_factors": selected_factors(lr, exclusions_ui),
                    "ldf": cl_results["ldf"],
                },
                bootstrap=bootstrap_results,
                exclusions=exclusions_ui,
            )
            context_path = save_context_json(payload, Path("sample_outputs/latest_context.json"))

            st.session_state.clean_df = clean_df
            st.session_state.results = {
                "triangle": tri,
                "triangle_df": tri_df,
                "link_ratios": lr,
                "flagged": flagged,
                "chain_ladder": cl_results,
                "bootstrap": bootstrap_results,
                "calendar": cal,
            }
            st.session_state.context = payload
            st.success(f"Model run complete. Context saved to {context_path}")
        except DataIngestionError as e:
            st.error(str(e))
        except Exception as e:  # pragma: no cover
            st.exception(e)

tabs = st.tabs(["Data", "Triangle", "Diagnostics", "Chain Ladder Results", "Bootstrap Results", "AI Assistant", "Report"])

with tabs[0]:
    st.subheader("Data")
    if raw_df is None:
        st.info("Load the demo dataset or upload your file to begin.")
    else:
        st.dataframe(raw_df.head(200), use_container_width=True)
        st.download_button("Download preview CSV", raw_df.to_csv(index=False), "raw_preview.csv")
        st.markdown("Demo dataset is from `chainladder.load_sample('genins')`, converted to long Accident Year format.")

with tabs[1]:
    st.subheader("Development Triangle")
    if st.session_state.results:
        tri_df = st.session_state.results["triangle_df"]
        st.dataframe(tri_df, use_container_width=True)
        st.plotly_chart(triangle_heatmap(tri_df, "Incurred Triangle Heatmap"), use_container_width=True)

with tabs[2]:
    st.subheader("Diagnostics")
    if st.session_state.results:
        tri_df = st.session_state.results["triangle_df"]
        flagged = st.session_state.results["flagged"]
        st.plotly_chart(trend_by_origin(tri_df), use_container_width=True)
        st.dataframe(flagged, use_container_width=True)
        st.plotly_chart(triangle_heatmap(flagged.pivot(index="origin", columns="dev_from", values="link_ratio").reset_index().fillna(0), "Link Ratio Heatmap"), use_container_width=True)
        st.dataframe(st.session_state.results["calendar"], use_container_width=True)

with tabs[3]:
    st.subheader("Chain Ladder Results")
    if st.session_state.results:
        cl_res = st.session_state.results["chain_ladder"]
        st.metric("Total IBNR", f"{cl_res['total_reserve']:,.2f}")
        st.dataframe(cl_res["summary"], use_container_width=True)
        st.subheader("LDF (selected by Chainladder)")
        st.dataframe(cl_res["ldf"], use_container_width=True)

with tabs[4]:
    st.subheader("Bootstrap Results")
    if st.session_state.results:
        boot = st.session_state.results["bootstrap"]
        if boot:
            st.dataframe(boot["summary"], use_container_width=True)
            st.plotly_chart(bootstrap_histogram(boot["samples"]), use_container_width=True)
        else:
            st.info("Bootstrap not run.")

with tabs[5]:
    st.subheader("AI Assistant")
    st.caption("Advisory only; not a substitute for actuarial judgment.")
    question = st.text_input("Ask a question", value="What is driving the reserve?")
    if st.button("Run AI Assistant"):
        if not st.session_state.context:
            st.warning("Run reserving first.")
        else:
            response = query_openai_compatible(st.session_state.context, question)
            st.markdown(response)
    if not is_ai_enabled():
        st.info("AI disabled (OPENAI_API_KEY missing). Core calculations remain available.")

with tabs[6]:
    st.subheader("Report")
    if st.session_state.context:
        report_md = generate_markdown_report(st.session_state.context)
        st.markdown(report_md)
        st.download_button("Download Markdown report", report_md, "ibnr_report.md")
        st.download_button(
            "Download JSON context",
            json.dumps(st.session_state.context, default=str, indent=2),
            "ibnr_context.json",
        )
