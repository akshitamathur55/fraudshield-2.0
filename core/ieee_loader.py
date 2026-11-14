"""ieee_loader.py - turns the public IEEE-CIS Fraud Detection data (Kaggle) into FraudShield's own schema,
so real e-commerce card-fraud data can be used for training next to the simulated data.

Put the Kaggle files here (any ONE of these folders works):
    data/ieee/train_transaction.csv   (+ optional data/ieee/train_identity.csv)
    data/train_transaction.csv        ieee/train_transaction.csv        train_transaction.csv

What the real data gives us, and what it does not (be upfront about this in a viva):
  * IEEE-CIS has ONE fraud flag (isFraud) - no fraud sub-types. Every fraud row is therefore labelled
    "Credit Card Fraud" (it is online card-not-present fraud). The other 3 classes stay simulated.
  * IEEE-CIS has no payee / beneficiary field. payee_changed_hours is filled with typical-legit random values,
    so the model cannot learn anything (good or bad) from that column for IEEE rows.
  * Amounts are USD; they are converted to rupees with USD_TO_INR so they sit on the same scale as our data.
  * "Customer" = same card + billing address; "device" = a customer-specific device fingerprint, so IEEE rows
    never create fake 'one device, 500 customers' links in the connections map.
"""
import os, hashlib
import numpy as np, pandas as pd
from core.config import CLASS_IDS, HOME_COUNTRY

USD_TO_INR = 83.0
SEARCH_DIRS = ["data/ieee", "data", "ieee", "."]
TX_NAME, ID_NAME = "train_transaction.csv", "train_identity.csv"
TX_COLS = ["TransactionID", "isFraud", "TransactionDT", "TransactionAmt", "card1", "card2", "card4", "card6", "addr1", "addr2", "D1"]
ID_COLS = ["TransactionID", "DeviceType", "DeviceInfo", "id_30", "id_31"]


def find_ieee_files():
    """-> (transaction_csv, identity_csv_or_None), or (None, None) when the Kaggle files are not present."""
    for d in SEARCH_DIRS:
        t = os.path.join(d, TX_NAME)
        if os.path.exists(t):
            i = os.path.join(d, ID_NAME)
            return t, (i if os.path.exists(i) else None)
    return None, None


def _md5hex(s):  # stable 16-char hex id (Python's built-in hash() changes every run)
    return hashlib.md5(s.encode()).hexdigest()[:16]


def load_ieee(tx_path, id_path=None, n_legit=30000, n_fraud=6000, seed=42, usd_to_inr=USD_TO_INR):
    """Read the Kaggle files, build every FraudShield column on the FULL history, then sample.
    Returns a DataFrame with the same columns as fraud_transactions.csv plus  source='ieee'."""
    have = pd.read_csv(tx_path, nrows=0).columns
    miss = [c for c in TX_COLS[:4] if c not in have]
    if miss: raise ValueError(f"{tx_path} is missing required IEEE-CIS columns: {miss}")
    tx = pd.read_csv(tx_path, usecols=[c for c in TX_COLS if c in have])
    for c in ("card1", "card2", "card4", "card6", "addr1", "addr2", "D1"):
        if c not in tx: tx[c] = np.nan
    tx = tx.sort_values("TransactionDT", kind="stable").reset_index(drop=True)

    # ---- who is the customer / card -------------------------------------------------------------
    card_key = tx["card1"].fillna(-1).astype(int).astype(str) + "|" + tx["card2"].fillna(-1).astype(int).astype(str) + "|" \
        + tx["card4"].fillna("NA") + "|" + tx["card6"].fillna("NA")
    user_key = card_key + "|" + tx["addr1"].fillna(-1).astype(int).astype(str)
    tx["card_id"] = ["CRD-%012d" % (100_000_000_000 + i) for i in pd.factorize(card_key)[0]]   # offset: never clashes with simulated ids
    tx["user_id"] = ["USR-%06d" % (100_000 + i) for i in pd.factorize(user_key)[0]]
    uid = tx["user_id"]

    # ---- device: fingerprint from the identity table (only ~25% of rows have one) ----------------
    fp = pd.Series(np.nan, index=tx.index, dtype=object)
    if id_path and os.path.exists(id_path):
        ihave = pd.read_csv(id_path, nrows=0).columns
        idf = pd.read_csv(id_path, usecols=[c for c in ID_COLS if c in ihave]).drop_duplicates("TransactionID")
        tx = tx.merge(idf, on="TransactionID", how="left")
        parts = [tx[c].astype("object") for c in ("DeviceInfo", "id_30", "id_31") if c in tx]
        if parts:
            joined = parts[0].fillna("").astype(str)
            for s in parts[1:]: joined = joined + "|" + s.fillna("").astype(str)
            fp = joined.where(joined.str.strip("|") != "")            # all-empty -> NaN (no identity info)
    trusted = fp.groupby(uid).transform("first")                      # the customer's first-seen device fingerprint
    is_new = (fp.notna() & trusted.notna() & (fp != trusted)).astype(int)
    dev_fp = fp.fillna(trusted).fillna("primary")                     # no identity row -> treated as the usual device
    tx["device_id"] = [_md5hex(f"{u}|{f}") for u, f in zip(uid, dev_fp)]
    tx["is_new_device"] = is_new.values

    # ---- amounts, history-based features (computed only from EARLIER rows, so nothing leaks) ------
    amt = (tx["TransactionAmt"].astype(float) * usd_to_inr).round(2).clip(lower=1.0)
    tx["amount"] = amt
    g = amt.groupby(uid)
    prev_n = g.cumcount()
    prev_mean = (g.cumsum() - amt) / prev_n.replace(0, np.nan)
    tx["user_avg_amount"] = prev_mean.fillna(amt).round(2)           # first purchase: 'usual' = itself

    t = tx["TransactionDT"].astype(float)
    first_seen_days = (t - t.groupby(uid).transform("min")) / 86400.0
    d1 = tx["D1"].astype(float)
    tx["account_age_days"] = d1.fillna(first_seen_days).clip(lower=0).astype(int)

    vel = np.ones(len(tx), dtype=int)                                  # same rolling 60-second window as data_gen.py
    for _, idx in tx.groupby("card_id").indices.items():
        ts = t.to_numpy()[idx]
        vel[idx] = np.arange(len(ts)) - np.searchsorted(ts, ts - 60, side="left") + 1
    tx["velocity_1m"] = np.maximum(vel, 1)

    home_country_code = tx["addr2"].mode().iloc[0] if tx["addr2"].notna().any() else 87
    tx["ip_country"] = np.where(tx["addr2"].isna() | (tx["addr2"] == home_country_code), HOME_COUNTRY, "XX")
    tx["hour"] = ((t // 3600) % 24).astype(int)
    rng = np.random.default_rng(seed)
    tx["payee_changed_hours"] = (rng.exponential(2500, len(tx)) + 72).round(3)   # no payee info in IEEE-CIS (see header)
    tx["timestamp"] = t
    tx["label"] = np.where(tx["isFraud"] == 1, CLASS_IDS["Credit Card Fraud"], CLASS_IDS["Legitimate"])
    tx["transaction_id"] = ["IEEE-%08d" % i for i in tx["TransactionID"]]
    tx["source"] = "ieee"

    cols = ["transaction_id", "user_id", "card_id", "device_id", "amount", "user_avg_amount", "account_age_days", "is_new_device",
            "ip_country", "hour", "velocity_1m", "payee_changed_hours", "timestamp", "label", "source"]
    out = tx[cols]
    fr, lg = out[out.label == 1], out[out.label == 0]                  # sample AFTER the history features were built
    out = pd.concat([fr.sample(min(n_fraud, len(fr)), random_state=seed), lg.sample(min(n_legit, len(lg)), random_state=seed)])
    return out.sort_values("timestamp").reset_index(drop=True)
