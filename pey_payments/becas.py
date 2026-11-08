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
from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from . import store
from .marco import PRIVACIDAD, pagina

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
        f'<tr><td><a href="/beca/{escape(p["seudonimo"])}">{escape(p["seudonimo"])}</a></td>'
        f'<td>{escape(p["institucion"] or "")}</td><td class="num">${p["mxn_recibidos"]:.4f}</td>'
        f'<td class="num">{p["uso"]}</td></tr>' for p in b["por_estudiante"])
    cuerpo = f"""
<h1>Donaciones a AIdeaText · ciclo {b['ciclo']}</h1>
<p class="entrada">Estudiantes de distintos estados de México usan AIdeaText gracias a tu donación. Lo que se dona
con CoDi desde el botón «Donación» de <a href="https://context.aideatext.ai">conText</a> se reparte
<b>en partes iguales</b> entre todos los estudiantes registrados, sin importar cuánto lo usen.</p>
<div class="cifras">
  <div class="cifra acento"><b>${b['total_mxn']:.2f}</b><span>MXN donados</span></div>
  <div class="cifra"><b>{b['beneficiarios']}</b><span>estudiantes registrados</span></div>
  <div class="cifra"><b>${b['mxn_por_estudiante']:.4f}</b><span>MXN para cada uno</span></div>
  <div class="cifra"><b>{b['uso_total']}</b><span>actividades en el ciclo</span></div>
</div>
<p><a class="boton" href="https://context.aideatext.ai">Haz una donación desde conText</a></p>
<h2>Reparto y uso por estudiante</h2>
<div class="tabla"><table>
<tr><th>Estudiante (seudónimo)</th><th>Institución</th><th class="num">Subvención</th><th class="num">Uso en el ciclo</th></tr>
{filas}</table></div>
<p class="nota">Uso = análisis de texto y turnos con el tutor en AIdeaText durante el ciclo; se actualiza cada 15 minutos.
La tabla va ordenada por uso: al cierre del ciclo muestra quién aprovechó más la subvención y quién menos.
Los montos se recalculan con cada donación. <a href="/becas.json">Datos abiertos en JSON</a>.</p>"""
    return pagina(f"Donaciones a AIdeaText · ciclo {b['ciclo']}", cuerpo, "/becas",
                  "Reparto en partes iguales de las donaciones CoDi entre estudiantes de AIdeaText")


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
    cuerpo = f"""
<h1>🎁 Tu uso de AIdeaText está subvencionado</h1>
<p class="entrada">Personas que no conoces donaron con CoDi para que estudiantes como tú sigan usando AIdeaText.
Lo donado se reparte por igual entre los {d['beneficiarios']} estudiantes registrados. Nadie sabe quién eres.</p>
<div class="cifras">
  <div class="cifra acento"><b>${d['mxn_recibidos']:.4f}</b><span>MXN de subvención · ciclo {d['ciclo']}</span></div>
  <div class="cifra"><b>{d['uso']}</b><span>tu actividad en el ciclo</span></div>
</div>
<p><a class="boton azul" href="{V61_URL}">Seguir trabajando en AIdeaText →</a></p>
<p class="nota">Tu actividad cuenta análisis y turnos con el tutor. Aquí solo aparece tu seudónimo
<b>{escape(seudonimo)}</b>. <a href="/becas">Ver el reparto completo</a>.</p>"""
    return pagina("Tu uso de AIdeaText está subvencionado", cuerpo)


@router.get("/privacidad", response_class=HTMLResponse)
def privacidad():
    return pagina("Aviso de privacidad", PRIVACIDAD, "/privacidad")
