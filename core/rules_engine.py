"""rules_engine.py - fast, deterministic 'if this then that' rules. They run BEFORE the ML model (FR-1)."""
from core.config import *

def run_rules(p: dict) -> list:
    """Returns a list of triggered rules: [{'rule','class','reason'}]. Empty list = nothing fired."""
    hits = []
    # Rule 1: Card testing = 3+ tiny transactions on one card inside 60 seconds
    if p["amount"] <= CARD_TEST_MAX_AMOUNT and p["velocity_1m"] >= CARD_TEST_MIN_COUNT:
        hits.append({"rule": "R1_CARD_TESTING", "class": "Card Testing",
                     "reason": f"{p['velocity_1m']} txns of <= Rs{CARD_TEST_MAX_AMOUNT:.0f} on one card within {CARD_TEST_WINDOW_SEC}s"})
    # Rule 2: ATO = brand-new device right after the payee/beneficiary was changed (within 10 min)
    if p["is_new_device"] and p["payee_changed_hours"] <= ATO_WINDOW_HOURS:
        hits.append({"rule": "R2_ATO", "class": "Account Takeover",
                     "reason": "New device used within 10 minutes of a beneficiary change"})
    return hits
