"""Subvención del uso de AIdeaText (v61) con donaciones CoDi, repartida por igual.

La donación no compra sesiones sueltas ni otra herramienta: paga el uso de AIdeaText
(https://v61-dev.aideatext.ai, que ya incluye conText) para los estudiantes activos.

Flujo:
  1. `scripts/sincronizar_estudiantes_v61.py` (cada 15 min) copia de v61 SOLO el seudónimo de
     investigación (RES-0004…), la institución y una cifra de uso del ciclo (análisis + turnos con
     el tutor). Ni nombre, ni correo, ni contenido.
  2. Reparto IGUALITARIO: lo donado en el ciclo se divide en partes iguales entre todos los
     estudiantes activos, sin mirar cuánto usan. Nadie tiene que "canjear" nada.
  3. Cada estudiante ve en su cabecera de v61: "Tu uso de AIdeaText está subvencionado · $X MXN".
  4. Al cierre del ciclo /becas ordena por uso: quién aprovechó más la subvención y quién menos.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from . import store

router = APIRouter()
CICLO = os.getenv("CICLO", "2026-2")
V61_URL = os.getenv("V61_URL", "https://v61-dev.aideatext.ai")

SCHEMA = """
CREATE TABLE IF NOT EXISTS beneficiarios (
  seudonimo   TEXT PRIMARY KEY,          -- investigacion_id de v61; nunca nombre ni correo
  institucion TEXT,
  activo      INTEGER NOT NULL DEFAULT 1
);
"""


def _conn():
    c = store.conn()
    c.executescript(SCHEMA)
    cols = {r[1] for r in c.execute("PRAGMA table_info(beneficiarios)")}
    if "uso" not in cols:
        c.execute("ALTER TABLE beneficiarios ADD COLUMN uso INTEGER NOT NULL DEFAULT 0")
    return c


def sincronizar(beneficiarios: list[dict]) -> int:
    """Reemplaza el padrón de estudiantes activos y su uso del ciclo."""
    with _conn() as c:
        c.execute("UPDATE beneficiarios SET activo = 0")
        for b in beneficiarios:
            c.execute("INSERT INTO beneficiarios(seudonimo, institucion, activo, uso) VALUES (?,?,1,?) "
                      "ON CONFLICT(seudonimo) DO UPDATE SET institucion=excluded.institucion, activo=1, uso=excluded.uso",
                      (b["seudonimo"], b.get("institucion"), int(b.get("uso") or 0)))
    return len(beneficiarios)


def resumen(total_mxn: float) -> dict:
    with _conn() as c:
        por = [dict(r) for r in c.execute(
            "SELECT seudonimo, institucion, uso FROM beneficiarios WHERE activo = 1 ORDER BY uso DESC, seudonimo")]
    n = len(por)
    parte = round(total_mxn / n, 4) if n else 0.0
    for p in por:
        p["mxn_recibidos"] = parte
    return {"ciclo": CICLO, "total_mxn": total_mxn, "beneficiarios": n, "mxn_por_estudiante": parte,
            "uso_total": sum(p["uso"] for p in por), "por_estudiante": por}


def _total() -> float:
    from .donaciones import cafe_feed
    return cafe_feed()["total"]


@router.get("/becas.json")
def becas():
    return resumen(_total())


@router.get("/becas", response_class=HTMLResponse)
def becas_html():
    b = becas()
    filas = "".join(
        f'<tr><td><a href="/beca/{p["seudonimo"]}">{p["seudonimo"]}</a></td><td>{p["institucion"]}</td>'
        f'<td>${p["mxn_recibidos"]:.4f}</td><td>{p["uso"]}</td></tr>' for p in b["por_estudiante"])
    return f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Subvención de AIdeaText · ciclo {b['ciclo']}</title>
<style>body{{font-family:system-ui;background:#faf7f2;color:#2b2118;max-width:720px;margin:auto;padding:24px}}
table{{width:100%;border-collapse:collapse;background:#fff}} td,th{{padding:8px;border-bottom:1px solid #eee;text-align:left}}
a{{color:#8a4b2a}} .k{{display:inline-block;margin:0 18px 12px 0}} .k b{{font-size:1.6rem;color:#8a4b2a;display:block}}</style>
<h1>Donaciones a AIdeaText · ciclo {b['ciclo']}</h1>
<p>Las donaciones hechas con CoDi desde el botón «Donación» de <a href="https://context.aideatext.ai">conText</a> se reparten <b>en partes iguales</b> entre todos los estudiantes activos de
<a href="{V61_URL}">AIdeaText</a>, sin importar cuánto lo usen. Al cierre del ciclo esta tabla muestra quién
aprovechó más la subvención y quién menos. Solo seudónimos: nadie aquí ve nombres.</p>
<div><span class="k"><b>${b['total_mxn']:.2f}</b>donado</span><span class="k"><b>{b['beneficiarios']}</b>estudiantes</span>
<span class="k"><b>${b['mxn_por_estudiante']:.4f}</b>para cada uno</span><span class="k"><b>{b['uso_total']}</b>actividades en el ciclo</span></div>
<table><tr><th>Estudiante</th><th>Institución</th><th>Subvención</th><th>Uso en el ciclo</th></tr>{filas}</table>
<p><small>Uso = análisis de texto + turnos con el tutor en AIdeaText durante el ciclo. Se actualiza cada 15 minutos.</small></p>
<p><a href="https://context.aideatext.ai">← Donar desde conText (botón «Donación»)</a> · <a href="/becas.json">datos en JSON</a></p></html>"""


def _uno(seudonimo: str) -> dict:
    b = becas()
    p = next((p for p in b["por_estudiante"] if p["seudonimo"] == seudonimo), None)
    if not p:
        raise HTTPException(404, "Estudiante no registrado en la subvención")
    return {"ciclo": b["ciclo"], "mxn_recibidos": p["mxn_recibidos"], "uso": p["uso"],
            "beneficiarios": b["beneficiarios"], "subvencionado": p["mxn_recibidos"] > 0}


@router.get("/beca/{seudonimo}.json")
def beca_estudiante_json(seudonimo: str):
    """Lo que v61 muestra en la cabecera del estudiante. Solo cifras."""
    return _uno(seudonimo)


@router.get("/beca/{seudonimo}", response_class=HTMLResponse)
def beca_estudiante(seudonimo: str):
    d = _uno(seudonimo)
    return f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Tu uso de AIdeaText está subvencionado</title>
<style>body{{font-family:system-ui;background:#faf7f2;color:#2b2118;max-width:520px;margin:auto;padding:24px}}
a{{color:#8a4b2a;font-weight:600}} .big{{font-size:2rem;font-weight:700;color:#8a4b2a}}</style>
<h1>🎁 Tu uso de AIdeaText está subvencionado</h1>
<p>Personas que no conoces donaron por CoDi para que estudiantes como tú sigan usando AIdeaText.
Lo donado se reparte por igual entre los {d['beneficiarios']} estudiantes activos. Nadie sabe quién eres.</p>
<div class="big">${d['mxn_recibidos']:.4f} MXN</div><small>has recibido en el ciclo {d['ciclo']}</small>
<p>Tu actividad en el ciclo: <b>{d['uso']}</b> (análisis y turnos con el tutor).</p>
<p><a href="{V61_URL}">Seguir trabajando en AIdeaText →</a></p></html>"""
