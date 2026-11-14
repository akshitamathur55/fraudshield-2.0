"""validation.py - strict schema check for every incoming payload (SRS 'Data Requirements')."""
import re

class ValidationError(Exception):
    def __init__(self, errors): self.errors = errors; super().__init__("; ".join(errors))

_RX = {"transaction_id": r"TXN-[0-9]{8}", "user_id": r"USR-[0-9]{6}", "card_id": r"CRD-[0-9]{12}",
       "device_id": r"[0-9a-fA-F]+", "ip_country": r"[A-Z]{2}"}

def _num(v):  # real number but not bool / NaN
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v

def validate_payload(p: dict) -> dict:
    """Returns a cleaned payload or raises ValidationError listing ALL problems."""
    errs, out = [], {}
    for f, rx in _RX.items():
        v = p.get(f)
        if not isinstance(v, str) or not re.fullmatch(rx, v): errs.append(f"{f}: invalid value {v!r}")
        else: out[f] = v
    v = p.get("amount")
    if not _num(v) or v <= 0: errs.append(f"amount: must be a number > 0 (got {v!r})")
    else: out["amount"] = float(v)
    for f in ("velocity_1m", "account_age_days"):
        v = p.get(f)
        if not (isinstance(v, int) and not isinstance(v, bool)) or v < 0: errs.append(f"{f}: must be integer >= 0 (got {v!r})")
        else: out[f] = v
    v = p.get("payee_changed_hours")
    if not _num(v) or v < 0: errs.append(f"payee_changed_hours: must be number >= 0 (got {v!r})")
    else: out["payee_changed_hours"] = float(v)
    # extra helper fields (optional, with safe defaults)
    out["is_new_device"] = bool(p.get("is_new_device", False))
    v = p.get("user_avg_amount", out.get("amount"))
    out["user_avg_amount"] = float(v) if _num(v) and v > 0 else out.get("amount", 1.0)
    h = p.get("hour", 12)
    if not (isinstance(h, int) and 0 <= h <= 23): errs.append(f"hour: must be integer 0-23 (got {h!r})")
    out["hour"] = h
    if errs: raise ValidationError(errs)
    return out
