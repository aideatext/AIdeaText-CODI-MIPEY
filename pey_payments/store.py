"""Libro de órdenes y derechos de acceso (SQLite para el prototipo).

En producción se cambia por la base de AIdeaText (DocumentDB/Mongo); la interfaz es la misma.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid

DB_PATH = os.getenv("PAYMENTS_DB", "payments.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  order_id      TEXT PRIMARY KEY,      -- nuestra referencia (clientReferenceId / numRef)
  num_ref       TEXT UNIQUE,           -- 7 dígitos para CoDi
  user_id       TEXT NOT NULL,
  plan          TEXT NOT NULL,
  amount        REAL NOT NULL,
  channel       TEXT NOT NULL,         -- link | qr | pn
  pey_id        TEXT,                  -- paymentLinkId | IDC del QR | transactionId PN
  status        TEXT NOT NULL DEFAULT 'pending',   -- pending | paid
  created_at    INTEGER NOT NULL,
  paid_at       INTEGER
);
CREATE TABLE IF NOT EXISTS webhook_events (
  webhook_id    TEXT PRIMARY KEY,      -- header webhook-id (idempotencia)
  type          TEXT,
  payload       TEXT,
  received_at   INTEGER
);
CREATE TABLE IF NOT EXISTS entitlements (
  user_id       TEXT PRIMARY KEY,
  credits       INTEGER NOT NULL DEFAULT 0,  -- sesiones de tutor / análisis disponibles
  valid_until   INTEGER                      -- acceso por periodo (licencias)
);
"""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def _num_ref(c: sqlite3.Connection) -> str:
    # CoDi acepta numRef de 1-7 dígitos; lo usamos para conciliar QR/PN con la orden.
    row = c.execute("SELECT COUNT(*) AS n FROM orders").fetchone()
    return str(1000000 + (row["n"] % 8999999))[-7:]


def create_order(user_id: str, plan: str, amount: float, channel: str) -> dict:
    with conn() as c:
        order_id = f"ait-{uuid.uuid4().hex[:12]}"
        num_ref = _num_ref(c)
        c.execute(
            "INSERT INTO orders(order_id,num_ref,user_id,plan,amount,channel,created_at) VALUES (?,?,?,?,?,?,?)",
            (order_id, num_ref, user_id, plan, amount, channel, int(time.time())),
        )
        return dict(c.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone())


def set_pey_id(order_id: str, pey_id: str) -> None:
    with conn() as c:
        c.execute("UPDATE orders SET pey_id=? WHERE order_id=?", (pey_id, order_id))


def get_order(order_id: str) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
        return dict(r) if r else None


def find_order(*, order_id: str | None = None, pey_id: str | None = None, num_ref: str | None = None) -> dict | None:
    with conn() as c:
        for col, val in (("order_id", order_id), ("pey_id", pey_id), ("num_ref", num_ref)):
            if val:
                r = c.execute(f"SELECT * FROM orders WHERE {col}=?", (val,)).fetchone()
                if r:
                    return dict(r)
    return None


def seen_webhook(webhook_id: str, type_: str, payload: dict) -> bool:
    """Registra el evento; devuelve True si ya se había procesado (reintento de pey)."""
    with conn() as c:
        try:
            c.execute(
                "INSERT INTO webhook_events VALUES (?,?,?,?)",
                (webhook_id, type_, json.dumps(payload), int(time.time())),
            )
            return False
        except sqlite3.IntegrityError:
            return True


# Catálogo de planes: qué otorga cada pago.
PLANS = {
    "tutor-10":      {"label": "10 sesiones con el tutor virtual", "amount": 49.0,  "credits": 10, "days": 0},
    "estudiante-mes": {"label": "Acceso estudiante 30 días",        "amount": 99.0,  "credits": 0,  "days": 30},
    "prueba":        {"label": "Prueba de integración",            "amount": 0.01,  "credits": 1,  "days": 0},
}


def mark_paid_and_grant(order: dict) -> None:
    plan = PLANS.get(order["plan"], {"credits": 0, "days": 0})
    now = int(time.time())
    with conn() as c:
        cur = c.execute(
            "UPDATE orders SET status='paid', paid_at=? WHERE order_id=? AND status!='paid'",
            (now, order["order_id"]),
        )
        if cur.rowcount == 0:
            return  # ya estaba pagada; no duplicar derechos
        row = c.execute("SELECT * FROM entitlements WHERE user_id=?", (order["user_id"],)).fetchone()
        credits = (row["credits"] if row else 0) + plan["credits"]
        base = max(row["valid_until"] or 0, now) if row else now
        valid_until = base + plan["days"] * 86400 if plan["days"] else (row["valid_until"] if row else None)
        c.execute(
            "INSERT INTO entitlements(user_id,credits,valid_until) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET credits=excluded.credits, valid_until=excluded.valid_until",
            (order["user_id"], credits, valid_until),
        )


def get_entitlement(user_id: str) -> dict:
    with conn() as c:
        r = c.execute("SELECT * FROM entitlements WHERE user_id=?", (user_id,)).fetchone()
        return dict(r) if r else {"user_id": user_id, "credits": 0, "valid_until": None}
