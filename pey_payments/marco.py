"""Marco visual común de codi.aideatext.ai, con la identidad de https://aideatext.ai.

Paleta, tipografías (Fraunces + IBM Plex), logotipo y sello NVIDIA Inception salen del
sitio principal (css/portada.css). Todas las páginas públicas de este servicio usan
`pagina()` para que cabecera, pie y aviso de privacidad sean los mismos.
"""
from __future__ import annotations

from html import escape

CSS = """
@font-face{font-family:'Fraunces Variable';src:url(/static/fonts/fraunces-latin-wght-normal.woff2) format('woff2');font-weight:100 900;font-display:swap}
@font-face{font-family:'IBM Plex Sans';src:url(/static/fonts/ibm-plex-sans-latin-400-normal.woff2) format('woff2');font-weight:400;font-display:swap}
@font-face{font-family:'IBM Plex Sans';src:url(/static/fonts/ibm-plex-sans-latin-600-normal.woff2) format('woff2');font-weight:600;font-display:swap}
@font-face{font-family:'IBM Plex Mono';src:url(/static/fonts/ibm-plex-mono-latin-500-normal.woff2) format('woff2');font-weight:500;font-display:swap}
:root{--papel:#fbf8f3;--panel:#f2eee6;--tinta:#16202b;--tinta-suave:#4e5a68;--azul:#0b7ec5;--azul-hondo:#0a5c92;
--rojo:#ae0025;--borde:#e5dfd4;--marco:70rem;--lectura:39rem;--radio:.875rem;--radio-grande:1.25rem;
--serif:'Fraunces Variable','Iowan Old Style',Georgia,serif;--sans:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
--mono:'IBM Plex Mono',ui-monospace,Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--papel);color:var(--tinta);font:1rem/1.6 var(--sans)}
a{color:var(--azul)} a:hover{color:var(--azul-hondo)}
.cabecera,.contenido,.pie{padding-inline:max(clamp(1rem,5vw,2rem),calc((100% - var(--marco))/2))}
.cabecera{display:flex;align-items:center;gap:1.25rem;padding-block:.85rem .7rem;border-bottom:1px solid var(--borde);flex-wrap:wrap}
.marca-lockup{display:flex;align-items:center;gap:.7rem}
.marca{width:clamp(2.9rem,2.2rem + 2.2vw,3.9rem);height:auto}
.sello{height:clamp(1.6rem,1.3rem + 1vw,2.1rem);width:auto}
.menu{margin-left:auto;display:flex;gap:1rem;flex-wrap:wrap;font-size:.92rem}
.menu a{text-decoration:none;color:var(--tinta-suave)} .menu a:hover,.menu a.on{color:var(--azul)}
.contenido{padding-block:2rem 3rem}
h1{font-family:var(--serif);font-weight:650;font-size:clamp(1.7rem,1.3rem + 1.6vw,2.5rem);line-height:1.15;margin:0 0 .6rem;max-width:var(--lectura)}
h2{font-family:var(--serif);font-weight:600;font-size:1.3rem;margin:2rem 0 .6rem}
.entrada{color:var(--tinta-suave);max-width:var(--lectura);font-size:1.05rem}
.cifras{display:flex;flex-wrap:wrap;gap:.8rem;margin:1.6rem 0}
.cifra{background:var(--panel);border:1px solid var(--borde);border-radius:var(--radio-grande);padding:1rem 1.2rem;min-width:9.5rem}
.cifra b{display:block;font-family:var(--serif);font-size:1.9rem;line-height:1.1;color:var(--azul-hondo)}
.cifra span{font-size:.85rem;color:var(--tinta-suave)}
.cifra.acento b{color:var(--rojo)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--borde);border-radius:var(--radio);overflow:hidden}
th,td{padding:.6rem .8rem;text-align:left;border-bottom:1px solid var(--borde)} th{background:var(--panel);font-size:.85rem;color:var(--tinta-suave);font-weight:600}
td.num,th.num{text-align:right;font-family:var(--mono)} tr:last-child td{border-bottom:0}
.tabla{overflow-x:auto}
.nota{font-size:.88rem;color:var(--tinta-suave);max-width:var(--lectura)}
.boton{display:inline-block;background:var(--rojo);color:#fff;text-decoration:none;font-weight:600;padding:.6rem 1.1rem;border-radius:.6rem}
.boton:hover{color:#fff;opacity:.9} .boton.azul{background:var(--azul)}
.tarjeta{background:#fff;border:1px solid var(--borde);border-radius:var(--radio-grande);padding:1.5rem;max-width:var(--lectura)}
.pie{border-top:1px solid var(--borde);padding-block:1.8rem 2.4rem;font-size:.88rem;color:var(--tinta-suave);background:var(--panel)}
.pie nav{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem;margin-bottom:.9rem}
.pie p{margin:.35rem 0;max-width:52rem}
:focus-visible{outline:2px solid var(--azul);outline-offset:2px}
"""

MENU = [("/becas", "Reparto de donaciones"), ("/privacidad", "Datos personales"),
        ("https://context.aideatext.ai", "Donar desde conText")]


def pagina(titulo: str, cuerpo: str, activo: str = "", descripcion: str = "") -> str:
    menu = "".join(
        f'<a href="{u}"{" class=on" if u == activo else ""}>{escape(t)}</a>' for u, t in MENU)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(titulo)} · AIdeaText</title>
<meta name="description" content="{escape(descripcion or titulo)}">
<link rel="icon" href="/static/img/favicon.svg" type="image/svg+xml">
<style>{CSS}</style></head><body>
<header class="cabecera">
  <div class="marca-lockup">
    <a href="https://aideatext.ai"><img class="marca" src="/static/img/logo-aideatext.png" width="156" height="156" alt="AIdeaText"></a>
    <img class="sello" src="/static/img/nvidia-inception-color.svg" width="500" height="216" alt="NVIDIA Inception">
  </div>
  <nav class="menu" aria-label="Secciones">{menu}</nav>
</header>
<main class="contenido">{cuerpo}</main>
<footer class="pie">
  <nav aria-label="Enlaces de AIdeaText">
    <a href="https://aideatext.ai">AIdeaText</a>
    <a href="https://v61-dev.aideatext.ai">La aplicación</a>
    <a href="https://context.aideatext.ai">conText</a>
    <a href="https://aidesk.aideatext.ai">AIDesk</a>
    <a href="/privacidad">Aviso de privacidad</a>
    <a href="mailto:first.contact@aideatext.ai">Escríbenos</a>
  </nav>
  <p>Las donaciones se reciben con <b>CoDi</b> (Banco de México) mediante pey, sin comisiones para quien dona.
  El pago va directo de tu banco a AIdeaText: este sitio nunca ve tus datos bancarios.</p>
  <p>Aquí solo aparecen <b>seudónimos</b> de investigación. Ningún nombre, correo ni texto de estudiantes sale de AIdeaText.
  <a href="/privacidad">Cómo tratamos los datos personales</a>.</p>
  <p>© 2026 AIdeaText · first.contact@aideatext.ai</p>
</footer></body></html>"""


PRIVACIDAD = """
<h1>Aviso de privacidad de las donaciones</h1>
<p class="entrada">Este aviso cubre <b>codi.aideatext.ai</b>, el servicio que recibe las donaciones hechas con CoDi
desde conText y las reparte entre los estudiantes registrados de AIdeaText. Se emite conforme a la Ley Federal de
Protección de Datos Personales en Posesión de los Particulares (LFPDPPP) de México.</p>

<h2>Responsable</h2>
<p class="nota">AIdeaText. Contacto para cualquier asunto de datos personales: <a href="mailto:first.contact@aideatext.ai">first.contact@aideatext.ai</a>.</p>

<h2>Qué datos tratamos</h2>
<div class="tabla"><table>
<tr><th>De quién</th><th>Qué dato</th><th>Para qué</th></tr>
<tr><td>Quien dona</td><td>Monto, fecha y clave de rastreo de la transferencia CoDi que nos entrega pey. Opcionalmente, el nombre que la persona escriba para el muro.</td><td>Saber cuánto se donó y repartirlo. No pedimos ni guardamos cuenta bancaria, CLABE del donante, correo ni teléfono.</td></tr>
<tr><td>Estudiantes registrados en AIdeaText</td><td>Un <b>seudónimo de investigación</b> (p. ej. RES-0001), su institución y una cifra de uso en el ciclo (número de análisis y de turnos con el tutor).</td><td>Repartir la donación por igual entre estudiantes activos y mostrar, al cierre del ciclo, cuánto se aprovechó.</td></tr>
</table></div>
<p class="nota">No tratamos datos personales sensibles. El nombre, el correo y los textos de cada estudiante se quedan
dentro de AIdeaText y <b>nunca</b> llegan a este servicio ni a quien dona.</p>

<h2>Finalidades</h2>
<p class="nota">Primarias: recibir donaciones, repartirlas en partes iguales y rendir cuentas públicamente con cifras
agregadas y seudónimos. No hay finalidades secundarias: no hacemos mercadotecnia ni perfiles, y no vendemos datos.</p>

<h2>Transferencias</h2>
<p class="nota">El cobro lo procesa <b>pey</b> sobre <b>CoDi</b> de Banco de México. Fuera de eso no transferimos datos a terceros,
salvo requerimiento de autoridad competente.</p>

<h2>Derechos ARCO y revocación</h2>
<p class="nota">Puedes ejercer tus derechos de Acceso, Rectificación, Cancelación y Oposición, o revocar tu consentimiento,
escribiendo a <a href="mailto:first.contact@aideatext.ai">first.contact@aideatext.ai</a> con el asunto «Derechos ARCO».
Respondemos en un máximo de 20 días hábiles. Si eres estudiante y no quieres aparecer en el reparto, basta con pedirlo:
tu seudónimo se retira de la tabla pública.</p>

<h2>Conservación</h2>
<p class="nota">Las cifras de cada ciclo se conservan mientras sean necesarias para rendir cuentas a quienes donaron y
a las instituciones. El seudónimo de un estudiante que deja de estar activo sale del reparto en la siguiente actualización.</p>

<h2>Cambios a este aviso</h2>
<p class="nota">Cualquier cambio se publica en esta misma página. Última actualización: 8 de noviembre de 2026.</p>
"""
