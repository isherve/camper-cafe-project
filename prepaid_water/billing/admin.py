"""Admin configuration for monitoring prepaid billing operations."""
from django.contrib import admin

from .models import Account, Customer, Tariff, Transaction, WaterUsage


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "meter_id", "rfid_card", "phone", "is_water_enabled", "created_at")
    search_fields = ("name", "meter_id", "rfid_card", "phone")
    list_filter = ("is_water_enabled", "created_at")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("customer", "balance", "updated_at")
    search_fields = ("customer__name", "customer__meter_id")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "amount", "type", "date", "reference")
    search_fields = ("customer__name", "customer__meter_id", "reference")
    list_filter = ("type", "date")


@admin.register(WaterUsage)
class WaterUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "liters", "cost", "timestamp")
    search_fields = ("customer__name", "customer__meter_id")
    list_filter = ("timestamp",)


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("id", "price_per_liter", "is_active", "effective_from")
    list_filter = ("is_active", "effective_from")
