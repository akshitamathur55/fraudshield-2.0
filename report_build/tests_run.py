import os, sys, json, copy, numpy as np
ROOT="/home/claude/FraudShield2.0"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from core.model_wrapper import FraudShieldEngine
from core.scenarios import SCENARIOS
from core.rules_engine import run_rules
from core.validation import validate_payload, ValidationError
import pandas as pd
eng=FraudShieldEngine(); S=SCENARIOS; N=S["Normal everyday purchase"]; CT=S["Launch Card Testing Automated Script Attack"]
out=[]
def add(i,cat,desc,inp,exp,act,ok): out.append(dict(id=i,cat=cat,desc=desc,inp=inp,exp=exp,act=act,ok=bool(ok)))
def summ(r): return "Rejected: "+str(len(r["errors"]))+" error(s)" if not r["valid"] else f"{r['predicted_class']} / {r['route']} / risk {r['risk_score']:.0f}"
# functional scenarios
r=eng.score(N); add("TC-01","Functional","Normal everyday purchase","amount 950, usual device, IN","Legitimate / ALLOW",summ(r),r["predicted_class"]=="Legitimate" and r["route"]=="ALLOW")
r=eng.score(CT); add("TC-02","Functional","Card-testing burst (5 txns of Rs 12 in 60 s)","amount 12, velocity 5, new device","Card Testing / HARD BLOCK",summ(r),r["predicted_class"]=="Card Testing" and r["route"]=="HARD BLOCK")
r=eng.score(S["Account Takeover (new device + payee change)"]); add("TC-03","Functional","Account takeover (new device, payee changed 3 min ago)","amount 9000, payee 0.05 h","Account Takeover / HARD BLOCK",summ(r),r["predicted_class"]=="Account Takeover" and r["route"]=="HARD BLOCK")
r=eng.score(S["APP Scam (trusted device, big transfer to new payee)"]); add("TC-04","Functional","APP scam (trusted device, 17x usual amount, payee 6 h old)","amount 28000, payee 6 h","APP Scam / not ALLOW",summ(r),r["predicted_class"]=="APP Scam" and r["route"]!="ALLOW")
r=eng.score(S["Card-Not-Present Credit Card Fraud"]); add("TC-05","Functional","Card-not-present fraud (foreign IP, night, 23x usual)","amount 32000, IP RU, 03:00","Credit Card Fraud / not ALLOW",summ(r),r["predicted_class"]=="Credit Card Fraud" and r["route"]!="ALLOW")
# validation
def bad(i,desc,mod,delete=None):
    p=copy.deepcopy(N); p.update(mod)
    if delete: p.pop(delete)
    r=eng.score(p); add(i,"Validation",desc,str(mod) if mod else f"missing {delete}","Rejected with error message",summ(r),not r["valid"])
bad("TC-06","Negative amount",dict(amount=-5))
bad("TC-07","Zero amount",dict(amount=0))
bad("TC-08","Malformed card_id",dict(card_id="XYZ"))
bad("TC-09","ip_country not ISO-2",dict(ip_country="India"))
bad("TC-10","velocity_1m supplied as text",dict(velocity_1m="3"))
bad("TC-11","Missing device_id",{},delete="device_id")
bad("TC-12","Non-hex device_id",dict(device_id="xyz!"))
bad("TC-13","Hour outside 0-23",dict(hour=25))
bad("TC-14","Boolean passed as amount",dict(amount=True))
bad("TC-15","NaN amount",dict(amount=float("nan")))
bad("TC-16","Negative payee_changed_hours",dict(payee_changed_hours=-1))
# rule boundaries
def rule_case(i,desc,mod,exp_rule,expect):
    p=validate_payload({**N,**mod}); hits=[h["rule"] for h in run_rules(p)]
    add(i,"Business rule",desc,str(mod),("Rule fires" if expect else "Rule does not fire"),("Fired: "+",".join(hits)) if hits else "No rule fired",(exp_rule in hits)==expect)
rule_case("TC-17","Rule 1 at amount boundary (Rs 50.00, 3 txns)",dict(amount=50.0,velocity_1m=3),"R1_CARD_TESTING",True)
rule_case("TC-18","Rule 1 just above boundary (Rs 50.01, 3 txns)",dict(amount=50.01,velocity_1m=3),"R1_CARD_TESTING",False)
rule_case("TC-19","Rule 1 with only 2 tiny txns",dict(amount=20.0,velocity_1m=2),"R1_CARD_TESTING",False)
rule_case("TC-20","Rule 2 at 10-minute boundary (0.1666 h, new device)",dict(is_new_device=True,payee_changed_hours=0.1666),"R2_ATO",True)
rule_case("TC-21","Rule 2 just outside window (0.17 h, new device)",dict(is_new_device=True,payee_changed_hours=0.17),"R2_ATO",False)
rule_case("TC-22","Rule 2 requires a new device (known device, payee 0.05 h)",dict(is_new_device=False,payee_changed_hours=0.05),"R2_ATO",False)
# configurability, fault isolation, graph, latency
r=eng.score(CT,allow_below=0,block_above=100); add("TC-23","Configuration","Widen thresholds to 0 / 100 on a card-testing attack","allow_below=0, block_above=100","CHALLENGE (score 90 lies between cut-offs)",summ(r),r["route"]=="CHALLENGE")
r=eng.score(N,allow_below=0,block_above=0); add("TC-24","Configuration","Strict thresholds 0 / 0 on a normal payment","allow_below=0, block_above=0","Not ALLOW (any score >= 0 is challenged or blocked)",summ(r),r["route"]!="ALLOW")
orig=eng._explain
def boom(*a,**k): raise RuntimeError("simulated explanation failure")
eng._explain=boom; r=eng.score(CT); eng._explain=orig
add("TC-25","Fault isolation (NFR-2)","Explanation module raises an exception","_explain() patched to raise","Decision still returned, explain_ok = False",f"{r['predicted_class']} / {r['route']} / explain_ok={r['explain_ok']}",r["valid"] and r["route"]=="HARD BLOCK" and not r["explain_ok"])
G=eng.graph.G; hub=max([n for n in G if n[0]=="device"],key=lambda n:sum(1 for m in G.neighbors(n) if m[0]=="user"))
du,dc=eng.graph.stats("USR-999999","CRD-999999999999",hub[1]); add("TC-26","Graph","New customer + card appear on the most-shared known device","hub device (%d users known)"%(du-1),"device_user_count >= 3",f"users={du}, cards={dc}",du>=3)
lat=[eng.score(list(S.values())[i%5])["latency_ms"] for i in range(1000)]
add("TC-27","Performance (NFR-1)","1,000 end-to-end decisions","5 scenarios x 200","p99 <= 100 ms",f"p99 = {np.percentile(lat,99):.1f} ms, max = {max(lat):.1f} ms",np.percentile(lat,99)<=100)
r1=eng.score(N); r2=eng.score(N); add("TC-28","Determinism","Same payload scored twice","identical payload","Identical score and route",f"{r1['risk_score']} vs {r2['risk_score']}",r1["risk_score"]==r2["risk_score"] and r1["route"]==r2["route"])
json.dump(out,open("/home/claude/report/tests.json","w"),indent=1)
print(sum(t["ok"] for t in out),"/",len(out),"passed"); [print(t["id"],t["ok"],t["act"]) for t in out if not t["ok"]]
