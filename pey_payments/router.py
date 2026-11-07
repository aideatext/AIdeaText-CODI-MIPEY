"""Router FastAPI de pagos para AIdeaText.

Se monta en el backend FastAPI existente (v5 / tutor.aideatext.ai):

    from pey_payments.router import router as payments_router
    app.include_router(payments_router)

Endpoints:
    GET  /payments/plans
    POST /payments/checkout          -> payment link (CoDi + tarjeta), redirige al checkout de pey
    POST /payments/codi/qr           -> QR CoDi (para pantalla / aula / impreso)
    POST /payments/codi/push         -> cobro al celular del estudiante o tutor
    GET  /payments/orders/{order_id} -> estado de la orden (para que Streamlit haga polling)
    GET  /payments/entitlements/{user_id}
    POST /webhooks/pey               -> recibe eventos firmados (Standard Webhooks)
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from standardwebhooks import Webhook
from standardwebhooks.webhooks import WebhookVerificationError

from . import store
from .client import PeyClient, PeyError

log = logging.getLogger("pey")
router = APIRouter()

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://tutor.aideatext.ai")
_client: PeyClient | None = None


def pey() -> PeyClient:
    global _client
    if _client is None:
        _client = PeyClient()
    return _client


def _bank_account() -> str | None:
    return os.getenv("PEY_BANK_ACCOUNT_ID") or None


class OrderIn(BaseModel):
    user_id: str
    plan: str = Field(examples=["tutor-10"])


class PushIn(OrderIn):
    phone_number: str = Field(pattern=r"^[0-9]{10}$")


def _new_order(body: OrderIn, channel: str) -> tuple[dict, dict]:
    plan = store.PLANS.get(body.plan)
    if not plan:
        raise HTTPException(404, f"Plan desconocido: {body.plan}")
    return store.create_order(body.user_id, body.plan, plan["amount"], channel), plan


def _meta(order: dict) -> dict:
    return {"orderId": order["order_id"], "userId": order["user_id"], "plan": order["plan"], "app": "aideatext"}


@router.get("/payments/plans")
def plans():
    return store.PLANS


@router.post("/payments/checkout")
def checkout(body: OrderIn):
    order, plan = _new_order(body, "link")
    try:
        link = pey().create_payment_link(
            amount=plan["amount"],
            success_url=f"{PUBLIC_BASE_URL}/pago/exito?order={order['order_id']}",
            back_url=f"{PUBLIC_BASE_URL}/pago/cancelado?order={order['order_id']}",
            client_reference_id=order["order_id"],
            metadata=_meta(order),
        )
    except PeyError as e:
        raise HTTPException(502, e.body)
    store.set_pey_id(order["order_id"], link["id"])
    return {"order_id": order["order_id"], "checkout_url": link["url"], "payment_link_id": link["id"]}


@router.post("/payments/codi/qr")
def codi_qr(body: OrderIn):
    order, plan = _new_order(body, "qr")
    try:
        qr = pey().create_codi_qr(
            amount=plan["amount"],
            concept=f"AIdeaText {plan['label']}"[:40],
            num_ref=order["num_ref"],
            expiration=900,               # 15 min
            generate_image=True,
            bank_account_id=_bank_account(),
            metadata=_meta(order),
        )
    except PeyError as e:
        raise HTTPException(502, e.body)
    store.set_pey_id(order["order_id"], qr["id"])
    return {"order_id": order["order_id"], "codi_qr_id": qr["id"], "qr_string": qr["qrString"], "qr_png_base64": qr.get("qrImage")}


@router.post("/payments/codi/push")
def codi_push(body: PushIn):
    order, plan = _new_order(body, "pn")
    try:
        pn = pey().create_codi_push(
            amount=plan["amount"],
            phone_number=body.phone_number,
            concept=f"AIdeaText {plan['label']}"[:40],
            num_ref=order["num_ref"],
            expiration=600,
            bank_account_id=_bank_account(),
            metadata=_meta(order),
        )
    except PeyError as e:
        raise HTTPException(502, e.body)
    store.set_pey_id(order["order_id"], pn["transactionId"])
    return {"order_id": order["order_id"], "transaction_id": pn["transactionId"], "codi_id": pn["codiId"]}


@router.get("/payments/orders/{order_id}")
def order_status(order_id: str):
    order = store.get_order(order_id)
    if not order:
        raise HTTPException(404, "Orden no encontrada")
    return order


@router.get("/payments/entitlements/{user_id}")
def entitlements(user_id: str):
    return store.get_entitlement(user_id)


# ---------------------------------------------------------------- Webhooks
def _order_from_event(evt: dict) -> dict | None:
    ext = ((evt.get("metadata") or {}).get("externalMetadata") or {})
    t = evt.get("type")
    if t == "payment_link.status_updated":
        return store.find_order(order_id=evt.get("clientReferenceId"), pey_id=evt.get("paymentLinkId"))
    if t == "codi.qr.payment_received":
        return store.find_order(order_id=ext.get("orderId"), pey_id=evt.get("codiQrId"), num_ref=evt.get("numRef"))
    if t == "codi.pn.payment_received":
        return store.find_order(order_id=ext.get("orderId"), pey_id=evt.get("transactionId"), num_ref=evt.get("numRef"))
    return None


@router.post("/webhooks/pey")
async def pey_webhook(request: Request):
    raw = await request.body()
    secret = os.getenv("PEY_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(500, "Falta PEY_WEBHOOK_SECRET")
    try:
        evt = Webhook(secret).verify(raw, dict(request.headers))
    except WebhookVerificationError:
        raise HTTPException(400, "Firma inválida")

    webhook_id = request.headers.get("webhook-id", evt.get("transactionId", ""))
    if store.seen_webhook(webhook_id, evt.get("type", ""), evt):
        return {"ok": True, "duplicate": True}

    order = _order_from_event(evt)
    if not order:
        log.warning("Evento sin orden asociada: %s", evt)
        return {"ok": True, "matched": False}

    paid = evt.get("type") in ("codi.qr.payment_received", "codi.pn.payment_received") or evt.get("status") == "paid"
    if paid:
        # Defensa: el monto recibido debe cubrir el de la orden (QR con amount=0 permite montos libres).
        amount = evt.get("amount") or sum(t.get("amount", 0) for t in evt.get("transactions", []))
        if amount + 1e-6 < order["amount"]:
            log.warning("Pago parcial %s < %s en %s", amount, order["amount"], order["order_id"])
            return {"ok": True, "partial": True}
        store.mark_paid_and_grant(order)
    return {"ok": True, "order_id": order["order_id"], "paid": paid}
