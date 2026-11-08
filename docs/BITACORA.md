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

## 2026-11-08 · Reparto automático a estudiantes de v61 (Nivel 1, sin tocar conText)
- `scripts/sincronizar_estudiantes_v61.py` lee de `v61-dev-pg-1` solo `investigacion_id` e institución de los estudiantes activos (6 en dev: RES-0001…0006). Sin nombres ni correos.
- `pey_payments/becas.py`: cada sesión financiada = 1 código de un solo uso, asignado al estudiante con menos códigos (equitativo y determinista). Se ejecuta cada vez que se consulta `/cafe/feed`.
- Rutas: `/becas` (reparto), `/beca/{seudonimo}` (pantalla del estudiante), `/canje/{codigo}` (marca usado y redirige a conText con `?ref=sesion-pendiente`; segundo uso → 410).
- Verificado con el pago real de $0.01: 1 financiada → asignada a RES-0001 → canje 303 → recanje 410.
- Pendiente: que v61 muestre el enlace `/beca/{investigacion_id}` dentro de la cuenta del estudiante, y publicar este servicio.

### Criterio de reparto: igualitario por rondas (decidido 14:30 UTC)
- Cada ronda da 1 sesión a **cada** estudiante activo, sin mirar cuántas tiene ni cuántas usó. Solo se reparten rondas completas; el sobrante queda como saldo.
- Cada código lleva `ciclo` (`CICLO`, por defecto `2026-2`) y `ronda`. Al cierre del ciclo `/becas` ordena por uso: quién usó más y quién menos.
- Páginas públicas: `/cafe` (donar), `/becas` (reparto y uso por estudiante, solo seudónimos), `/becas.json`, `/beca/{seudonimo}`, `/canje/{codigo}`.
- Publicado temporalmente con un *quick tunnel* de Cloudflare (la URL cambia si se reinicia). URL fija pendiente: agregar en el panel de Cloudflare el hostname `codi.aideatext.ai` → `http://localhost:8000` al túnel `appmm-ec2`.

### Etiqueta en v61-dev (14:38 UTC)
- v61 `57dac24` (https://github.com/aideatext/AIdeaText-v61): `/api/yo` devuelve `becas: {url, seudonimo}` si existe `AIDEATEXT_BECAS_URL`; `comun.js` pinta en la cabecera del estudiante "🎁 Tu sesión ha sido financiada · Has recibido $X MXN · N de M disponibles" (enlace a `/beca/{seudonimo}`). Solo aparece si recibió al menos 1 sesión.
- Este repo: `GET /beca/{seudonimo}.json` + CORS para v61-dev y edu.
- Desplegado: `build-ui.sh` → `v61/ui:57dac24`; `/srv/v61-dev/.env` con `AIDEATEXT_BECAS_URL` (hoy el quick tunnel; cambiar a `https://codi.aideatext.ai` cuando exista y `docker compose up -d api`).
- 14:45 UTC: **URL fija** `https://codi.aideatext.ai` (túnel `appmm-ec2` → `http://localhost:8000`). `/srv/v61-dev/.env` → `AIDEATEXT_BECAS_URL=https://codi.aideatext.ai`; verificado en `/api/yo` de Ana Ferrer (RES-0001). El quick tunnel queda retirado.
