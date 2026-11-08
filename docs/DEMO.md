# Demo pública 24x7: sesión pendiente con CoDi

Cualquier persona (jurado, aliados, estudiantes) puede seguir el flujo completo con dinero real, desde la app de su banco.

## URLs

| Paso | Qué ver | URL |
|---|---|---|
| 1. Donar | QR CoDi de monto libre y muro en vivo | https://codi.aideatext.ai/cafe |
| 2. Reparto | Rondas iguales para todos los estudiantes, uso por estudiante (solo seudónimos) | https://codi.aideatext.ai/becas |
| 2b. Datos | Lo mismo en JSON | https://codi.aideatext.ai/becas.json |
| 3. Estudiante | Etiqueta "🎁 Tu sesión ha sido financiada · Has recibido $X MXN" en la cabecera | https://v61-dev.aideatext.ai (cuenta demo `ana.ferrer@alumna.litoral.edu.pe` / `aideatext`) |
| 3b. Sus sesiones | Botones "Usar esta sesión" (un solo uso) | https://codi.aideatext.ai/beca/RES-0001 |
| 4. Uso | El tutor socrático donde se gasta la sesión | https://context.aideatext.ai/?ref=sesion-pendiente |

## Recorrido (5 minutos)
1. En `/cafe`, escanear el QR con la app del banco (CoDi) y pagar. Con el precio de demo, **$0.01 = 1 sesión**.
2. Cuando lo donado alcanza una ronda completa (1 sesión por cada estudiante activo, hoy 6 = $0.06), `/becas` muestra la ronda y cada estudiante recibe 1.
3. Entrar a v61-dev como Ana: aparece la etiqueta verde. Al pulsarla, "Usar esta sesión" abre conText.
4. Volver a `/becas`: la columna "Usadas" sube. Un código ya usado responde 410 si se intenta otra vez.

## Repositorios
- Pagos, reparto, `/cafe`, `/becas`: https://github.com/aideatext/AIdeaText-CODI-MIPEY
- Plataforma de estudiantes (etiqueta en la cabecera): https://github.com/aideatext/AIdeaText-v61
- conText (sin cambios para el reparto): https://github.com/aideatext/conText-HackTheAndes

## Operación (EC2)
- `aideatext-codi.service` (systemd): uvicorn en `127.0.0.1:8000`, `Restart=always`, arranca con la máquina. Plantilla en `deploy/`.
- `aideatext-codi-sync.timer`: copia el padrón de estudiantes activos de v61-dev cada 15 min.
- Entrada pública: túnel Cloudflare `appmm-ec2` (`cloudflared-appmm.service`), hostname `codi.aideatext.ai` → `http://localhost:8000`.
- v61-dev: contenedores con `restart: unless-stopped`; `AIDEATEXT_BECAS_URL=https://codi.aideatext.ai` en `/srv/v61-dev/.env`.
- Ver estado: `systemctl status aideatext-codi` · registros: `journalctl -u aideatext-codi -f`.
- Precio de demo: `PRECIO_SESION=0.01` en `.env`; para operación real `10` y `sudo systemctl restart aideatext-codi`.
