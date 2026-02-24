from models import Summary
import polars as pl
import streamlit as st

# Applies filters to the data
@st.cache_data
def process_and_filter(transactions_df, filters):
    # get segment from nested struct
    df = transactions_df.with_columns(
        pl.col("customer").struct.field("segment").alias("segment")
    )
    
    df = df.filter(
        (pl.col("date") >= filters["start_date"]) &
        (pl.col("date") <= filters["end_date"]) &
        (pl.col("region").is_in(filters["selected_regions"])) &
        (pl.col("category").is_in(filters["selected_categories"]))
    )
    
    if filters["selected_segment"] != "All":
        df = df.filter(pl.col("segment") == filters["selected_segment"])
        
    return df

# trend is calculated as percentage change between first and second half of the data
@st.cache_data
def get_trend(df):
    if len(df) < 2:
        return "0%"
    df_sorted = df.sort("date")
    mid = len(df_sorted) // 2
    first_half = df_sorted.head(mid)["amount"].sum()
    second_half = df_sorted.tail(len(df_sorted) - mid)["amount"].sum()
    if first_half > 0:
        trend_val = ((second_half - first_half) / first_half) * 100
        return f"{trend_val:+.1f}%"
    return "N/A"

@st.cache_data
def get_summary(df, daily_metrics_df):
    completed_df = df.filter(pl.col("status").str.to_lowercase() == "completed")
    refunds_df = df.filter(pl.col("status").str.to_lowercase() == "refunded")
    # pending_df = df.filter(pl.col("status").str.to_lowercase() == "pending")


    completed_revenue = completed_df["amount"].sum() if not completed_df.is_empty() else 0
    # pending_revenue = pending_df["amount"].sum() if not pending_df.is_empty() else 0
    refund_revenue = refunds_df["amount"].sum() if not refunds_df.is_empty() else 0
    avg_order_val = completed_df["amount"].mean() if not completed_df.is_empty() else 0

    calc_refund_rate = (refund_revenue / (completed_revenue) * 100) if (completed_revenue) > 0 else 0

    summary = Summary(
        totalRevenue=completed_revenue,
        averageOrderValue=avg_order_val,
        conversionRate=daily_metrics_df["conversionRate"].mean() if not daily_metrics_df.is_empty() else 0,
        totalCustomers=df["customer"].struct.field("id").n_unique() if "customer" in df.columns else 0,
        refundRate=calc_refund_rate,
        topRegion=completed_df.group_by("region").agg(pl.col("amount").sum()).sort("amount", descending=True).head(1)["region"][0] if not completed_df.is_empty() else "N/A",
        topCategory=completed_df.group_by("category").agg(pl.col("amount").sum()).sort("amount", descending=True).head(1)["category"][0] if not completed_df.is_empty() else "N/A"
    )

    # Re-build enriched_metrics for your charts
    daily_stats = completed_df.group_by("date").agg([
        pl.col("amount").sum().alias("revenue_filtered"),
        pl.col("amount").len().alias("orders_filtered")
    ])
    
    enriched_metrics = daily_stats.join(daily_metrics_df, on="date", how="inner").sort("date")

    return summary, enriched_metrics

@st.cache_data
def get_enriched_metrics(df, daily_metrics_df):
    daily_stats = df.group_by("date").agg([
        pl.col("amount").sum().alias("revenue_filtered"),
        pl.col("amount").len().alias("orders_filtered")
    ])
    
    enriched = (
        daily_stats
        .join(daily_metrics_df, on="date", how="inner")
        .sort("date")
    )
    
    return enriched
