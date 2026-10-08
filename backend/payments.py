"""Simulated payment processing (no real gateway). Card numbers are never stored."""
import re, secrets

METHODS = ("Cash on Delivery", "UPI", "Credit/Debit Card")


def _luhn(number):
    digits = [int(c) for c in number][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return total % 10 == 0


def process_payment(method, details, amount):
    """Returns (ok, error, status, reference)."""
    if method not in METHODS:
        return False, "Please select a payment method.", None, None
    if method == "Cash on Delivery":
        return True, None, "Pending (COD)", "COD"
    if method == "UPI":
        upi = (details.get("upi") or "").strip()
        if not re.fullmatch(r"[\w.\-]{2,}@[a-zA-Z]{2,}", upi):
            return False, "Enter a valid UPI ID (e.g. name@okbank).", None, None
        return True, None, "Paid", "UPI" + secrets.token_hex(5).upper()
    number = re.sub(r"\s+", "", details.get("card_number") or "")
    if not (number.isdigit() and 13 <= len(number) <= 19 and _luhn(number)):
        return False, "Enter a valid card number.", None, None
    if not re.fullmatch(r"(0[1-9]|1[0-2])\s*/\s*\d{2}", (details.get("expiry") or "").strip()):
        return False, "Enter card expiry as MM/YY.", None, None
    if not re.fullmatch(r"\d{3,4}", details.get("cvv") or ""):
        return False, "Enter a valid CVV.", None, None
    return True, None, "Paid", "CARD" + number[-4:] + secrets.token_hex(3).upper()
