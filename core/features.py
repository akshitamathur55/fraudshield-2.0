"""features.py - turns a raw payload (+ graph stats) into the number-vector the ML model eats.
Used by BOTH training and live scoring, so they can never disagree."""
import numpy as np
from core.config import HOME_COUNTRY

FEATURES = ["amount_log", "amount_ratio", "velocity_1m", "account_age_days", "payee_changed_hours",
            "is_new_device", "ip_mismatch", "hour", "is_night", "device_user_count",
            "device_card_count", "is_micro", "recent_payee_change"]

# friendly names for the dashboard / explanations
NICE = {"amount_log": "Transaction amount", "amount_ratio": "Amount vs user's usual spend",
        "velocity_1m": "Transactions in last minute", "account_age_days": "Account age",
        "payee_changed_hours": "Hours since payee change", "is_new_device": "Unrecognised device",
        "ip_mismatch": "IP country mismatch", "hour": "Time of day", "is_night": "Night-time activity",
        "device_user_count": "Users sharing this device", "device_card_count": "Cards used on this device",
        "is_micro": "Micro-amount (<= Rs 50)", "recent_payee_change": "Payee changed within 48h"}

def build_features(d: dict, device_user_count: int, device_card_count: int) -> list:
    """d = a validated payload dict (or a dataframe row as dict)."""
    return [np.log1p(d["amount"]), d["amount"] / max(d["user_avg_amount"], 1.0), d["velocity_1m"],
            d["account_age_days"], d["payee_changed_hours"], int(d["is_new_device"]),
            int(d["ip_country"] != HOME_COUNTRY), d["hour"], int(d["hour"] <= 5),
            device_user_count, device_card_count, int(d["amount"] <= 50), int(d["payee_changed_hours"] <= 48)]
