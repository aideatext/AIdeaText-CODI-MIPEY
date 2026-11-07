"""'Invítame un café' para AIdeaText con CoDi (pey).

Flujo:
  1. Se crea UNA VEZ un QR CoDi con amount=0 (monto libre) y sin expiración  -> reutilizable.
  2. El QR (PNG) se pega en cualquier página de AIdeaText.
  3. El donante lo escanea con la app de su banco, elige el monto y paga.
  4. Confirmación por dos vías (cualquiera basta):
       a) GET /transaction/codi/qr/{id} en pey (sin webhook, sin servidor público)
       b) webhook codi.qr.payment_received -> /webhooks/pey (si hay URL pública)
  5. /cafe muestra el QR, botones de monto fijo y el muro de agradecimientos en vivo.
"""
from __future__ import annotations

import json
import os
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import store
from .client import PeyError
from .router import _bank_account, pey

router = APIRouter()
QR_FILE = os.getenv("DONATION_QR_FILE", "donacion_qr.json")
CAFES = {"1 café": 35, "2 cafés": 70, "Desayuno": 150}


def load_static_qr() -> dict | None:
    try:
        return json.load(open(QR_FILE, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def create_static_qr(force: bool = False) -> dict:
    qr = load_static_qr()
    if qr and not force:
        return qr
    r = pey().create_codi_qr(
        amount=0,                      # monto libre: lo decide el donante
        concept="Cafe AIdeaText",
        expiration=0,                  # sin expiración -> QR permanente
        generate_image=True,
        bank_account_id=_bank_account(),
        metadata={"app": "aideatext", "tipo": "donacion"},
    )
    qr = {"id": r["id"], "qrString": r["qrString"], "qrImage": r.get("qrImage"), "created": int(time.time())}
    json.dump(qr, open(QR_FILE, "w", encoding="utf-8"))
    return qr


class CafeIn(BaseModel):
    amount: float = Field(gt=0, le=10000)
    nombre: str | None = Field(default=None, max_length=30)


@router.post("/cafe/qr")
def cafe_qr_fijo(body: CafeIn):
    """QR de monto fijo (botones 1 café / 2 cafés), expira en 15 min."""
    try:
        r = pey().create_codi_qr(
            amount=body.amount, concept="Cafe AIdeaText", expiration=900, generate_image=True,
            bank_account_id=_bank_account(),
            metadata={"app": "aideatext", "tipo": "donacion", "nombre": body.nombre or "Anónimo"},
        )
    except PeyError as e:
        raise HTTPException(502, e.body)
    return {"codi_qr_id": r["id"], "qr_png_base64": r.get("qrImage"), "qr_string": r["qrString"]}


class CafePushIn(CafeIn):
    telefono: str = Field(pattern=r"^[0-9]{10}$")


@router.post("/cafe/push")
def cafe_push(body: CafePushIn):
    """Para quien ve la página DESDE su celular (no puede escanear su propia pantalla):
    la solicitud de cobro llega a su app bancaria y solo la aprueba."""
    try:
        r = pey().create_codi_push(
            amount=body.amount, phone_number=body.telefono, concept="Cafe AIdeaText", expiration=600,
            bank_account_id=_bank_account(),
            metadata={"app": "aideatext", "tipo": "donacion", "nombre": body.nombre or "Anónimo"},
        )
    except PeyError as e:
        raise HTTPException(502, e.body)
    return {"transaction_id": r["transactionId"], "codi_id": r["codiId"]}


def _feed() -> list[dict]:
    items: dict[str, dict] = {}
    # a) eventos recibidos por webhook
    with store.conn() as c:
        for row in c.execute("SELECT payload FROM webhook_events WHERE type LIKE 'codi.%' ORDER BY received_at DESC LIMIT 50"):
            e = json.loads(row["payload"])
            ext = (e.get("metadata") or {}).get("externalMetadata") or {}
            items[e.get("transactionId", str(len(items)))] = {
                "amount": e.get("amount"), "fecha": e.get("datePaid"), "nombre": ext.get("nombre") or "Anónimo"}
    # b) consulta directa a pey del QR permanente (no requiere webhook)
    qr = load_static_qr()
    if qr:
        try:
            for t in pey().list_qr_transactions(qr["id"]).get("items", []):
                if t.get("status", "PAID") == "PAID":
                    items.setdefault(t["id"], {"amount": t.get("amount"), "fecha": t.get("datePaid"), "nombre": "Anónimo"})
        except PeyError:
            pass
    return sorted(items.values(), key=lambda x: x.get("fecha") or 0, reverse=True)


@router.get("/cafe/feed")
def cafe_feed():
    feed = _feed()
    return {"total": round(sum(i["amount"] or 0 for i in feed), 2), "cafes": len(feed), "donaciones": feed[:20]}


@router.get("/cafe/qr.png")
def cafe_qr_png():
    import base64
    from fastapi.responses import Response
    qr = create_static_qr()
    if not qr.get("qrImage"):
        raise HTTPException(404, "pey no devolvió imagen")
    return Response(base64.b64decode(qr["qrImage"]), media_type="image/png")


PAGE = """<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Invítame un café · AIdeaText</title>
<style>
:root{--bg:#faf7f2;--ink:#2b2118;--muted:#7a6a5c;--acc:#8a4b2a;--card:#fff}
body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,sans-serif}
main{max-width:520px;margin:0 auto;padding:28px 16px}
h1{font-size:1.6rem;margin:.2rem 0} p{color:var(--muted);line-height:1.5}
.card{background:var(--card);border-radius:16px;padding:20px;margin:16px 0;box-shadow:0 1px 3px #0001;text-align:center}
img{width:240px;max-width:100%} .row{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
button{border:0;background:var(--acc);color:#fff;padding:10px 14px;border-radius:999px;font-size:1rem;cursor:pointer}
input{padding:8px;border:1px solid #ddd;border-radius:8px;width:60%;margin-bottom:10px}
.big{font-size:2rem;font-weight:700;color:var(--acc)} li{list-style:none;padding:6px 0;border-bottom:1px solid #eee}
ul{padding:0;margin:0;text-align:left} small{color:var(--muted)}
</style><main>
<h1>☕ Invítame un café</h1>
<p>AIdeaText es un tutor de escritura con IA para estudiantes. Si te sirve, apóyalo con lo que quieras,
sin comisiones, directo desde la app de tu banco con <b>CoDi</b>.</p>
<div class="card"><b>Monto libre</b><br><img src="/cafe/qr.png" alt="QR CoDi monto libre"><br>
<small>Escanea con tu app bancaria → CoDi → elige el monto</small></div>
<div class="card"><b>O elige un monto</b><br><br><input id="n" placeholder="Tu nombre (opcional)">
<input id="tel" inputmode="numeric" placeholder="¿Estás en tu celular? Tu número (10 dígitos)">
<div class="row">__BOTONES__</div><div id="fijo"></div></div>
<div class="card"><div class="big" id="tot">$0</div><small id="cnt">0 cafés</small><ul id="wall"></ul></div>
<script>
async function fijo(m){const tel=document.getElementById('tel').value.trim(),nombre=document.getElementById('n').value||null;
 const push=/^[0-9]{10}$/.test(tel);
 const r=await fetch(push?'/cafe/push':'/cafe/qr',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify(push?{amount:m,nombre,telefono:tel}:{amount:m,nombre})});const j=await r.json();
 document.getElementById('fijo').innerHTML=!r.ok?'Error: '+JSON.stringify(j):push
  ?`<p>📲 Revisa tu app bancaria: te llegó una solicitud CoDi por $${m} MXN. Solo apruébala.</p>`
  :`<img src="data:image/png;base64,${j.qr_png_base64}"><br><small>$${m} MXN · válido 15 min</small>`}
async function feed(){const j=await (await fetch('/cafe/feed')).json();
 document.getElementById('tot').textContent='$'+j.total.toFixed(2)+' MXN';document.getElementById('cnt').textContent=j.cafes+' cafés';
 document.getElementById('wall').innerHTML=j.donaciones.map(d=>`<li>☕ ${d.nombre} · $${d.amount} <small>${d.fecha?new Date(d.fecha*1000).toLocaleTimeString():''}</small></li>`).join('')}
feed();setInterval(feed,4000);
</script></main></html>"""


@router.get("/cafe", response_class=HTMLResponse)
def cafe_page():
    botones = "".join(f'<button onclick="fijo({v})">{k} · ${v}</button>' for k, v in CAFES.items())
    return PAGE.replace("__BOTONES__", botones)
