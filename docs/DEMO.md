# Demo pública 24x7: subvención del uso de AIdeaText con CoDi

Cualquier persona (jurado, aliados, estudiantes) puede seguir el flujo completo con dinero real, desde la app de su banco.

## URLs

| Paso | Qué ver | URL |
|---|---|---|
| 1. Donar | Botón «Donación» en la cabecera de conText: QR CoDi de monto libre | https://context.aideatext.ai |
| 2. Reparto | Lo donado dividido en partes iguales entre los estudiantes activos, y su uso en el ciclo (solo seudónimos) | https://codi.aideatext.ai/becas |
| 2b. Datos | Lo mismo en JSON | https://codi.aideatext.ai/becas.json |
| 3. Estudiante | Etiqueta "🎁 Tu uso de AIdeaText está subvencionado con: $X MXN" en la cabecera (se actualiza sola cada 20 s) | https://v61-dev.aideatext.ai (cuenta demo `ana.ferrer@alumna.litoral.edu.pe` / `aideatext`) |
| 3b. Su subvención | Monto recibido, su actividad y enlace para seguir en AIdeaText | https://codi.aideatext.ai/beca/RES-0001 |

## Recorrido (5 minutos)
1. En https://context.aideatext.ai pulsar «Donación», escanear el QR con la app del banco (CoDi) y pagar cualquier monto.
2. `/becas` divide al instante el total donado en partes iguales entre todos los estudiantes activos de AIdeaText. Nadie canjea nada: el uso queda subvencionado.
3. Entrar a v61-dev como Ana: en la cabecera aparece la etiqueta verde con lo recibido. Ana sigue trabajando normalmente (escritura, tutor, conText integrado).
4. `/becas` muestra el uso de cada estudiante en el ciclo (análisis + turnos con el tutor, actualizado cada 15 min). Al cierre del semestre se ve quién aprovechó más y quién menos.

## Repositorios
- Pagos y reparto (`/becas`, cobro CoDi): https://github.com/aideatext/AIdeaText-CODI-MIPEY
- Plataforma de estudiantes (etiqueta en la cabecera): https://github.com/aideatext/AIdeaText-v61
- conText (botón «Donación»; también integrado en v61): https://github.com/aideatext/conText-HackTheAndes

## Operación (EC2)
- `aideatext-codi.service` (systemd): uvicorn en `127.0.0.1:8000`, `Restart=always`, arranca con la máquina. Plantilla en `deploy/`.
- `aideatext-codi-sync.timer`: copia el padrón de estudiantes activos de v61-dev cada 15 min.
- Entrada pública: túnel Cloudflare `appmm-ec2` (`cloudflared-appmm.service`), hostname `codi.aideatext.ai` → `http://localhost:8000`.
- v61-dev: contenedores con `restart: unless-stopped`; `AIDEATEXT_BECAS_URL=https://codi.aideatext.ai` en `/srv/v61-dev/.env`.
- Ver estado: `systemctl status aideatext-codi` · registros: `journalctl -u aideatext-codi -f`.
- Precio de demo: `PRECIO_SESION=0.01` en `.env`; para operación real `10` y `sudo systemctl restart aideatext-codi`.
