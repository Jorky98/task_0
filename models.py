from dataclasses import dataclass
from typing import List

@dataclass
class Transaction:
    id: str
    region: str
    amount: float
    date: str


# -------- Metadata --------
@dataclass
class DateRange:
    start: str
    end: str

@dataclass
class Metadata:
    generatedAt: str
    transactionCount: int
    daysOfData: int
    dateRange: DateRange

    def __post_init__(self):
        if isinstance(self.dateRange, dict):
            self.dateRange = DateRange(**self.dateRange)
# -------- Summary --------
@dataclass
class Summary:
    totalRevenue: float
    averageOrderValue: float
    conversionRate: float
    totalCustomers: int
    refundRate: float
    topRegion: str
    topCategory: str
# -------- Customer --------
@dataclass
class Customer:
    id: str
    segment: str
    lifetimeValue: float
# -------- Transaction --------
@dataclass
class Transaction:
    id: str
    date: str
    timestamp: str
    amount: float
    product: str
    productId: str
    category: str
    region: str
    customer: Customer
    paymentMethod: str
    status: str
# -------- Daily Metric --------
@dataclass
class DailyMetric:
    date: str
    revenue: float
    orders: int
    activeUsers: int
    newUsers: int
    conversionRate: float
    averageOrderValue: float
    churnRate: float
# -------- Product --------
@dataclass
class Product:
    id: str
    name: str
    category: str
    price_range: List[float] # [min_price, max_price]
# -------- Filters --------
@dataclass
class Filters:
    availableCategories: List[str]
    availableRegions: List[str]
    availableSegments: List[str]


# -------- Root Model --------

@dataclass
class DashboardData:
    metadata: Metadata
    summary: Summary
    transactions: List[Transaction]
    dailyMetrics: List[DailyMetric]
    products: List[Product]
    regions: List[str]
    customerSegments: List[str]
    filters: Filters
