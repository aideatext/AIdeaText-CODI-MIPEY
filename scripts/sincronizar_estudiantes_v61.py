"""Copia de AIdeaText v61 el padrón de estudiantes activos que pueden recibir sesiones pendientes.

    python scripts/sincronizar_estudiantes_v61.py            # contenedor v61-dev-pg-1 (demos)
    V61_PG_CONTAINER=v61-prod-pg-1 python scripts/sincronizar_estudiantes_v61.py

Solo se copia el seudónimo de investigación (estudiantes.investigacion_id), la institución
y una cifra de uso (análisis + turnos con el tutor desde CICLO_INICIO).
Nunca nombre, correo ni el id interno. Se lee por `docker exec ... psql` porque la base de v61
no publica puertos (ver docs de v61: v61-despliegue-cloudflare-ec2).
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
from pey_payments import becas  # noqa: E402

CONT = os.getenv("V61_PG_CONTAINER", "v61-dev-pg-1")
INICIO = os.getenv("CICLO_INICIO", "2026-08-01")  # desde cuándo cuenta el uso del ciclo
SQL = ("SELECT e.investigacion_id, e.institucion_id, "
       f"(SELECT count(*) FROM analisis a WHERE a.estudiante_id = e.id AND a.creado >= '{INICIO}') + "
       f"(SELECT count(*) FROM interacciones i WHERE i.estudiante_id = e.id AND i.creado >= '{INICIO}') "
       "FROM estudiantes e WHERE e.estado = 'activo' AND e.investigacion_id IS NOT NULL ORDER BY 1")

out = subprocess.run(
    ["docker", "exec", CONT, "sh", "-c",
     f'psql -U "${{POSTGRES_USER:-postgres}}" -d "${{POSTGRES_DB:-postgres}}" -AtF"|" -c "{SQL}"'],
    check=True, capture_output=True, text=True).stdout
filas = [dict(zip(("seudonimo", "institucion", "uso"), l.split("|"))) for l in out.splitlines() if l.strip()]
n = becas.sincronizar(filas)
print(f"{n} estudiantes activos de {CONT} con uso subvencionado (uso desde {INICIO}):")
for f in filas:
    print(f"  {f['seudonimo']}  ({f['institucion']})  uso={f['uso']}")
