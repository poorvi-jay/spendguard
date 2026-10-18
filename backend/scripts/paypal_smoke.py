"""
Manual smoke test of the PayPal sandbox authorize -> capture/void flow.

Run from backend/:
    python scripts/paypal_smoke.py capture
    python scripts/paypal_smoke.py void
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app import paypal_client


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "capture"
    if mode not in ("capture", "void"):
        sys.exit("usage: python scripts/paypal_smoke.py [capture|void]")

    try:
        order = paypal_client.create_order(18.50)
        print(f"order_id: {order['order_id']} (status {order['status']})")
        print(f"\nApprove at:\n  {order['approval_url']}\n")
        input("Log in as the sandbox Personal buyer, approve, then press Enter here...")

        auth_id = paypal_client.authorize_order(order["order_id"])
        print(f"authorization_id: {auth_id}")

        if mode == "capture":
            result = paypal_client.capture_authorization(auth_id)
            print(f"captured (status {result.get('status')})")
        else:
            paypal_client.void_authorization(auth_id)
            print("voided")
    except httpx.HTTPStatusError as e:
        print(f"\nPayPal returned {e.response.status_code} for {e.request.url}")
        print(e.response.text)
        sys.exit(1)


if __name__ == "__main__":
    main()
