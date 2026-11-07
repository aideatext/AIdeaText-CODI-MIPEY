# ☕ "Invítame un café" con CoDi — flujo para el hackathon

## Idea
No cobramos un servicio: demostramos que **cualquiera puede apoyar a AIdeaText con una donación, sin comisión,
desde la app de su banco**. Un QR CoDi permanente de **monto libre** se pega en cualquier página de AIdeaText.

## Flujo
```
Donante ──escanea QR (app bancaria/CoDi)──► Banxico ──► CLABE pre-autorizada (cuenta ligada a la API key)
                                                  │
                         pey: GET /transaction/codi/qr/{id}  (o webhook codi.qr.payment_received)
                                                  ▼
                          /cafe  → muro de agradecimientos en vivo (total, número de cafés)
```

## Pasos (≈30 min)
1. **Portal pey** (portal.mipey.mx): la CLABE pre-autorizada ya está cargada en Finanzas como cuenta `codi`.
   En **Desarrollador → Crear API Key**, liga esa cuenta → copia la key.
   (Opcional: engrane → webhook con una URL pública → copia el secreto.)
2. `.env`: `PEY_API_KEY=...` (y `PEY_WEBHOOK_SECRET` si configuraste webhook).
3. Crear el QR permanente:
   ```bash
   pip install -r requirements.txt
   python scripts/crear_qr_cafe.py        # genera cafe_qr.png y donacion_qr.json
   ```
4. **Publicarlo en cualquier URL nuestra**: subir `cafe_qr.png` y pegar `embed/invitame-un-cafe.html`
   (aideatext.ai, tutor, v5…). Esto no requiere backend.
5. **Demo en vivo**: `uvicorn app:app --port 8000` → abrir `http://localhost:8000/cafe`
   (QR de monto libre + botones $35 / $70 / $150 + muro que se actualiza cada 4 s).
6. Probar: alguien escanea con su app bancaria y dona $1 → aparece en el muro.
   Verificación por consola: `python scripts/crear_qr_cafe.py --ver`.

## Notas
- La confirmación por consulta a pey **no necesita webhook ni túnel**; el webhook es un extra (para el muro con nombre).
- El dinero llega a la CLABE ligada a la API key (en el hackathon, una cuenta pre-autorizada por los organizadores).
- Quien dona necesita una app bancaria mexicana con CoDi activo.
- Siguiente paso real: cambiar a la CLABE de AIdeaText/ETAITE y reutilizar el mismo QR en la plataforma.

## Pitch (30 s)
"Los proyectos educativos abiertos viven de pequeñas contribuciones, pero las pasarelas se comen las donaciones chicas.
Con CoDi, un estudiante o un profesor puede invitarle un café a AIdeaText desde su banco, sin comisión,
y el muro de agradecimientos lo muestra al instante. El mismo QR sirve después para pagar sesiones del tutor."
