# Guía para agentes de implementación

Proyecto: integración de cobros CoDi (vía pey) en AIdeaText. Hackathon DevDay Exchange Community CDMX (entrega dom 8-nov-2026 13:00).

## Tarea actual (hackathon): "Sesión pendiente" Nivel 0 sobre conText

El código base ya existe y pasa las pruebas locales. Falta **ponerlo a funcionar con la API real** y dejarlo listo para la demo:

1. **Configurar**: copiar `.env.example` a `.env`. El humano pega `PEY_API_KEY` (ligada a una CLABE pre-autorizada) y `CONTEXT_USO_TOKEN` (= `USO_TOKEN` del servicio conText en Render). El agente **no** pide ni escribe esas claves en el chat ni en commits.
2. **Pruebas locales sin dinero**: `pip install -r requirements.txt` → `python scripts/test_webhook_local.py` (debe decir `OK`).
3. **Prueba real de 1 centavo**: `python scripts/smoke_test_pey.py qr` → escanear `qr.png` con una app bancaria → `python scripts/smoke_test_pey.py tx` debe listar la transacción. Si la API responde distinto a lo esperado en `pey_payments/client.py`, ajustar el cliente a la respuesta real y documentarlo.
4. **QR permanente**: `python scripts/crear_qr_cafe.py` (monto libre, sin expiración).
5. **Demo**: `uvicorn app:app --port 8000` → `/cafe` muestra QR, montos fijos (10 / 50 / 300 MXN), push al celular y el muro "N sesiones financiadas · M usadas".
   Canje: `https://context.aideatext.ai/?ref=sesion-pendiente` (conText ya cuenta ese `ref` en `/api/uso`; **no se modifica conText**).
6. **Publicar** (opcional): Web Service Python en Render (`uvicorn app:app --host 0.0.0.0 --port $PORT`), variables como secretos de Render; luego configurar el webhook de pey con `https://<servicio>/webhooks/pey`.

**Criterio de terminado**: una donación real de $1 sube "sesiones financiadas" en `/cafe`, y una sesión abierta con el enlace de canje sube "usadas".
**Fuera de alcance hoy**: códigos de canje de un solo uso, libro verificable, constancias (Niveles 1–2 de `docs/PLAN-SESION-PENDIENTE.md`); concursa.

## Leer primero
1. `docs/FLUJO-CODI.md` — quién es quién y el flujo completo.
2. `CAFE-CODI.md` — el caso de demo "Invítame un café".
3. `README.md` — ruta por fases y modelo de cobro.
4. `docs/PLAN-SESION-PENDIENTE.md` — concepto "sesión pendiente" y niveles 0–4.
5. `docs/OPERACION-HACKATHON.md` — qué CLABE usar y cómo se conecta con conText (Nivel 0).

## Estructura
- `pey_payments/client.py` — cliente de la API pey (`https://api.pey.mx`, Bearer).
- `pey_payments/router.py` — `/payments/*` (órdenes, checkout, QR, push) y `/webhooks/pey` (Standard Webhooks, idempotente).
- `pey_payments/donaciones.py` — `/cafe` (QR monto libre, montos fijos, push al celular, muro en vivo).
- `pey_payments/store.py` — SQLite: órdenes, eventos de webhook, derechos (créditos / vigencia).
- `app.py` — app FastAPI de demo. En AIdeaText real: `include_router` en el backend existente.

## Reglas
- **Nunca** subir credenciales, `.env`, CLABEs ni datos de personas. Ver `.gitignore`.
- No hay sandbox: toda prueba real usa $0.01 MXN.
- Antes de commitear: `python scripts/test_webhook_local.py` debe imprimir `OK`.
- Documentación en español; debe servir a la vez a usuarios operativos y a lectores de convocatorias/investigación.
