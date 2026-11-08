"""Reparto automático de "sesiones pendientes" entre estudiantes activos de AIdeaText v61.

Flujo (Nivel 1, sin tocar conText):
  1. `scripts/sincronizar_estudiantes_v61.py` copia de v61 SOLO el seudónimo de investigación
     (`estudiantes.investigacion_id`, p. ej. RES-0004) de los estudiantes activos. Ni nombre ni correo.
  2. Cada sesión financiada (total donado // PRECIO_SESION) se convierte en un código de un solo uso.
  3. El código se asigna al estudiante con menos códigos (empate: el seudónimo menor). Es equitativo
     y determinista: el mismo dinero produce siempre el mismo reparto.
  4. El estudiante ve sus sesiones en /beca/{seudonimo}. Al pulsar "Usar", /canje/{codigo} marca el
     código como usado (una sola vez) y redirige a conText con ?ref=sesion-pendiente.
"""
from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from . import store

router = APIRouter()

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
  usado       INTEGER                    -- epoch del canje; NULL = disponible
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
    """Crea y asigna los códigos que falten hasta igualar las sesiones financiadas. Devuelve cuántos creó."""
    nuevos = 0
    with _conn() as c:
        ya = c.execute("SELECT COUNT(*) FROM codigos").fetchone()[0]
        for _ in range(max(0, sesiones_financiadas - ya)):
            fila = c.execute(
                "SELECT b.seudonimo FROM beneficiarios b LEFT JOIN codigos k ON k.seudonimo = b.seudonimo "
                "WHERE b.activo = 1 GROUP BY b.seudonimo ORDER BY COUNT(k.codigo), b.seudonimo LIMIT 1").fetchone()
            if not fila:
                break  # sin beneficiarios: el dinero queda como saldo hasta que haya a quién asignarlo
            c.execute("INSERT INTO codigos(codigo, seudonimo, creado) VALUES (?,?,?)",
                      (secrets.token_urlsafe(6), fila["seudonimo"], int(time.time())))
            nuevos += 1
    return nuevos


def resumen() -> dict:
    with _conn() as c:
        asignadas = c.execute("SELECT COUNT(*) FROM codigos").fetchone()[0]
        usadas = c.execute("SELECT COUNT(*) FROM codigos WHERE usado IS NOT NULL").fetchone()[0]
        por = [dict(r) for r in c.execute(
            "SELECT b.seudonimo, b.institucion, COUNT(k.codigo) AS asignadas, COUNT(k.usado) AS usadas "
            "FROM beneficiarios b LEFT JOIN codigos k ON k.seudonimo = b.seudonimo "
            "WHERE b.activo = 1 GROUP BY b.seudonimo ORDER BY b.seudonimo")]
    return {"beneficiarios": len(por), "asignadas": asignadas, "canjeadas": usadas, "por_estudiante": por}


def _destino() -> str:
    from .donaciones import CONTEXT_REF, CONTEXT_URL
    return f"{CONTEXT_URL}/?ref={CONTEXT_REF}"


@router.get("/becas")
def becas():
    from .donaciones import cafe_feed  # cafe_feed ya llama a repartir()
    f = cafe_feed()
    return {"sesiones_financiadas": f["sesiones_financiadas"], **resumen()}


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
