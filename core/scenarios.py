"""scenarios.py - ready-made test payloads for the simulation console (and tests)."""
SCENARIOS = {
 "Normal everyday purchase": dict(transaction_id="TXN-90000001", user_id="USR-000010", card_id="CRD-000000000010",
    amount=950.0, device_id="a1b2c3d4e5f60718", ip_country="IN", velocity_1m=1, account_age_days=900,
    payee_changed_hours=3000.0, is_new_device=False, user_avg_amount=1000.0, hour=15),
 "Launch Card Testing Automated Script Attack": dict(transaction_id="TXN-90000002", user_id="USR-000020", card_id="CRD-000000000020",
    amount=12.0, device_id="deadbeefdeadbeef", ip_country="US", velocity_1m=5, account_age_days=400,
    payee_changed_hours=3000.0, is_new_device=True, user_avg_amount=1500.0, hour=3),
 "Account Takeover (new device + payee change)": dict(transaction_id="TXN-90000003", user_id="USR-000030", card_id="CRD-000000000030",
    amount=9000.0, device_id="feedfacefeedface", ip_country="NG", velocity_1m=1, account_age_days=1500,
    payee_changed_hours=0.05, is_new_device=True, user_avg_amount=1800.0, hour=2),
 "APP Scam (trusted device, big transfer to new payee)": dict(transaction_id="TXN-90000004", user_id="USR-000040", card_id="CRD-000000000040",
    amount=28000.0, device_id="0123456789abcdef", ip_country="IN", velocity_1m=1, account_age_days=1200,
    payee_changed_hours=6.0, is_new_device=False, user_avg_amount=1600.0, hour=14),
 "Card-Not-Present Credit Card Fraud": dict(transaction_id="TXN-90000005", user_id="USR-000050", card_id="CRD-000000000050",
    amount=32000.0, device_id="cafebabecafebabe", ip_country="RU", velocity_1m=1, account_age_days=700,
    payee_changed_hours=4000.0, is_new_device=True, user_avg_amount=1400.0, hour=3),
}
