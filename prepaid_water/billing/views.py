"""API views implementing core prepaid billing workflows."""
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, Customer, Tariff, Transaction, WaterUsage
from .permissions import IsAdminOrStaff
from .serializers import (
    AccountTopupSerializer,
    AdminReportSerializer,
    CustomerBalanceSerializer,
    CustomerRegistrationSerializer,
    WaterUsageSerializer,
)


class CustomerRegisterView(APIView):
    """POST /api/customer/register - create customer profile and prepaid account."""

    permission_classes = [IsAdminOrStaff]

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response(CustomerBalanceSerializer(customer).data, status=status.HTTP_201_CREATED)


class AccountTopupView(APIView):
    """POST /api/account/topup - load customer account credit."""

    permission_classes = [IsAdminOrStaff]

    @db_transaction.atomic
    def post(self, request):
        serializer = AccountTopupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = get_object_or_404(Customer, pk=serializer.validated_data["customer_id"])
        account = customer.account
        amount = serializer.validated_data["amount"]

        account.balance += amount
        if account.balance > 0:
            customer.is_water_enabled = True
            customer.save(update_fields=["is_water_enabled"])
        account.save(update_fields=["balance", "updated_at"])

        Transaction.objects.create(
            customer=customer,
            amount=amount,
            type=Transaction.TOPUP,
            reference=f"Top-up at {timezone.now().isoformat()}",
        )

        return Response(
            {
                "message": "Top-up successful",
                "customer_id": customer.id,
                "new_balance": account.balance,
            },
            status=status.HTTP_200_OK,
        )


class WaterUsageIngestView(APIView):
    """POST /api/water/usage - receive IoT meter usage and deduct from balance."""

    # ESP32 devices are authenticated with a shared token by default; allow unauthenticated request
    # and enforce token manually for easier IoT integration.
    permission_classes = [permissions.AllowAny]

    @db_transaction.atomic
    def post(self, request):
        expected_token = request.headers.get("X-DEVICE-TOKEN")
        configured_token = request.query_params.get("token") or "WASAC-DEVICE-SECRET"
        if expected_token != configured_token:
            return Response({"detail": "Invalid device token."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = WaterUsageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        meter_id = serializer.validated_data["meter_id"]
        liters = serializer.validated_data["liters"]
        meter_payload_id = serializer.validated_data.get("meter_payload_id", "")

        customer = get_object_or_404(Customer, meter_id=meter_id)
        account = Account.objects.select_for_update().get(customer=customer)

        tariff = Tariff.objects.filter(is_active=True).first()
        if tariff is None:
            return Response({"detail": "No active tariff configured."}, status=status.HTTP_400_BAD_REQUEST)

        cost = (liters * tariff.price_per_liter).quantize(Decimal("0.01"))
        account.balance = max(Decimal("0.00"), account.balance - cost)
        account.save(update_fields=["balance", "updated_at"])

        if account.balance == Decimal("0.00"):
            customer.is_water_enabled = False
            customer.save(update_fields=["is_water_enabled"])

        usage = WaterUsage.objects.create(
            customer=customer,
            liters=liters,
            cost=cost,
            meter_payload_id=meter_payload_id,
        )
        Transaction.objects.create(
            customer=customer,
            amount=cost,
            type=Transaction.DEDUCTION,
            reference=f"Usage reading {usage.id} from meter {meter_id}",
        )

        return Response(
            {
                "message": "Usage recorded",
                "customer_id": customer.id,
                "liters": liters,
                "cost": cost,
                "remaining_balance": account.balance,
                "water_enabled": customer.is_water_enabled,
            },
            status=status.HTTP_200_OK,
        )


class CustomerBalanceView(APIView):
    """GET /api/customer/balance?customer_id=1 - fetch account balance."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        customer_id = request.query_params.get("customer_id")

        if customer_id:
            customer = get_object_or_404(Customer, pk=customer_id)
        else:
            customer = get_object_or_404(Customer, user=request.user)

        return Response(CustomerBalanceSerializer(customer).data, status=status.HTTP_200_OK)


class AdminReportView(APIView):
    """GET /api/admin/report - provides dashboard KPIs and recent activity."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        total_revenue = (
            Transaction.objects.filter(type=Transaction.TOPUP).aggregate(total=Sum("amount")).get("total")
            or Decimal("0.00")
        )
        total_consumption = WaterUsage.objects.aggregate(total=Sum("liters")).get("total") or Decimal("0.000")
        active_meters = Customer.objects.filter(is_water_enabled=True).count()

        customers = Customer.objects.select_related("account").all()
        recent_transactions = Transaction.objects.select_related("customer").all()[:50]

        report_payload = {
            "total_revenue": total_revenue,
            "total_water_consumption_liters": total_consumption,
            "active_meters": active_meters,
            "customers": customers,
            "recent_transactions": recent_transactions,
        }
        serializer = AdminReportSerializer(report_payload)
        return Response(serializer.data, status=status.HTTP_200_OK)
