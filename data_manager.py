import json
import polars as pl
from dacite import from_dict
from models import DashboardData, Transaction, Customer, DailyMetric, Product, Filters, Metadata, DateRange, Summary

class DataManager:
    def __init__(self, file_path: str):
        with open(file_path, 'r') as f:
            self.raw_data = json.load(f)
        
        self.metadata = from_dict(data_class=Metadata, data=self.raw_data['metadata'])
        self.summary = from_dict(data_class=Summary, data=self.raw_data['summary'])
        self.regions = self.raw_data.get('regions', [])
        self.customer_segments = self.raw_data.get('customerSegments', [])
        self.filters_config = from_dict(data_class=Filters, data=self.raw_data['filters'])

        self.transactions_df = pl.DataFrame(self.raw_data['transactions'])
        self.daily_metrics_df = pl.DataFrame(self.raw_data['dailyMetrics'])
        self.products_df = pl.DataFrame(self.raw_data['products'])
        
        self.transactions_df = self.transactions_df.with_columns(
            pl.col("date").str.to_date("%Y-%m-%d")
        )
        self.daily_metrics_df = self.daily_metrics_df.with_columns(
            pl.col("date").str.to_date("%Y-%m-%d")
        )