"""Demo standalone para el hackathon: uvicorn app:app --reload --port 8000

Incluye una página mínima /demo para mostrar los tres flujos (checkout, QR, push) en vivo.
En AIdeaText real solo se hace app.include_router(payments_router) en el FastAPI existente.
"""
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402

from pey_payments.router import router as payments_router  # noqa: E402

from fastapi.responses import RedirectResponse  # noqa: E402

from pey_payments.donaciones import router as cafe_router  # noqa: E402

app = FastAPI(title="AIdeaText x pey (CoDi)")
app.include_router(payments_router)
app.include_router(cafe_router)


@app.get("/")
def root():
    return RedirectResponse("/cafe")

DEMO = """<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIdeaText · Pagos CoDi</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:560px;margin:32px auto;padding:0 16px;color:#1b1b1f}
 h1{font-size:1.4rem} button{padding:10px 14px;border-radius:8px;border:1px solid #333;background:#111;color:#fff;cursor:pointer}
 select,input{padding:8px;border-radius:6px;border:1px solid #bbb;width:100%;margin:4px 0 12px}
 .card{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}
 img{max-width:240px;display:block;margin:8px auto} code{font-size:.8rem;word-break:break-all}
</style>
<h1>AIdeaText · paga tu acceso con CoDi</h1>
<label>Usuario</label><input id="u" value="estudiante-demo">
<label>Plan</label><select id="p"></select>
<div class="card"><b>1. Checkout (CoDi + tarjeta)</b><br><br><button onclick="link()">Ir a pagar</button></div>
<div class="card"><b>2. QR CoDi</b> (aula, pantalla, impreso)<br><br><button onclick="qr()">Generar QR</button><div id="qr"></div></div>
<div class="card"><b>3. Cobro al celular</b><input id="tel" placeholder="10 dígitos"><button onclick="pn()">Enviar solicitud</button></div>
<div class="card"><b>Estado</b><div id="st">—</div><div id="ent"></div></div>
<script>
const $=id=>document.getElementById(id);let order=null,timer=null;
fetch('/payments/plans').then(r=>r.json()).then(ps=>{for(const[k,v]of Object.entries(ps))$('p').innerHTML+=`<option value="${k}">${v.label} — $${v.amount} MXN</option>`});
const body=x=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:$('u').value,plan:$('p').value,...x})});
async function call(path,x){const r=await fetch(path,body(x));const j=await r.json();if(!r.ok){$('st').textContent=JSON.stringify(j);throw j}order=j.order_id;watch();return j}
async function link(){const j=await call('/payments/checkout');window.open(j.checkout_url,'_blank')}
async function qr(){const j=await call('/payments/codi/qr');$('qr').innerHTML=j.qr_png_base64?`<img src="data:image/png;base64,${j.qr_png_base64}">`:`<code>${j.qr_string}</code>`}
async function pn(){await call('/payments/codi/push',{phone_number:$('tel').value});$('st').textContent='Solicitud enviada: aprueba en tu app bancaria'}
function watch(){clearInterval(timer);timer=setInterval(async()=>{const o=await (await fetch('/payments/orders/'+order)).json();$('st').textContent=`Orden ${o.order_id}: ${o.status}`;
 if(o.status==='paid'){clearInterval(timer);const e=await (await fetch('/payments/entitlements/'+o.user_id)).json();$('ent').textContent=`Créditos: ${e.credits}`+(e.valid_until?` · acceso hasta ${new Date(e.valid_until*1000).toLocaleDateString()}`:'')}},2000)}
</script></html>"""


@app.get("/demo", response_class=HTMLResponse)
def demo():
    return DEMO


@app.get("/pago/exito", response_class=HTMLResponse)
def ok(order: str = ""):
    return f"<p style='font-family:system-ui'>Pago recibido. Orden {order}. Ya puedes volver a AIdeaText.</p>"


@app.get("/pago/cancelado", response_class=HTMLResponse)
def cancel(order: str = ""):
    return f"<p style='font-family:system-ui'>Pago cancelado. Orden {order}.</p>"
