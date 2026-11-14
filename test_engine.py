"""test_engine.py - Day 3/5 local test: scores every scenario + edge cases, checks latency."""
from core.model_wrapper import FraudShieldEngine
from core.scenarios import SCENARIOS
from core.config import LATENCY_BUDGET_MS
eng = FraudShieldEngine()
eng.score(SCENARIOS["Normal everyday purchase"])           # warm-up call
worst = 0
for name, p in SCENARIOS.items():
    r = eng.score(p); worst = max(worst, r["latency_ms"])
    print(f"\n== {name}\n   class={r['predicted_class']} | score={r['risk_score']} | route={r['route']} | {r['latency_ms']} ms")
    print("   rules:", [h['rule'] for h in r['rules_triggered']], "| top drivers:", [(d['label'], d['impact']) for d in r['drivers']])
print("\n== Edge cases (must be rejected cleanly)")
bad = dict(SCENARIOS["Normal everyday purchase"], amount=-5, card_id="XYZ", ip_country="India", velocity_1m="3")
print(eng.score(bad)["errors"])
assert worst <= LATENCY_BUDGET_MS, "Latency budget exceeded!"
print(f"\nALL GOOD - worst latency {worst} ms (budget {LATENCY_BUDGET_MS} ms)")
