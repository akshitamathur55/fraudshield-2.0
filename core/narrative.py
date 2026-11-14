"""narrative.py - turns the engine's numbers into plain English a non-expert can follow."""
from core.config import HOME_COUNTRY

CLASS_EXPLAIN = {
    "Legitimate": "a normal payment",
    "Card Testing": "criminals fire many tiny payments to check whether a stolen card still works",
    "Account Takeover": "someone other than the real customer has got into the account and is moving money",
    "APP Scam": "the real customer was tricked by a scammer into sending the money themselves",
    "Credit Card Fraud": "stolen card details are being used for an online purchase"}
ROUTE_EXPLAIN = {"ALLOW": "Payment goes through with no extra steps.",
                 "CHALLENGE": "We ask the customer to prove it is really them (OTP / 3-D Secure) before continuing.",
                 "HARD BLOCK": "The payment is stopped immediately."}

def phrase(feature, p, graph):
    """One human sentence fragment for a model driver."""
    return {
        "amount_log": f"the amount (Rs {p['amount']:,.0f}) is out of the ordinary",
        "amount_ratio": f"it is {p['amount'] / max(p['user_avg_amount'], 1):.1f}x what this customer normally spends",
        "velocity_1m": f"{p['velocity_1m']} payments hit this card within a minute",
        "account_age_days": f"the account is only {p['account_age_days']} days old",
        "payee_changed_hours": f"the payee was changed only {p['payee_changed_hours']:.1f} hours ago",
        "is_new_device": "it came from a device we have not seen for this customer",
        "ip_mismatch": f"the IP address is in {p['ip_country']}, not the customer's home country ({HOME_COUNTRY})",
        "hour": "it happened at an unusual time of day",
        "is_night": "it happened in the middle of the night",
        "device_user_count": f"this device is shared by {graph['device_user_count']} different customers",
        "device_card_count": f"this device has been used with {graph['device_card_count']} different cards",
        "is_micro": "the amount is tiny (Rs 50 or less), typical when criminals test stolen cards",
        "recent_payee_change": "the payee was added within the last 48 hours"}.get(feature, feature)

def reasons(res, p):
    """Reasons in plain English: fired rules first, then top model drivers."""
    out = [r["reason"][0].lower() + r["reason"][1:] for r in res["rules_triggered"]]
    out += [phrase(d["feature"], p, res["graph"]) for d in res["drivers"]]
    seen, uniq = set(), []
    for r in out:
        if r not in seen: seen.add(r); uniq.append(r)
    return uniq

def summary(res, p):
    """Markdown paragraph explaining the decision."""
    head = f"**{ROUTE_EXPLAIN[res['route']]}** We gave this payment a risk score of **{res['risk_score']:.0f} out of 100**. "
    if res["predicted_class"] == "Legitimate" and res["route"] == "ALLOW":
        return head + "Nothing about it looks unusual."
    why = reasons(res, p)
    body = f"It most resembles **{res['predicted_class']}**: {CLASS_EXPLAIN[res['predicted_class']]}. "
    if why: body += "Main reasons: " + "; ".join(why[:4]) + "."
    return head + body

def pipeline_steps(res, p, lo, hi):
    """[(icon, title, detail, flagged)] describing what each stage did - the 'how did we get here' story."""
    top = max(res["probabilities"], key=res["probabilities"].get)
    g = res["graph"]; rules = res["rules_triggered"]
    return [
        ("✅", "1. Checked the data", "All fields passed validation (IDs, amount, country code, etc.).", False),
        ("🚩" if rules else "✔️", "2. Safety rules", "; ".join(r["reason"] for r in rules) if rules else "No hard rule fired.", bool(rules)),
        ("🕸️", "3. Connection check", f"This device has been linked to {g['device_user_count']} customer(s) and {g['device_card_count']} card(s)."
         + (" Sharing like this is a warning sign." if g["device_user_count"] >= 3 or g["device_card_count"] >= 3 else ""),
         g["device_user_count"] >= 3 or g["device_card_count"] >= 3),
        ("🤖", "4. AI model", f"Most likely outcome: {top} ({res['probabilities'][top]:.0%}). Risk score = 100% minus the chance it is legitimate.",
         top != "Legitimate"),
        ("⚖️", "5. Decision", f"Score {res['risk_score']:.0f}: below {lo} = Allow, {lo}-{hi} = Challenge, above {hi} = Block, so **{res['route']}**.",
         res["route"] != "ALLOW"),
    ]
