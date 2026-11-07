"""Crea el QR CoDi permanente de monto libre para 'Invítame un café'.

    python scripts/crear_qr_cafe.py          # crea (o reutiliza) donacion_qr.json + cafe_qr.png
    python scripts/crear_qr_cafe.py --nuevo  # fuerza uno nuevo
    python scripts/crear_qr_cafe.py --ver    # lista los pagos recibidos en ese QR

El PNG se puede pegar en cualquier página de AIdeaText (no requiere servidor).
"""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
from pey_payments.donaciones import create_static_qr, load_static_qr  # noqa: E402
from pey_payments.router import pey  # noqa: E402

if "--ver" in sys.argv:
    qr = load_static_qr() or sys.exit("Primero crea el QR")
    print(json.dumps(pey().list_qr_transactions(qr["id"]), indent=2, ensure_ascii=False))
    sys.exit()

qr = create_static_qr(force="--nuevo" in sys.argv)
if qr.get("qrImage"):
    open("cafe_qr.png", "wb").write(base64.b64decode(qr["qrImage"]))
print("QR CoDi id :", qr["id"])
print("qrString   :", qr["qrString"][:80], "...")
print("Imagen     : cafe_qr.png" if qr.get("qrImage") else "Sin imagen")
