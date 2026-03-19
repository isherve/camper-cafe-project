"""Database models for prepaid water billing domain."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Customer(models.Model):
    """Stores customer profile and meter identification details."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        null=True,
        blank=True,
        help_text="Optional login account for customer portal access.",
    )
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    meter_id = models.CharField(max_length=60, unique=True)
    rfid_card = models.CharField(max_length=100, unique=True)
    is_water_enabled = models.BooleanField(
        default=True,
        help_text="Flag used to disable supply automatically when balance is depleted.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.meter_id})"


class Account(models.Model):
    """Prepaid wallet attached to exactly one customer."""

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.customer.name} - balance {self.balance}"


class Tariff(models.Model):
    """Defines the active pricing per liter for water usage."""

    price_per_liter = models.DecimalField(max_digits=10, decimal_places=4)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_from"]

    def save(self, *args, **kwargs):
        # Ensure only one tariff is active at a time.
        if self.is_active:
            Tariff.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.price_per_liter} RWF/L"


class Transaction(models.Model):
    """Tracks all customer wallet events: topups and usage deductions."""

    TOPUP = "topup"
    DEDUCTION = "deduction"
    TYPES = ((TOPUP, "Top Up"), (DEDUCTION, "Deduction"))

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPES)
    date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.customer.name}: {self.type} {self.amount}"


class WaterUsage(models.Model):
    """Raw and billed water usage sent by IoT meters (ESP32)."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="water_usages")
    liters = models.DecimalField(max_digits=12, decimal_places=3)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    meter_payload_id = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional reading identifier for idempotency from IoT payload.",
    )

    class Meta:
        ordering = ["-timestamp"]

    def clean(self):
        if self.liters <= 0:
            raise ValidationError("Liters used must be greater than zero.")

    def __str__(self) -> str:
        return f"{self.customer.meter_id}: {self.liters}L ({self.cost})"
