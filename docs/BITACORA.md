# Bitácora — Sesión pendiente (CoDi × conText)

## 2026-11-07 · Hecho

- Pruebas locales: `python scripts/test_webhook_local.py` → `OK`.
- QR CoDi permanente de monto libre creado con `scripts/crear_qr_cafe.py` (archivos locales `donacion_qr.json` y `cafe_qr.png`, fuera del repo).
- **conText** (repo `aideatext/conText-HackTheAndes`, commits `2c1486f` y `cd1134f`, ya en `main`):
  - Botón de apoyo en la cabecera, a la derecha de "Llevarme mi resumen". Abre una ventana con el QR CoDi.
  - Dos modos por variable de entorno, sin tocar código: `cafe` ("Invítame un café") y `beca` ("Regala sesiones a estudiantes").
  - Aviso en el pie para quien llega con `?ref=sesion-pendiente`: "Esta sesión te la regaló alguien".
  - Rutas nuevas: `GET /api/apoyo` (configuración) y `GET /api/apoyo/qr.png` (imagen). conText no procesa pagos.
  - Sin `APOYO_MODO` o sin `APOYO_QR_PNG` el botón no aparece y conText funciona como antes.

## Pendiente (para terminar)

### 1. Activar el botón en Render (servicio conText)
En **Environment**:

| Variable | Valor |
|---|---|
| `APOYO_MODO` | `cafe` (después `beca`) |
| `APOYO_QR_PNG` | salida de `base64 -w0 cafe_qr.png` (una línea, ≈4040 caracteres). Es un secreto: apunta a la cuenta. |
| `APOYO_PAGINA_URL` | opcional, `https://<servicio-pagos>/cafe` |
| `APOYO_PRECIO` | opcional, `10` |

Guardar con **Save, rebuild and deploy**. Verificar: `https://context.aideatext.ai/api/apoyo` responde `"modo":"cafe"`.

### 2. Confirmar `USO_TOKEN`
Confirmar que existe en el servicio conText y copiar el mismo valor a `CONTEXT_USO_TOKEN` en el `.env` de este repo (para contar "sesiones usadas").

### 3. Prueba real de $1
Escanear el QR desde una app bancaria y pagar $1. Luego:
```bash
python scripts/crear_qr_cafe.py --ver   # debe listar la transacción
```
Si la respuesta de pey no coincide con `pey_payments/client.py`, ajustar el cliente y documentarlo aquí.

### 4. Publicar el servicio de pagos (opcional)
Web Service Python en Render: `uvicorn app:app --host 0.0.0.0 --port $PORT`, con las variables de `.env` como secretos.
Después: configurar el webhook de pey a `https://<servicio>/webhooks/pey` y poner esa URL `/cafe` en `APOYO_PAGINA_URL`.

### 5. Demostrar el criterio de terminado
- Una donación real de $1 sube "sesiones financiadas" en `/cafe`.
- Una sesión abierta con `https://context.aideatext.ai/?ref=sesion-pendiente` que conversa sube "usadas".

### 6. Cambio a esquema de subvención (después del hackathon)
- `APOYO_MODO=beca` en Render.
- Nivel 1 de `PLAN-SESION-PENDIENTE.md`: códigos de canje de un solo uso en lugar del enlace público.
- Persistencia del uso en conText (Azure Tables) para que "usadas" no se reinicie.

### Notas operativas
- Push a GitHub: por HTTPS no hay credenciales en el EC2. Usar SSH: `git push git@github.com:aideatext/<repo>.git HEAD:main`.
- No hay acceso a Render desde el agente. Con una API key de Render en `.env`, el agente puede configurar variables y desplegar.

## 2026-11-08 · Revisión de producción

- `https://context.aideatext.ai/api/apoyo` responde `"modo":"cafe"`, pero en Render se pegaron mal dos valores:
  - `APOYO_QR_PNG` tenía el **texto del comando** (`base64 -w0 cafe_qr.png`) y no su salida, así que el QR servido eran 13 bytes de basura.
  - `APOYO_PAGINA_URL` tenía el marcador literal `https://<servicio-pagos>/cafe`.
- conText `89bac9c`: ahora valida la firma PNG y rechaza URLs con `<>`. Con un valor mal pegado el botón se oculta en vez de mostrar un QR roto.
- Corrección: pegar en `APOYO_QR_PNG` el contenido de `cafe_qr.b64` (4040 caracteres, empieza con `iVBORw0KGgo`) y borrar `APOYO_PAGINA_URL` hasta publicar el servicio de pagos.
- `.env` de este repo: `CONTEXT_USO_TOKEN` sigue vacío.

- 05:12 UTC: corregido en Render. `/api/apoyo` → `{"modo":"cafe","pagina":null}`; `/api/apoyo/qr.png` (3028 bytes) es idéntico byte a byte a `cafe_qr.png`. Botón de apoyo operativo en producción.

- 13:45 UTC: **primer pago real** por el QR permanente. pey `01M6XPH4SA1B8TY9V0SD55891E`, `PAID`, $0.01 MXN CODI, `externalMetadata.tipo=donacion`. La respuesta coincide con `pey_payments/client.py` (sin cambios).
- Para la demo con centavos: `PRECIO_SESION=0.01` en `.env` (local/Render, no en código). Con eso `/cafe` muestra **1 sesión financiada**. Para operación real volver a `10`.
- Simulación del estudiante: abrir `https://context.aideatext.ai/?ref=sesion-pendiente` (ventana privada) y conversar. conText lo cuenta en `/api/uso` → `porRef.sesion-pendiente.conversaron`; `/cafe` lo muestra como "usadas" en cuanto `CONTEXT_USO_TOKEN` esté en `.env`.
