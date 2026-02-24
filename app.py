import streamlit as st

from data_manager import DataManager
from utils import export_utils
from utils.ui_components import KPICards, ChartComponents, FilterPanel, Tables
import utils.data_utils as data_utils

# Init Data
@st.cache_resource
def load_data():
    return DataManager("data/kpi_dataset_small.json")
    #return DataManager("data/kpi_dataset_large.json")
data_manager = load_data()
    
kpi_ui = KPICards()
chart_ui = ChartComponents()
tables_ui = Tables()
filter_panel = FilterPanel(data_manager)

# --- FILTER PANEL ---
filters = filter_panel.render()

# --- DATA PROCESSING ---
df = data_utils.process_and_filter(data_manager.transactions_df, filters)
trend_label = data_utils.get_trend(df)

enriched_metrics = data_utils.get_enriched_metrics(df, data_manager.daily_metrics_df)
summary, enriched_metric = data_utils.get_summary(df, data_manager.daily_metrics_df)

# --- UI RENDERING ---
st.set_page_config(layout="wide", page_title="Business Performance Dashboard")
col_title, col_export = st.columns([3, 1])

with col_title:
    st.title("Business Performance Dashboard")

with col_export:
    st.write("")
    if st.button("Export Report", use_container_width=True):
        report_html = export_utils.generate_fully_interactive_report(
            data_manager, 
            df
        )
        st.download_button(
            label="Download HTML Report",
            data=report_html,
            file_name="dashboard_report.html",
            mime="text/html",
            use_container_width=True
        )
st.markdown("---")

# KPI Cards
kpi_ui.display(summary, trend_label)

# Graphs
chart_ui.display_grid(df)
st.markdown("---")

# Tables
tables_ui.render(df, summary, enriched_metrics)

# # Export Report
# if st.sidebar.button("Export Full Local Report"):
#     report_html = export_utils.generate_fully_interactive_report(
#         data_manager, 
#         df
#     )
#     st.sidebar.download_button("Download HTML Report", report_html, "dashboard.html", "text/html")