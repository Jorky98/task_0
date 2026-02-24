import datetime
import plotly.express as px
import streamlit as st
import polars as pl
import pandas as pd
from dataclasses import asdict

class KPICards:
    @staticmethod
    def render_card(label, value, delta=None, help_text=None):
        st.metric(label=label, value=value, delta=delta, help=help_text)

    def display(self, summary, trend_label):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            self.render_card("Total Revenue", f"${summary.totalRevenue:,.0f}", delta=trend_label)
        
        with c2:
            self.render_card("Avg Order Value", f"${summary.averageOrderValue:.2f}")

        with c3:
            self.render_card("Top Region", summary.topRegion)

        with c4:
            self.render_card("Top Category", summary.topCategory)

class ChartComponents:
    @staticmethod
    def line_ch(data, **kw):
        if data.is_empty(): return None
        trend = data.group_by("date").agg(pl.col("amount").sum()).sort("date")
        return px.line(trend.to_pandas(), x="date", y="amount", title=kw.get("title"))

    @staticmethod
    def pie_ch(data, **kw):
        if data.is_empty(): return None
        cat_data = data.group_by("category").agg(pl.col("amount").sum())
        return px.pie(cat_data.to_pandas(), values="amount", names="category", hole=0.4, title=kw.get("title"))

    @staticmethod
    def bar_ch(data, **kw):
        if data.is_empty(): return None
        reg_df = (
            data.group_by("region")
            .agg(pl.col("amount").sum())
            .sort("amount", descending=True)
        )
        return px.bar(
            reg_df.to_pandas(), 
            x="region", 
            y="amount", 
            title=kw.get("title"),
            color="region",
            text_auto='.2s'
        )
    
    @staticmethod
    def wrapper(figure_func, *args, **kwargs):
        title = kwargs.get("title", "Chart")
        st.subheader(title)

        placeholder = st.empty()
        placeholder.info(f"Loading {title}...")

        try:
            fig = figure_func(*args, **kwargs)
            if fig is None: 
                placeholder.warning(f"No data for {title}")
            else: 
                placeholder.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering {title}: {e}")

    def display_grid(self, df):
            self.wrapper(self.line_ch, df, title="Revenue Trend")
            st.markdown("---")

            col_l, col_r = st.columns(2)
            with col_l:
                self.wrapper(self.pie_ch, df, title="Category Share")
            with col_r:
                self.wrapper(self.bar_ch, df, title="Regional Performance")

class FilterPanel:
    def __init__(self, dm):
        self.dm = dm

    def render(self):
        st.sidebar.header("Filters")
        
        # Date Range Filter
        st.sidebar.subheader("Date Range")
        max_date = datetime.datetime.strptime(self.dm.metadata.dateRange.end, "%Y-%m-%d").date()
        min_date = datetime.datetime.strptime(self.dm.metadata.dateRange.start, "%Y-%m-%d").date()

        date_option = st.sidebar.selectbox(
            "Select Period",
            ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
        )
        
        if date_option == "All Time":
            start, end = min_date, max_date
        elif date_option == "Last 7 Days":
            start, end = max_date - datetime.timedelta(days=7), max_date
        elif date_option == "Last 30 Days":
            start, end = max_date - datetime.timedelta(days=30), max_date
        elif date_option == "Last 90 Days":
            start, end = max_date - datetime.timedelta(days=90), max_date
        else: # Custom Range
            col_from, col_to = st.sidebar.columns(2)
            start = col_from.date_input("From", min_date)
            end = col_to.date_input("To", max_date)

        st.sidebar.markdown("---")
        
        selected_regions = st.sidebar.multiselect(
            "Regions", 
            options=self.dm.filters_config.availableRegions, 
            default=self.dm.filters_config.availableRegions
        )
        selected_categories = st.sidebar.multiselect(
            "Categories", 
            options=self.dm.filters_config.availableCategories, 
            default=self.dm.filters_config.availableCategories
        )
        st.sidebar.subheader("Customer Segment")
        available_segments = self.dm.filters_config.availableSegments if hasattr(self.dm.filters_config, 'availableSegments') else ["Enterprise", "SMB", "Individual"]
        selected_segment = st.sidebar.radio(
            "Select Segment",
            options=["All"] + available_segments,
            index=0
        )
        
        return {
            "start_date": start,
            "end_date": end,
            "selected_regions": selected_regions,
            "selected_categories": selected_categories,
            "selected_segment": selected_segment
        }

class Tables:
    @staticmethod
    def render(df, summary, filtered_daily_metrics):
        t1, t2, t3 = st.tabs(["Summary", "Transactions", "Daily Metrics"])
        
        with t1:
            summary_dict = asdict(summary)
            
            labels = {
                "totalRevenue": "Total Revenue ($)",
                "averageOrderValue": "Avg. Order Value ($)",
                "conversionRate": "Conversion Rate (%)",
                "totalCustomers": "Total Active Users",
                "refundRate": "Refund Rate (%)",
                "topRegion": "Top Performing Region",
                "topCategory": "Top Selling Category"
            }
            
            formatted_data = []
            for key, value in summary_dict.items():
                label = labels.get(key, key)
                if isinstance(value, float):
                    display_value = f"{value:,.2f}"
                elif isinstance(value, int):
                    display_value = f"{value:,}"
                else:
                    display_value = str(value)

                formatted_data.append({"Metric": label, "Value": display_value})

            st.table(pd.DataFrame(formatted_data))

        with t2:
            st.subheader("Transaction Log")
            Tables._render_paged_table(df, "transactions")

        with t3:
            st.subheader("Daily Stats History")
            Tables._render_paged_table(filtered_daily_metrics, "daily_metrics")

    @staticmethod
    def _render_paged_table(data_df, key_prefix):
        total_rows = len(data_df)
        
        if total_rows > 0:
            col_size, col_page, col_info = st.columns([1, 1, 2])
            
            with col_size:
                size_options = [20, 50, 100, "Unlimited"]
                selected_size = st.selectbox("Rows per page", options=size_options, index=0, key=f"{key_prefix}_size")

            if selected_size == "Unlimited":
                if total_rows > 10000:
                    st.warning("Large dataset: Showing all rows might slow down your browser.")
                display_df = data_df
            else:
                page_size = int(selected_size)
                total_pages = max(1, (total_rows - 1) // page_size + 1)
                
                with col_page:
                    current_page = st.number_input(f"Page (1-{total_pages})", min_value=1, max_value=total_pages, value=1, key=f"{key_prefix}_page")
                
                start_idx = (current_page - 1) * page_size
                display_df = data_df.slice(start_idx, page_size)
                
                with col_info:
                    st.write(f"Showing {start_idx + 1} to {min(start_idx + page_size, total_rows)} of {total_rows}")

            st.dataframe(display_df.to_pandas(), use_container_width=True, height=500)
        else:
            st.warning("No data available for the current filters.")