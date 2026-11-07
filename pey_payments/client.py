"""Cliente mínimo de la API de pey (https://docs.pey.mx).

Cubre los endpoints que AIdeaText necesita para cobrar:
  - CoDi QR            POST /codi/qr
  - CoDi push (PN)     POST /codi/pn
  - Payment link       POST /payment-link/create | /payment-link/update | GET /payment-link/{id}
  - Transacciones      GET /transaction/{id} | GET /transaction/api-key
  - Cuentas bancarias  POST /bank-account | GET /bank-account/{id}

No hay sandbox: pey recomienda probar en producción con montos de $0.01 MXN.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

PEY_BASE_URL = os.getenv("PEY_BASE_URL", "https://api.pey.mx")


class PeyError(RuntimeError):
    def __init__(self, status: int, body: Any):
        super().__init__(f"pey API error {status}: {body}")
        self.status = status
        self.body = body


class PeyClient:
    def __init__(self, api_key: str | None = None, base_url: str = PEY_BASE_URL, timeout: float = 20.0):
        api_key = api_key or os.getenv("PEY_API_KEY")
        if not api_key:
            raise ValueError("Falta PEY_API_KEY (créala en portal.mipey.mx > Desarrollador)")
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    # ------------------------------------------------------------------ util
    def _req(self, method: str, path: str, **kw) -> dict:
        r = self._http.request(method, path, **kw)
        try:
            body = r.json()
        except ValueError:
            body = r.text
        if r.status_code >= 400:
            raise PeyError(r.status_code, body)
        return body

    @staticmethod
    def _clean(d: dict) -> dict:
        return {k: v for k, v in d.items() if v is not None}

    # ------------------------------------------------------------------ CoDi
    def create_codi_qr(
        self,
        amount: float,
        concept: str | None = None,
        num_ref: str | None = None,          # 1-7 dígitos
        expiration: int | None = None,       # segundos; 0 = sin expiración, mínimo 360 si se usa
        generate_image: bool = True,
        bank_account_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Devuelve {id (IDC Banxico), qrString, qrImage (base64 PNG | None)}."""
        return self._req("POST", "/codi/qr", json=self._clean({
            "amount": amount, "concept": concept, "numRef": num_ref,
            "expiration": expiration, "generateImage": generate_image,
            "bankAccountId": bank_account_id, "metadata": metadata,
        }))

    def create_codi_push(
        self,
        amount: float,
        phone_number: str,                   # 10 dígitos, celular ligado a la app bancaria del pagador
        concept: str | None = None,
        num_ref: str | None = None,
        expiration: int | None = None,       # mínimo 360
        bank_account_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Devuelve {transactionId, codiId}."""
        return self._req("POST", "/codi/pn", json=self._clean({
            "amount": amount, "phoneNumber": phone_number, "concept": concept,
            "numRef": num_ref, "expiration": expiration,
            "bankAccountId": bank_account_id, "metadata": metadata,
        }))

    # ---------------------------------------------------------- Payment link
    def create_payment_link(
        self,
        amount: float,
        success_url: str,                    # HTTPS obligatorio
        back_url: str,                       # HTTPS obligatorio
        client_reference_id: str | None = None,
        has_tip: bool = False,
        metadata: dict | None = None,
    ) -> dict:
        """Checkout hospedado (CoDi + tarjeta + Apple/Google Pay). Devuelve {id, url}."""
        return self._req("POST", "/payment-link/create", json=self._clean({
            "amount": amount, "successUrl": success_url, "backUrl": back_url,
            "clientReferenceId": client_reference_id, "hasTip": has_tip, "metadata": metadata,
        }))

    def update_payment_link(self, payment_link_id: str, amount: float) -> dict:
        return self._req("POST", "/payment-link/update", json={"paymentLinkId": payment_link_id, "amount": amount})

    def get_payment_link(self, payment_link_id: str) -> dict:
        return self._req("GET", f"/payment-link/{payment_link_id}")

    # ---------------------------------------------------------- Transacciones
    def get_transaction(self, transaction_id: str) -> dict:
        return self._req("GET", f"/transaction/{transaction_id}")

    def list_transactions(self, next_token: str | None = None) -> dict:
        params = {"nextToken": next_token} if next_token else None
        return self._req("GET", "/transaction/api-key", params=params)

    def list_qr_transactions(self, codi_qr_id: str, next_token: str | None = None) -> dict:
        params = {"nextToken": next_token} if next_token else None
        return self._req("GET", f"/transaction/codi/qr/{codi_qr_id}", params=params)

    # ------------------------------------------------------- Cuentas banco
    def register_bank_account(self, alias: str, name: str, clabe: str, entity: str = "BUSINESS") -> dict:
        """entity: BUSINESS | PERSON. Banxico tarda ~5 días hábiles en activarla."""
        return self._req("POST", "/bank-account", json={"alias": alias, "name": name, "clabe": clabe, "entity": entity})

    def get_bank_account(self, bank_account_id: str) -> dict:
        return self._req("GET", f"/bank-account/{bank_account_id}")
