"""Reparto automático de "sesiones pendientes" entre estudiantes activos de AIdeaText v61.

Flujo (Nivel 1, sin tocar conText):
  1. `scripts/sincronizar_estudiantes_v61.py` copia de v61 SOLO el seudónimo de investigación
     (`estudiantes.investigacion_id`, p. ej. RES-0004) de los estudiantes activos. Ni nombre ni correo.
  2. Cada sesión financiada (total donado // PRECIO_SESION) se convierte en un código de un solo uso.
  3. Reparto igualitario por rondas: cada ronda da 1 sesión a todos los estudiantes activos. El
     sobrante que no completa una ronda queda como saldo. Al cierre del ciclo se compara el uso.
  4. El estudiante ve sus sesiones en /beca/{seudonimo}. Al pulsar "Usar", /canje/{codigo} marca el
     código como usado (una sola vez) y redirige a conText con ?ref=sesion-pendiente.
"""
from __future__ import annotations

import os
import secrets
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from . import store

router = APIRouter()
CICLO = os.getenv("CICLO", "2026-2")

SCHEMA = """
CREATE TABLE IF NOT EXISTS beneficiarios (
  seudonimo   TEXT PRIMARY KEY,          -- investigacion_id de v61; nunca nombre ni correo
  institucion TEXT,
  activo      INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS codigos (
  codigo      TEXT PRIMARY KEY,
  seudonimo   TEXT NOT NULL,
  creado      INTEGER NOT NULL,
  usado       INTEGER,                   -- epoch del canje; NULL = disponible
  ciclo       TEXT NOT NULL,             -- semestre o periodo, p. ej. 2026-2
  ronda       INTEGER NOT NULL           -- en cada ronda todos reciben 1
);
"""


def _conn():
    c = store.conn()
    c.executescript(SCHEMA)
    return c


def sincronizar(beneficiarios: list[dict]) -> int:
    """Reemplaza el padrón de beneficiarios activos. Los códigos ya asignados se conservan."""
    with _conn() as c:
        c.execute("UPDATE beneficiarios SET activo = 0")
        for b in beneficiarios:
            c.execute("INSERT INTO beneficiarios(seudonimo, institucion, activo) VALUES (?,?,1) "
                      "ON CONFLICT(seudonimo) DO UPDATE SET institucion=excluded.institucion, activo=1",
                      (b["seudonimo"], b.get("institucion")))
    return len(beneficiarios)


def repartir(sesiones_financiadas: int) -> int:
    """Reparto IGUALITARIO por rondas: cada ronda entrega 1 sesión a CADA estudiante activo,
    sin mirar cuántas tiene ni cuántas usó. Solo se reparte en rondas completas; lo que no
    alcanza para una ronda queda como saldo y entra en la siguiente donación.
    El uso real (quién usó más o menos) se revisa al cierre del ciclo en /becas."""
    nuevos = 0
    with _conn() as c:
        activos = [r["seudonimo"] for r in c.execute(
            "SELECT seudonimo FROM beneficiarios WHERE activo = 1 ORDER BY seudonimo")]
        if not activos:
            return 0
        ya = c.execute("SELECT COUNT(*) FROM codigos WHERE ciclo = ?", (CICLO,)).fetchone()[0]
        ronda = c.execute("SELECT COALESCE(MAX(ronda), 0) FROM codigos WHERE ciclo = ?", (CICLO,)).fetchone()[0]
        for _ in range(max(0, sesiones_financiadas - ya) // len(activos)):
            ronda += 1
            for s in activos:
                c.execute("INSERT INTO codigos(codigo, seudonimo, creado, ciclo, ronda) VALUES (?,?,?,?,?)",
                          (secrets.token_urlsafe(6), s, int(time.time()), CICLO, ronda))
                nuevos += 1
    return nuevos


def resumen(financiadas: int | None = None) -> dict:
    with _conn() as c:
        asignadas = c.execute("SELECT COUNT(*) FROM codigos WHERE ciclo = ?", (CICLO,)).fetchone()[0]
        usadas = c.execute("SELECT COUNT(*) FROM codigos WHERE ciclo = ? AND usado IS NOT NULL", (CICLO,)).fetchone()[0]
        rondas = c.execute("SELECT COALESCE(MAX(ronda), 0) FROM codigos WHERE ciclo = ?", (CICLO,)).fetchone()[0]
        por = [dict(r) for r in c.execute(
            "SELECT b.seudonimo, b.institucion, COUNT(k.codigo) AS asignadas, COUNT(k.usado) AS usadas "
            "FROM beneficiarios b LEFT JOIN codigos k ON k.seudonimo = b.seudonimo AND k.ciclo = ? "
            "WHERE b.activo = 1 GROUP BY b.seudonimo, b.institucion ORDER BY usadas DESC, b.seudonimo", (CICLO,))]
    n = len(por)
    out = {"ciclo": CICLO, "beneficiarios": n, "rondas": rondas, "asignadas": asignadas, "canjeadas": usadas,
           "por_estudiante": por}
    if financiadas is not None:
        out["saldo_por_repartir"] = financiadas - asignadas
        out["faltan_para_ronda"] = (n - (financiadas - asignadas) % n) if n else None
    return out


def _destino() -> str:
    from .donaciones import CONTEXT_REF, CONTEXT_URL
    return f"{CONTEXT_URL}/?ref={CONTEXT_REF}"


@router.get("/becas.json")
def becas():
    from .donaciones import cafe_feed  # cafe_feed ya llama a repartir()
    f = cafe_feed()
    return {"total_mxn": f["total"], "precio_sesion": f["precio_sesion"],
            "sesiones_financiadas": f["sesiones_financiadas"], **resumen(f["sesiones_financiadas"])}


@router.get("/becas", response_class=HTMLResponse)
def becas_html():
    b = becas()
    filas = "".join(
        f'<tr><td><a href="/beca/{p["seudonimo"]}">{p["seudonimo"]}</a></td><td>{p["institucion"]}</td>'
        f'<td>{p["asignadas"]}</td><td>{p["usadas"]}</td><td>{p["asignadas"] - p["usadas"]}</td></tr>'
        for p in b["por_estudiante"])
    return f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Reparto de sesiones · ciclo {b['ciclo']}</title>
<style>body{{font-family:system-ui;background:#faf7f2;color:#2b2118;max-width:720px;margin:auto;padding:24px}}
table{{width:100%;border-collapse:collapse;background:#fff}} td,th{{padding:8px;border-bottom:1px solid #eee;text-align:left}}
a{{color:#8a4b2a}} .k{{display:inline-block;margin:0 18px 12px 0}} .k b{{font-size:1.6rem;color:#8a4b2a;display:block}}</style>
<h1>Reparto de sesiones pendientes · ciclo {b['ciclo']}</h1>
<p>Cada ronda da <b>1 sesión a cada estudiante activo</b> de AIdeaText, por igual. Lo que no completa una ronda
queda como saldo para la siguiente donación. Al cierre del ciclo esta tabla muestra quién usó más y quién menos.
Solo seudónimos: nadie aquí ve nombres.</p>
<div><span class="k"><b>${b['total_mxn']:.2f}</b>donado</span><span class="k"><b>{b['sesiones_financiadas']}</b>financiadas</span>
<span class="k"><b>{b['beneficiarios']}</b>estudiantes</span><span class="k"><b>{b['rondas']}</b>rondas</span>
<span class="k"><b>{b['asignadas']}</b>asignadas</span><span class="k"><b>{b['canjeadas']}</b>usadas</span>
<span class="k"><b>{b['saldo_por_repartir']}</b>saldo (faltan {b['faltan_para_ronda']} para otra ronda)</span></div>
<table><tr><th>Estudiante</th><th>Institución</th><th>Recibidas</th><th>Usadas</th><th>Disponibles</th></tr>{filas}</table>
<p><a href="/cafe">← Donar</a> · <a href="/becas.json">datos en JSON</a></p></html>"""


@router.get("/beca/{seudonimo}.json")
def beca_estudiante_json(seudonimo: str):
    """Lo que v61 muestra en la cabecera del estudiante. Solo cifras, sin códigos."""
    from .donaciones import PRECIO_SESION, cafe_feed
    cafe_feed()  # asegura que el reparto está al día
    with _conn() as c:
        if not c.execute("SELECT 1 FROM beneficiarios WHERE seudonimo = ?", (seudonimo,)).fetchone():
            raise HTTPException(404, "Estudiante no registrado en el reparto")
        r = c.execute("SELECT COUNT(*) AS recibidas, COUNT(usado) AS usadas FROM codigos "
                      "WHERE seudonimo = ? AND ciclo = ?", (seudonimo, CICLO)).fetchone()
    return {"ciclo": CICLO, "recibidas": r["recibidas"], "usadas": r["usadas"],
            "disponibles": r["recibidas"] - r["usadas"], "mxn_recibidos": round(r["recibidas"] * PRECIO_SESION, 2)}


@router.get("/beca/{seudonimo}", response_class=HTMLResponse)
def beca_estudiante(seudonimo: str):
    with _conn() as c:
        if not c.execute("SELECT 1 FROM beneficiarios WHERE seudonimo = ?", (seudonimo,)).fetchone():
            raise HTTPException(404, "Estudiante no registrado en el reparto")
        cods = [dict(r) for r in c.execute(
            "SELECT codigo, usado FROM codigos WHERE seudonimo = ? ORDER BY creado", (seudonimo,))]
    libres = [k for k in cods if not k["usado"]]
    def fila(k: dict) -> str:
        cod = k["codigo"]
        accion = "✅ usada" if k["usado"] else '<a href="/canje/' + cod + '">▶ Usar esta sesión</a>'
        return f"<li>{accion} <small>{cod}</small></li>"
    filas = "".join(fila(k) for k in cods) or "<li>Aún no tienes sesiones asignadas.</li>"
    return f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Tus sesiones regaladas</title>
<style>body{{font-family:system-ui;background:#faf7f2;color:#2b2118;max-width:520px;margin:auto;padding:24px}}
li{{list-style:none;padding:8px 0;border-bottom:1px solid #eee}} a{{color:#8a4b2a;font-weight:600}}
.big{{font-size:2rem;font-weight:700;color:#8a4b2a}}</style>
<h1>🎁 Sesiones regaladas</h1><p>Alguien pagó estas sesiones de <b>conText</b> para ti. No sabe quién eres.</p>
<div class="big">{len(libres)}</div><small>disponibles · {len(cods)} recibidas</small><ul>{filas}</ul></html>"""


@router.get("/canje/{codigo}")
def canje(codigo: str):
    with _conn() as c:
        k = c.execute("SELECT usado FROM codigos WHERE codigo = ?", (codigo,)).fetchone()
        if not k:
            raise HTTPException(404, "Código inexistente")
        if k["usado"]:
            raise HTTPException(410, "Este código ya se usó")
        c.execute("UPDATE codigos SET usado = ? WHERE codigo = ? AND usado IS NULL", (int(time.time()), codigo))
    return RedirectResponse(_destino(), status_code=303)
