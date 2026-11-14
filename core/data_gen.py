"""data_gen.py - Day 1. Makes fake-but-realistic transactions with 4 fraud signatures injected."""
import numpy as np, pandas as pd
from core.config import CLASS_IDS, DATA_PATH

def _hex(rng, n=16): return "".join(rng.choice(list("0123456789abcdef"), n))

def generate(n_legit=10000, seed=42, save=True):
    rng = np.random.default_rng(seed)
    n_users = 3000
    users = pd.DataFrame({
        "user_id": [f"USR-{i:06d}" for i in range(n_users)],
        "card_id": [f"CRD-{i:012d}" for i in range(n_users)],
        "device_id": [_hex(rng) for _ in range(n_users)],
        "user_avg_amount": rng.lognormal(7.0, 0.6, n_users).round(2),   # ~Rs 1,100 typical
        "account_age_days": np.clip(rng.lognormal(6.0, 0.9, n_users), 5, 4000).astype(int)})
    month = 30 * 24 * 3600
    rows = []

    def row(u, ts, amount, dev, new_dev, ip, hour, vel, payee, label):
        rows.append(dict(user_id=u.user_id, card_id=u.card_id, device_id=dev, amount=round(float(amount), 2),
                         user_avg_amount=u.user_avg_amount, account_age_days=int(u.account_age_days),
                         is_new_device=int(new_dev), ip_country=ip, hour=int(hour), velocity_1m=int(vel),
                         payee_changed_hours=round(float(payee), 3), timestamp=float(ts), label=label))

    # ---------- LEGITIMATE (baseline 10,000 rows) ----------
    for _ in range(n_legit):
        u = users.iloc[rng.integers(n_users)]
        big = rng.random() < 0.03                       # occasional legit big purchase
        amt = u.user_avg_amount * (rng.uniform(3, 6) if big else rng.lognormal(0, 0.5))
        if rng.random() < 0.05: amt = rng.uniform(5, 50)   # tea / UPI micro payments
        new_dev = rng.random() < 0.04
        dev = _hex(rng) if new_dev else u.device_id
        ip = "IN" if rng.random() < 0.96 else rng.choice(["US", "GB", "AE", "SG"])
        payee = rng.uniform(0, 72) if rng.random() < 0.06 else rng.exponential(2500) + 72
        row(u, rng.uniform(0, month), max(amt, 1), dev, new_dev, ip, int(rng.normal(14, 4.5)) % 24,
            1 + rng.poisson(0.08), payee, CLASS_IDS["Legitimate"])

    # ---------- CARD TESTING: bot burst of 3-6 tiny txns on one card within ~30 seconds ----------
    bot_devs = [_hex(rng) for _ in range(40)]           # bots re-use devices across many cards
    for _ in range(130):
        u = users.iloc[rng.integers(n_users)]; dev = bot_devs[rng.integers(len(bot_devs))]
        t0, k = rng.uniform(0, month), int(rng.integers(3, 7))
        for j in range(k):
            row(u, t0 + j * rng.uniform(3, 8), rng.uniform(1, 50), dev, rng.random() < 0.8, rng.choice(["IN", "US", "RU"]),
                int(rng.integers(0, 24)), 0, rng.exponential(2500) + 72, CLASS_IDS["Card Testing"])

    # ---------- ACCOUNT TAKEOVER: new device + payee changed + large transfer ----------
    atk_devs = [_hex(rng) for _ in range(60)]
    for _ in range(500):
        u = users.iloc[rng.integers(n_users)]
        payee = rng.uniform(0.01, 0.16) if rng.random() < 0.25 else rng.uniform(0.17, 10)
        row(u, rng.uniform(0, month), u.user_avg_amount * rng.uniform(3, 9),
            atk_devs[rng.integers(len(atk_devs))] if rng.random() < 0.75 else _hex(rng),
            rng.random() < 0.95, "IN" if rng.random() < 0.5 else rng.choice(["US", "NG", "RU"]),
            int(rng.integers(0, 24)), 1 + rng.poisson(0.3), payee, CLASS_IDS["Account Takeover"])

    # ---------- APP SCAM: trusted device, but outsized transfer to a brand-new payee ----------
    for _ in range(500):
        u = users.iloc[rng.integers(n_users)]
        row(u, rng.uniform(0, month), u.user_avg_amount * rng.uniform(4, 15), u.device_id, rng.random() < 0.05, "IN",
            int(rng.integers(9, 21)), 1, rng.uniform(0.2, 48), CLASS_IDS["APP Scam"])

    # ---------- CNP CREDIT-CARD FRAUD: stolen card details, foreign IP, night, high value ----------
    for _ in range(600):
        u = users.iloc[rng.integers(n_users)]
        row(u, rng.uniform(0, month), u.user_avg_amount * rng.uniform(3, 12),
            _hex(rng) if rng.random() < 0.7 else bot_devs[rng.integers(len(bot_devs))], rng.random() < 0.85,
            "IN" if rng.random() < 0.2 else rng.choice(["US", "GB", "RU", "NG", "CN"]),
            int(rng.integers(0, 6)) if rng.random() < 0.6 else int(rng.integers(0, 24)),
            1 + rng.poisson(0.5), rng.exponential(2500) + 72, CLASS_IDS["Credit Card Fraud"])

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    # ROLLING WINDOW METRIC: how many txns on the same card in the last 60 s (incl. this one)
    vel = np.ones(len(df), dtype=int)
    for _, g in df.groupby("card_id"):
        ts = g["timestamp"].to_numpy()
        vel[g.index] = np.arange(len(ts)) - np.searchsorted(ts, ts - 60, side="left") + 1
    df["velocity_1m"] = np.maximum(vel, 1)
    df.insert(0, "transaction_id", [f"TXN-{i:08d}" for i in range(len(df))])
    if save: df.to_csv(DATA_PATH, index=False)
    return df

if __name__ == "__main__":
    d = generate()
    print(f"Saved {len(d)} rows to {DATA_PATH}\n", d["label"].value_counts().sort_index())
