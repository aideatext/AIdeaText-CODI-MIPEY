# Guía para agentes de implementación

Proyecto: integración de cobros CoDi (vía pey) en AIdeaText. Hackathon DevDay Exchange Community CDMX (entrega dom 8-nov-2026 13:00).

## Leer primero
1. `docs/FLUJO-CODI.md` — quién es quién y el flujo completo.
2. `CAFE-CODI.md` — el caso de demo "Invítame un café".
3. `README.md` — ruta por fases y modelo de cobro.
4. `docs/PLAN-SESION-PENDIENTE.md` — concepto "sesión pendiente" y niveles 0–4.

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
