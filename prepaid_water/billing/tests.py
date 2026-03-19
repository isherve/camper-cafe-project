"""Basic API workflow tests for prepaid billing logic."""
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Account, Customer, Tariff


class PrepaidWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(username="staff", password="pass1234", is_staff=True)
        group, _ = Group.objects.get_or_create(name="WASAC_STAFF")
        self.staff.groups.add(group)
        self.client.force_authenticate(user=self.staff)
        Tariff.objects.create(price_per_liter=Decimal("5.0000"), is_active=True)

    def test_customer_register_topup_and_usage(self):
        register_resp = self.client.post(
            "/api/customer/register",
            {
                "name": "Alice",
                "phone": "0780000000",
                "address": "Kigali",
                "meter_id": "MTR1001",
                "rfid_card": "RFID001",
            },
            format="json",
        )
        self.assertEqual(register_resp.status_code, 201)
        customer_id = register_resp.data["id"]

        topup_resp = self.client.post(
            "/api/account/topup", {"customer_id": customer_id, "amount": "100.00"}, format="json"
        )
        self.assertEqual(topup_resp.status_code, 200)

        self.client.force_authenticate(user=None)
        usage_resp = self.client.post(
            "/api/water/usage?token=WASAC-DEVICE-SECRET",
            {"meter_id": "MTR1001", "liters": "10.000"},
            format="json",
            HTTP_X_DEVICE_TOKEN="WASAC-DEVICE-SECRET",
        )
        self.assertEqual(usage_resp.status_code, 200)

        customer = Customer.objects.get(meter_id="MTR1001")
        self.assertEqual(customer.account.balance, Decimal("50.00"))

    def test_disable_water_when_balance_zero(self):
        customer = Customer.objects.create(
            name="Bob",
            phone="0781111111",
            address="Musanze",
            meter_id="MTR2002",
            rfid_card="RFID002",
        )
        Account.objects.create(customer=customer, balance=Decimal("20.00"))

        self.client.force_authenticate(user=None)
        resp = self.client.post(
            "/api/water/usage?token=WASAC-DEVICE-SECRET",
            {"meter_id": "MTR2002", "liters": "5.000"},
            format="json",
            HTTP_X_DEVICE_TOKEN="WASAC-DEVICE-SECRET",
        )
        self.assertEqual(resp.status_code, 200)
        customer.refresh_from_db()
        self.assertFalse(customer.is_water_enabled)
