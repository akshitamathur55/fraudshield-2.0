"""model_wrapper.py - Day 3. The whole pipeline in ONE function: score_transaction().
rules -> graph -> features -> ML -> explanation -> routing."""
import pickle, time, numpy as np
from core.config import *
from core.features import FEATURES, NICE, build_features
from core.rules_engine import run_rules
from core.validation import validate_payload, ValidationError

class FraudShieldEngine:
    def __init__(self, path=MODEL_PATH):
        a = pickle.load(open(path, "rb"))
        self.model, self.baseline, self.graph, self.name = a["model"], a["baseline"], a["graph"], a["name"]

    def _explain(self, x, base_prob_legit=None):
        """Local contribution = how much does risk DROP if we replace one feature with a 'typical legit' value?"""
        X = np.tile(x, (len(x) + 1, 1))
        for j in range(len(x)): X[j + 1, j] = self.baseline[j]
        legit = np.clip(self.model.predict_proba(X)[:, 0], 1e-6, 1 - 1e-6)
        logit = lambda q: np.log((1 - q) / q)                         # risk in log-odds (doesn't saturate)
        contrib = logit(legit[0]) - logit(legit[1:])                 # positive = pushed risk up
        pos = np.clip(contrib, 0, None)
        share = pos / pos.sum() * 100 if pos.sum() > 0 else pos      # % share of total risk push
        order = np.argsort(-pos)[:3]
        return [{"feature": FEATURES[j], "label": NICE[FEATURES[j]], "value": float(x[j]),
                 "impact": round(float(share[j]), 1)} for j in order if pos[j] > 0]

    def score(self, payload: dict, allow_below=ALLOW_BELOW, block_above=BLOCK_ABOVE) -> dict:
        t0 = time.perf_counter()
        try: p = validate_payload(payload)
        except ValidationError as e: return {"valid": False, "errors": e.errors}
        rules = run_rules(p)                                         # 1. deterministic rules
        du, dc = self.graph.stats(p["user_id"], p["card_id"], p["device_id"])   # 2. graph links
        x = np.array(build_features(p, du, dc), dtype=float)         # 3. features
        probs = self.model.predict_proba(x.reshape(1, -1))[0]        # 4. ML probabilities
        score = (1 - probs[0]) * 100
        pred = CLASSES[int(np.argmax(probs))]
        for r in rules:                                              # rules override the model
            pred = r["class"]; score = max(score, RULE_OVERRIDE_SCORE[r["class"]])
        drivers, explain_ok = [], True
        try: drivers = self._explain(x, probs[0])                    # 5. explanation (NFR-2: must not break routing)
        except Exception: explain_ok = False
        if score < allow_below: route = "ALLOW"                      # 6. route
        elif score > block_above: route = "HARD BLOCK"
        else: route = "CHALLENGE"
        return {"valid": True, "risk_score": round(float(score), 1), "predicted_class": pred, "route": route,
                "probabilities": {CLASSES[i]: round(float(pr), 4) for i, pr in enumerate(probs)},
                "rules_triggered": rules, "drivers": drivers, "explain_ok": explain_ok,
                "mitigation": MITIGATION[pred] if route != "ALLOW" else MITIGATION["Legitimate"],
                "graph": {"device_user_count": du, "device_card_count": dc},
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}
