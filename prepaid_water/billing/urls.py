"""App-level API URL routes."""
from django.urls import path

from .views import (
    AccountTopupView,
    AdminReportView,
    CustomerBalanceView,
    CustomerRegisterView,
    WaterUsageIngestView,
)

urlpatterns = [
    path("customer/register", CustomerRegisterView.as_view(), name="customer-register"),
    path("account/topup", AccountTopupView.as_view(), name="account-topup"),
    path("water/usage", WaterUsageIngestView.as_view(), name="water-usage"),
    path("customer/balance", CustomerBalanceView.as_view(), name="customer-balance"),
    path("admin/report", AdminReportView.as_view(), name="admin-report"),
]
