# Prepaid Water Billing Management System – Case Study of WASAC Group

Complete Django + Django REST Framework backend implementation for prepaid water billing with IoT usage ingestion from ESP32 flow meters.

## 1) Project Structure

```text
prepaid_water/
├── manage.py
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── billing/
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── permissions.py
    ├── admin.py
    └── tests.py
```

## 2) Setup Instructions

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 3) Roles

- **Admin**: Django superuser.
- **WASAC Staff**: user added to `WASAC_STAFF` group.
- **Customer**: optional user attached to customer profile and added to `CUSTOMER` group.

## 4) API Endpoints

- `POST /api/customer/register`
- `POST /api/account/topup`
- `POST /api/water/usage`
- `GET /api/customer/balance`
- `GET /api/admin/report`

## 5) Sample API Requests

### Register Customer

```bash
curl -X POST http://127.0.0.1:8000/api/customer/register \
  -u staff:password \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Uwase",
    "phone": "0780000000",
    "address": "Kigali",
    "meter_id": "MTR1001",
    "rfid_card": "RFID001",
    "username": "alice",
    "password": "alicepass123"
  }'
```

### Top Up Account

```bash
curl -X POST http://127.0.0.1:8000/api/account/topup \
  -u staff:password \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 1, "amount": "5000.00"}'
```

### IoT Water Usage Ingestion (ESP32)

```bash
curl -X POST "http://127.0.0.1:8000/api/water/usage?token=WASAC-DEVICE-SECRET" \
  -H "Content-Type: application/json" \
  -H "X-DEVICE-TOKEN: WASAC-DEVICE-SECRET" \
  -d '{"meter_id": "MTR1001", "liters": 10}'
```

### Get Customer Balance

```bash
curl "http://127.0.0.1:8000/api/customer/balance?customer_id=1" -u staff:password
```

### Admin Report

```bash
curl "http://127.0.0.1:8000/api/admin/report" -u admin:adminpassword
```

## 6) Billing Logic Implemented

```python
water_cost = liters_used * tariff_rate

if balance == 0:
    disable water supply
```

Implemented in `billing/views.py` (`WaterUsageIngestView`), where cost is calculated from active tariff, account balance is deducted automatically, a deduction transaction is recorded, and `is_water_enabled` is toggled off at zero balance.

## 7) Admin Dashboard Coverage

Django admin is configured for:
- Customers and meter states
- Prepaid balances
- Top-up and deduction transactions
- Water usage logs
- Tariff management (single active tariff)

## 8) Reporting

`GET /api/admin/report` returns:
- Total revenue (sum of topups)
- Total water consumption (liters)
- Active meters
- Customer balances
- Recent transaction list
