"""Serializers map model data to JSON and validate request payloads."""
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.db import transaction as db_transaction
from rest_framework import serializers

from .models import Account, Customer, Tariff, Transaction, WaterUsage


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """Registers a customer and initializes a prepaid account."""

    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address", "meter_id", "rfid_card", "username", "password"]

    @db_transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop("username", None)
        password = validated_data.pop("password", None)

        user = None
        if username and password:
            user = User.objects.create_user(username=username, password=password)
            customer_group, _ = Group.objects.get_or_create(name="CUSTOMER")
            user.groups.add(customer_group)

        customer = Customer.objects.create(user=user, **validated_data)
        Account.objects.create(customer=customer)
        return customer


class AccountTopupSerializer(serializers.Serializer):
    """Validates top-up operations against customer prepaid account."""

    customer_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))


class WaterUsageSerializer(serializers.Serializer):
    """Payload schema received from ESP32 meter."""

    meter_id = serializers.CharField(max_length=60)
    liters = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    meter_payload_id = serializers.CharField(max_length=120, required=False, allow_blank=True)


class TransactionSerializer(serializers.ModelSerializer):
    """Returns account history records for reporting screens."""

    class Meta:
        model = Transaction
        fields = ["id", "customer", "amount", "type", "date", "reference"]


class CustomerBalanceSerializer(serializers.ModelSerializer):
    """Shows customer account balance and water status."""

    balance = serializers.DecimalField(source="account.balance", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "meter_id", "balance", "is_water_enabled"]


class AdminReportSerializer(serializers.Serializer):
    """Aggregated values for admin dashboard widgets."""

    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_water_consumption_liters = serializers.DecimalField(max_digits=14, decimal_places=3)
    active_meters = serializers.IntegerField()
    customers = CustomerBalanceSerializer(many=True)
    recent_transactions = TransactionSerializer(many=True)


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ["id", "price_per_liter", "is_active", "effective_from"]


class WaterUsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterUsage
        fields = ["id", "customer", "liters", "cost", "timestamp", "meter_payload_id"]
