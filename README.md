# AIdeaText × pey (CoDi) — ruta de implementación de pagos

Prototipo para el **DevDay Exchange Community Hackathon CDMX** (7 nov 2026; entrega: **dom 8 nov, 1:00 PM**)
y, al mismo tiempo, primer paso real para cobrar en AIdeaText.

## 1. Qué ofrece pey y qué usamos

| Servicio pey | Endpoint | Uso en AIdeaText |
|---|---|---|
| Payment link (checkout hospedado: CoDi, tarjeta, Apple/Google Pay) | `POST /payment-link/create` | Pago web de planes desde la app |
| QR CoDi | `POST /codi/qr` | QR en aula, pantalla del tutor, material impreso |
| Push CoDi al celular | `POST /codi/pn` | Cobro al teléfono del estudiante o del tutor/familia |
| Webhooks firmados (Standard Webhooks) | `payment_link.status_updated`, `codi.qr.payment_received`, `codi.pn.payment_received` | Activar créditos/acceso al confirmarse el pago |
| Transacciones | `GET /transaction/...` | Conciliación y reportes |

Condiciones clave: API **gratuita y sin comisión en CoDi**; **no hay sandbox** (se prueba en producción con $0.01);
**no hay suscripciones** (la recurrencia la maneja AIdeaText); CoDi liquida **solo en MXN a cuentas mexicanas**.

## 2. Arquitectura

```
Streamlit (v5 / tutor) ──► FastAPI AIdeaText ──► api.pey.mx
        ▲   polling estado          │  include_router(pey_payments)
        │                           ▼
        └──── créditos/acceso ◄── /webhooks/pey ◄── pey (evento firmado)
```

- `pey_payments/client.py` — cliente de la API.
- `pey_payments/router.py` — endpoints `/payments/*` y `/webhooks/pey` (verifica firma, idempotencia, monto).
- `pey_payments/store.py` — órdenes, eventos y derechos (`credits`, `valid_until`). SQLite en el prototipo; se cambia por DocumentDB.
- Conciliación: `clientReferenceId` (link) / `numRef` + `metadata.orderId` (CoDi) = nuestra `order_id`.

## 3. Ruta por fases

### Fase 0 — Hoy, en el hackathon (≈2 h)
1. Cuenta en **portal.mipey.mx** → Finanzas → agregar cuenta de pago:
   - `codi`: CLABE mexicana. Activación Banxico ≈ **5 días hábiles**. Mientras tanto, usar la **cuenta de prueba** que da pey en la documentación (el dinero no se devuelve: solo centavos).
   - `stripe` (opcional) para tarjetas en el payment link.
2. Desarrollador → **Crear API Key** (ligada a la cuenta) → engrane → **Crear Webhook** con la URL pública → copiar el secreto.
3. Local:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env            # llenar PEY_API_KEY, PEY_WEBHOOK_SECRET, PUBLIC_BASE_URL
   python scripts/test_webhook_local.py   # sin dinero: firma, reintentos, créditos
   uvicorn app:app --port 8000
   cloudflared tunnel --url http://localhost:8000   # o ngrok; esa URL HTTPS va al webhook y a PUBLIC_BASE_URL
   ```
4. Prueba real con 1 centavo: `python scripts/smoke_test_pey.py qr` → escanear con la app bancaria → ver el webhook llegar.
5. Demo: abrir `/demo` → los tres flujos (checkout, QR, push) y el estado cambiando a **paid** con los créditos otorgados.

### Fase 1 — Integración en AIdeaText (semana 1)
- `app.include_router(payments_router)` en el FastAPI de `tutor.aideatext.ai`; ruta `/webhooks/pey` expuesta por Nginx con HTTPS.
- Streamlit: botón "Comprar sesiones" → llama `/payments/checkout` o `/payments/codi/qr`, muestra QR y hace polling de `/payments/orders/{id}`.
- Antes de cada sesión del tutor: consultar `/payments/entitlements/{user_id}` y descontar un crédito.
- Pasar `store.py` a la base de producción; logs de webhooks; secretos en AWS Secrets Manager.

### Fase 2 — Cuenta y fiscal (semanas 1–3, en paralelo)
- Registrar la **CLABE de ETAITE SAS** (`entity: BUSINESS`) cuando esté su cuenta bancaria; mientras, se puede operar con la cuenta de persona física (`PERSON`).
- Definir facturación (CFDI) de los cobros: pey no la emite; hay que resolverla aparte.

### Fase 3 — Modelo de cobro (mes 1)
| Segmento | Canal | Producto |
|---|---|---|
| Estudiante individual (MX) | Push CoDi / QR | Paquetes de sesiones (créditos) — sin comisión |
| Escuelas/docentes (MX) | Payment link o QR impreso por grupo | Acceso por periodo (`valid_until`) |
| Instituciones fuera de México (p. ej. UNIFE, Perú) | Payment link con tarjeta (Stripe) o factura/transferencia | Licencia institucional |
| Recurrente | Recordatorio + nuevo push/link al vencer | "Suscripción" gestionada por AIdeaText |

## 4. Riesgos y límites
- **Sin sandbox**: cada prueba mueve dinero real → siempre $0.01 y la cuenta de prueba.
- **CoDi = México**: no sirve para pagadores fuera del país; para ellos, tarjeta vía payment link.
- **Sin suscripciones** nativas: renovación manual por AIdeaText.
- `payment-link/update` solo cambia el monto mientras el link está `pending`.
- QR con `amount = 0` permite que el pagador elija el monto: el webhook valida que cubra la orden.

## 5. Pitch para el jurado (bien público)
"Pagar el acceso a un tutor de escritura con IA debería costar lo mismo que el acceso: cero comisiones.
AIdeaText usa CoDi para que estudiantes y escuelas paguen sesiones de tutoría con un QR en el aula o una
solicitud al celular, sin tarjeta y sin intermediarios; el pago activa al instante los créditos del tutor."
