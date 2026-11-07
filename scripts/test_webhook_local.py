"""Prueba local SIN dinero: crea una orden y simula el webhook firmado de pey.

    python scripts/test_webhook_local.py

Valida firma Standard Webhooks, idempotencia y otorgamiento de créditos.
"""
import base64
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PAYMENTS_DB", "test_payments.db")
SECRET = "whsec_" + base64.b64encode(b"aideatext-local-test-secret-32by").decode()
os.environ["PEY_WEBHOOK_SECRET"] = SECRET
os.environ.setdefault("PEY_API_KEY", "dummy")

if os.path.exists(os.environ["PAYMENTS_DB"]):
    os.remove(os.environ["PAYMENTS_DB"])

from fastapi.testclient import TestClient  # noqa: E402
from standardwebhooks import Webhook  # noqa: E402

from app import app  # noqa: E402
from pey_payments import store  # noqa: E402

c = TestClient(app)
order = store.create_order("estudiante-demo", "tutor-10", 49.0, "qr")
store.set_pey_id(order["order_id"], "35a13c183a")

evt = {
    "type": "codi.qr.payment_received", "amount": 49, "codiQrId": "35a13c183a",
    "numRef": order["num_ref"], "transactionId": "01TESTTXN", "datePaid": 1790724818,
    "metadata": {"externalMetadata": {"orderId": order["order_id"]}},
}
raw = json.dumps(evt)
now = datetime.now(timezone.utc)
sig = Webhook(SECRET).sign("msg_test_1", now, raw)
headers = {"webhook-id": "msg_test_1", "webhook-timestamp": str(int(now.timestamp())), "webhook-signature": sig,
           "content-type": "application/json"}

r1 = c.post("/webhooks/pey", content=raw, headers=headers)
r2 = c.post("/webhooks/pey", content=raw, headers=headers)              # reintento
bad = c.post("/webhooks/pey", content=raw, headers={**headers, "webhook-signature": "v1,AAAA"})
ent = c.get("/payments/entitlements/estudiante-demo").json()
st = c.get(f"/payments/orders/{order['order_id']}").json()

print("1er webhook :", r1.status_code, r1.json())
print("reintento   :", r2.status_code, r2.json())
print("firma falsa :", bad.status_code)
print("orden       :", st["status"])
print("derechos    :", ent)
assert r1.status_code == 200 and r2.json().get("duplicate") and bad.status_code == 400
assert st["status"] == "paid" and ent["credits"] == 10
print("OK: flujo de webhook verificado")
