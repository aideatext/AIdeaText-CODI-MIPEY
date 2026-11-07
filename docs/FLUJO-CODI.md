# Flujo de cobro CoDi con pey, desde cero

## Quién es quién

| Actor | Qué es | Qué NO es |
|---|---|---|
| **Banco comercial** (BBVA, Banorte, Santander, Banamex, etc.) | Donde AIdeaText tiene su cuenta; de ahí sale la **CLABE** (18 dígitos) | — |
| **Banxico / CoDi** | El riel público de pagos instantáneos (corre sobre SPEI). Gratis | **No** se abre "una cuenta en Banxico" |
| **pey** (Koshi SA de CV) | Servicio **hospedado** que da de alta la CLABE en CoDi y expone una API para generar cobros | **No** se instala en nuestro servidor. Hoy la API es gratuita |
| **Servidor de AIdeaText** | Llama a la API de pey con la API key, guarda órdenes y otorga acceso/créditos | — |
| **Pagador** | Persona con app bancaria mexicana y CoDi activo, normalmente en su celular | — |

## Paso a paso

1. **Cuenta bancaria normal** a nombre de AIdeaText (persona física o ETAITE SAS) → CLABE.
2. **En pey** (portal.mipey.mx → Finanzas) se registra esa CLABE como cuenta de pago `codi`.
   pey la inscribe en CoDi ante Banxico: **≈5 días hábiles**. Ese es el plazo, no "abrir cuenta en Banxico".
   *Hackathon:* las CLABEs pre-autorizadas de los organizadores ya están activas → sin espera.
3. **En pey → Desarrollador → Crear API Key**, ligada a esa cuenta `codi` (y opcionalmente a una `stripe` para tarjetas).
   La "tienda" del portal es nuestro perfil de comercio; **API key ↔ CLABE**: todo cobro hecho con esa key cae en esa CLABE.
4. **Nuestro servidor genera el cobro** llamando a pey:
   - `POST /codi/qr` → QR (fijo o de monto libre; reutilizable si no expira).
   - `POST /codi/pn` → solicitud al **número de celular** del pagador.
   - `POST /payment-link/create` → página de pago de pey (CoDi + tarjeta).
5. **El pagador paga desde su celular**, en la app de su banco (menú CoDi):
   - Si ve el QR en **otra pantalla** (proyector, laptop, cartel impreso) → lo escanea.
   - Si ya está **en su celular** (no puede escanear su propia pantalla) → **push al número** o **payment link**.
6. **Confirmación**: pey avisa por webhook firmado (`codi.qr.payment_received`, `codi.pn.payment_received`,
   `payment_link.status_updated`) o lo consultamos (`GET /transaction/...`). El dinero ya está en la CLABE.
7. **AIdeaText entrega**: créditos de tutor, acceso por periodo, o el agradecimiento en el muro.

```
Pagador (celular, app bancaria)
     │ escanea QR / aprueba push
     ▼
Banxico CoDi ──► SPEI ──► CLABE de AIdeaText (dinero, en segundos)
     │
     ▼
pey ──webhook firmado──► servidor AIdeaText ──► créditos / acceso / muro
 ▲                                │
 └──── API key (Bearer) ◄─────────┘  crea QR, push o link
```

## Costos
- API de pey: gratis hoy (sin alta, sin mensualidad, sin costo por petición).
- CoDi: sin comisión. Tarjeta vía payment link (Stripe): con comisión.
- No hay sandbox: pruebas con $0.01 MXN en producción.
