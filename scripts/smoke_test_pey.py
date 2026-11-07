"""Prueba REAL contra api.pey.mx con $0.01 MXN (pey no tiene sandbox).

    python scripts/smoke_test_pey.py qr          # genera QR de 1 centavo, guarda qr.png
    python scripts/smoke_test_pey.py pn 55XXXXXXXX
    python scripts/smoke_test_pey.py link        # imprime URL de checkout
    python scripts/smoke_test_pey.py tx          # lista transacciones de la API key
"""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
from pey_payments import PeyClient  # noqa: E402

p = PeyClient()
cmd = sys.argv[1] if len(sys.argv) > 1 else "qr"
bank = os.getenv("PEY_BANK_ACCOUNT_ID") or None

if cmd == "qr":
    r = p.create_codi_qr(0.01, concept="AIdeaText prueba", num_ref="1", generate_image=True, bank_account_id=bank,
                         metadata={"orderId": "smoke-qr"})
    if r.get("qrImage"):
        open("qr.png", "wb").write(base64.b64decode(r["qrImage"]))
        r["qrImage"] = "<guardado en qr.png>"
elif cmd == "pn":
    r = p.create_codi_push(0.01, phone_number=sys.argv[2], concept="AIdeaText prueba", bank_account_id=bank,
                           metadata={"orderId": "smoke-pn"})
elif cmd == "link":
    base = os.getenv("PUBLIC_BASE_URL", "https://tutor.aideatext.ai")
    r = p.create_payment_link(0.01, success_url=f"{base}/pago/exito", back_url=f"{base}/pago/cancelado",
                              client_reference_id="smoke-link")
elif cmd == "tx":
    r = p.list_transactions()
else:
    sys.exit(__doc__)
print(json.dumps(r, indent=2, ensure_ascii=False))
