# Operación para el hackathon — "Sesión pendiente" sobre conText (Nivel 0)

## 1. ¿Qué CLABE usar?

| Momento | Cuenta | Por qué |
|---|---|---|
| **Hoy y mañana (hackathon)** | Una de las **CLABEs pre-autorizadas** por los organizadores, de preferencia la **cuenta de prueba que publica pey en su documentación** | Ya están activas en CoDi: cero espera |
| **En paralelo, desde hoy** | Registrar **la CLABE propia** en portal.mipey.mx → Finanzas (cuenta `codi`) | Banxico tarda ≈5 días hábiles en activarla |
| **Después** | La CLABE de **ETAITE SAS** (`entity: BUSINESS`) cuando tenga cuenta bancaria | Que los ingresos queden en la empresa |

⚠️ El dinero que entra a una cuenta pre-autorizada **es de su titular y no regresa**: probar solo con $0.01–$1.00.
Cambiar de cuenta **no requiere tocar código**: se cambia la cuenta ligada a la API key (o `PEY_BANK_ACCOUNT_ID`).

## 2. Cómo se conecta con conText (sin tocar su código)

conText ya registra la etiqueta `?ref=` de cada enlace de invitación y la cuenta en `/api/uso` (protegido con `USO_TOKEN`).
Eso basta para el Nivel 0:

```
Donante ──CoDi──► fondo (QR /cafe)          "$X = N sesiones financiadas"
                                                     │
Estudiante ◄── enlace de canje: context.aideatext.ai/?ref=sesion-pendiente
                                                     │
conText /api/uso → porRef["sesion-pendiente"].conversaron = "M sesiones usadas"
```

- **Financiadas** = total donado ÷ `PRECIO_SESION` (10 MXN por defecto).
- **Usadas** = sesiones de conText abiertas con el enlace de canje que llegaron a conversar.
- Nadie liga una donación con un estudiante: anonimato por fondo común.

## 3. Pasos

1. **pey**: API key ligada a la CLABE elegida → `.env` → `PEY_API_KEY`.
2. **conText en Render**: confirmar que existe la variable `USO_TOKEN`; copiar su valor a `CONTEXT_USO_TOKEN` en `.env`.
3. **Probar local**:
   ```bash
   pip install -r requirements.txt
   python scripts/test_webhook_local.py
   python scripts/crear_qr_cafe.py
   uvicorn app:app --port 8000      # abrir http://localhost:8000/cafe
   ```
4. **Donar $1** desde una app bancaria → el muro sube a "sesiones financiadas".
5. **Canjear**: abrir `https://context.aideatext.ai/?ref=sesion-pendiente`, conversar un turno → el muro sube a "usadas".
6. **Publicar** (opcional, para una URL pública y webhook): desplegar este servicio en Render como *Web Service* Python
   (`uvicorn app:app --host 0.0.0.0 --port $PORT`), con las variables de `.env` como secretos de Render.

## 4. Límites conocidos

- conText en Render Free guarda los eventos **en memoria**: si el servicio se reinicia, el contador de "usadas" vuelve a cero.
  Para la demo basta; para operar hay que activar persistencia (Azure Tables o la base de AIdeaText).
- El enlace de canje es público: cualquiera con el enlace consume del fondo. En el Nivel 1 se reemplaza por códigos de un solo uso.
- concursa queda fuera por ahora (no aplica a México).
