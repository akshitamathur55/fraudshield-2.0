import os, sys, json
ROOT="/home/claude/FraudShield2.0"; sys.path.insert(0,ROOT); os.chdir(ROOT)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
IMG="/home/claude/report/img"; M,G,L,DK,P="#006A4E","#00D084","#30BA8F","#06231F","#E3F0EA"
def save(fig,n): fig.savefig(f"{IMG}/{n}.png",dpi=200,bbox_inches="tight",facecolor="white"); plt.close(fig)

# ---- sequence diagram ----
fig,ax=plt.subplots(figsize=(9,6.2)); ax.axis("off"); parts=["Analyst","Dashboard\n(Streamlit)","Engine\nscore()","Validator","Rules","Graph\nengine","ML model","Explainer"]; xs=[i*1.25 for i in range(len(parts))]
for x,p in zip(xs,parts):
    ax.add_patch(FancyBboxPatch((x-.5,9.2),1,.75,boxstyle="round,pad=0.02",fc=P,ec=M)); ax.text(x,9.57,p,ha="center",va="center",fontsize=8,weight="bold"); ax.plot([x,x],[9.2,.2],ls="--",color="#9CA3AF",lw=.8)
msgs=[(0,1,"1  Select scenario, press Execute",8.75),(1,2,"2  score(payload, thresholds)",8.2),(2,3,"3  validate_payload()",7.8),(3,2,"4  clean payload / errors",7.3),(2,4,"5  run_rules()",6.7),(4,2,"6  rule hits",6.2),(2,5,"7  stats(user, card, device)",5.6),(5,2,"8  (users, cards) on device",5.1),(2,6,"9  predict_proba(features)",4.5),(6,2,"10  class probabilities",4.0),(2,7,"11  occlusion drivers (try/except)",3.4),(7,2,"12  top-3 drivers",2.9),(2,1,"13  result: score, class, route, reasons",2.2),(1,0,"14  banner, gauge, explanation",1.6)]
for a,b,t,y in msgs:
    ax.annotate("",xy=(xs[b],y),xytext=(xs[a],y),arrowprops=dict(arrowstyle="->",color=M if a<b else "#6B7280",ls="-" if a<b else "--",lw=1.1))
    ax.text((xs[a]+xs[b])/2,y+.1,t,ha="center",va="bottom",fontsize=7.2)
ax.set_xlim(-.8,xs[-1]+.8); ax.set_ylim(0,10.2); save(fig,"sequence")

# ---- gantt ----
fig,ax=plt.subplots(figsize=(9,3.8))
tasks=[("Requirements & design documents",0,1,"#A5C9BA"),("Data generator (data_gen.py)",0.5,1.5,L),("Feature engineering + training",1.5,2.5,L),("Rules, graph, engine assembly",2.5,3.5,M),("Streamlit dashboard (3 screens)",3.5,4.5,M),("Live stream simulator",4.2,4.9,G),("UI palette, light/dark, guide",4.5,5.4,G),("Testing, experiments, tuning",4.9,5.8,"#F59E0B"),("README, report, presentation",5.3,6.2,"#A5C9BA")]
for i,(n,a,b,c) in enumerate(tasks[::-1]): ax.barh(i,b-a,left=a,color=c,ec="white",height=.62); ax.text(a+(b-a)/2,i,f"{n}" if False else "",ha="center")
ax.set_yticks(range(len(tasks))); ax.set_yticklabels([t[0] for t in tasks[::-1]],fontsize=8); ax.set_xticks([0.5+i for i in range(6)]); ax.set_xticklabels([f"Day {i+1}" for i in range(6)],fontsize=8); ax.set_xlim(0,6.3); ax.grid(axis="x",ls=":",alpha=.5); ax.set_title("Development schedule (relative effort per work package)",fontsize=11); ax.spines[:].set_visible(False)
save(fig,"gantt")

# ---- risk bands with example scenarios ----
from core.model_wrapper import FraudShieldEngine
from core.scenarios import SCENARIOS
e=FraudShieldEngine(); res={k:e.score(v) for k,v in SCENARIOS.items()}; json.dump({k:[v["risk_score"],v["predicted_class"],v["route"]] for k,v in res.items()},open("/home/claude/report/scen.json","w"))
fig,ax=plt.subplots(figsize=(9,2.6)); ax.barh(0,30,color="#00D084",height=.5); ax.barh(0,40,left=30,color="#F59E0B",height=.5); ax.barh(0,30,left=70,color="#EF4444",height=.5)
for x,t in ((15,"ALLOW  (< 30)"),(50,"CHALLENGE  (30 - 70)"),(85,"HARD BLOCK  (> 70)")): ax.text(x,0,t,ha="center",va="center",fontsize=9,weight="bold",color="#04110F" if x<80 else "white")
short={"Normal everyday purchase":"Normal","Launch Card Testing Automated Script Attack":"Card testing","Account Takeover (new device + payee change)":"Account takeover","APP Scam (trusted device, big transfer to new payee)":"APP scam","Card-Not-Present Credit Card Fraud":"CNP fraud"}
for k,(sc,c,r) in {k:(v["risk_score"],v["predicted_class"],v["route"]) for k,v in res.items()}.items():
    off=.55 if short[k] in("Normal","Account takeover","CNP fraud") else -.55
    ax.annotate(f"{short[k]}\n{sc:.0f}",xy=(sc,.27 if off>0 else -.27),xytext=(min(max(sc,6),94)+(0 if short[k]!="Card testing" else -6),off+(0 if off>0 else -.18)),ha="center",va="bottom" if off>0 else "top",fontsize=7.5,arrowprops=dict(arrowstyle="-",color="#374151"))
ax.set_xlim(0,100); ax.set_ylim(-1.3,1.3); ax.set_xlabel("Risk score (0 - 100)"); ax.set_yticks([]); ax.spines[:].set_visible(False); ax.set_title("Routing bands and where the five demo scenarios fall",fontsize=11)
save(fig,"risk_bands")

# ---- wireframes ----
def box(ax,x,y,w,h,txt="",fc="#FFFFFF",ec=M,fs=7,bold=False,tc="#111"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.005,rounding_size=0.01",fc=fc,ec=ec,lw=.8)); 
    if txt: ax.text(x+w/2,y+h/2,txt,ha="center",va="center",fontsize=fs,weight="bold" if bold else "normal",color=tc)
fig,ax=plt.subplots(figsize=(9,5.6)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off"); ax.add_patch(Rectangle((0,0),1,1,fc="#F2F3F4",ec="#999"))
box(ax,.02,.91,.5,.07,"FraudShield 2.0   - title and tagline",fc="#F2F3F4",ec="none",fs=8,bold=True); box(ax,.78,.915,.2,.06,"(o--)  Dark mode switch",fc=P,fs=7)
for i,t in enumerate(["Last decision ms","Average ms","AI accuracy","Payments checked"]): box(ax,.02+i*.245,.80,.23,.09,t,fc=P,fs=7)
for i,t in enumerate(["Start here","Check a payment","Live feed","Connections map","Money saved"]): box(ax,.02+i*.14,.74,.135,.045,t,fc=G if i==1 else "#FFFFFF",fs=6.5)
box(ax,.02,.04,.46,.68,"",fc="#FFFFFF"); ax.text(.04,.70,"1. Choose or edit a payment",fontsize=8,weight="bold",va="top")
box(ax,.04,.60,.42,.06,"Ready-made scenario  [drop-down]",fs=7); box(ax,.04,.52,.42,.06,"scenario story (one sentence)",fc=P,fs=7)
for r in range(2):
    for c in range(2): box(ax,.04+c*.215,.43-r*.08,.205,.06,["Amount (Rs)","Payments / 60 s","Hours since payee change","Account age"][r*2+c],fs=6.5)
box(ax,.04,.27,.205,.06,"IP country",fs=6.5); box(ax,.255,.27,.205,.06,"[ ] New device",fs=6.5); box(ax,.04,.20,.42,.05,"> More fields (IDs, device, usual spend)",fc="#F2F3F4",fs=6.5)
ax.text(.04,.17,"2. Set how strict to be",fontsize=8,weight="bold",va="top"); box(ax,.04,.09,.42,.04,"threshold slider  ( Allow < 30 ... Block > 70 )",fs=6.5); box(ax,.04,.045,.42,.04,"EXECUTE SCORING EVALUATION",fc=G,fs=7,bold=True)
ax.text(.52,.70,"What happened to this payment?",fontsize=8,weight="bold",va="top")
box(ax,.52,.61,.46,.07,"DECISION BANNER  (APPROVED / CHALLENGE / BLOCKED)",fc="#EF4444",fs=7,bold=True,tc="white"); box(ax,.52,.51,.46,.08,"Plain-English summary card",fc=P,fs=7)
box(ax,.52,.31,.225,.18,"Riskometer\\n(gauge 0-100)".replace("\\n","\n"),fs=7); box(ax,.755,.31,.225,.18,"Class confidence\nbar chart",fs=7)
box(ax,.52,.19,.46,.10,"How we got here:  1 Data - 2 Rules - 3 Connections - 4 AI - 5 Decision",fc=P,fs=6.5); box(ax,.52,.075,.46,.10,"Top risk drivers (bar chart)   +   What should the team do?",fs=6.5)
save(fig,"wire_check")
fig,ax=plt.subplots(figsize=(9,5.2)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off"); ax.add_patch(Rectangle((0,0),1,1,fc="#F2F3F4",ec="#999"))
box(ax,.02,.90,.96,.08,"Header + theme switch + metrics bar",fc=P,fs=7.5); box(ax,.02,.77,.96,.11,"",fc="#FFFFFF"); 
for i,t in enumerate(["Live stream: ON  (switch)","Seconds per payment [slider]","Share of attacks [slider]","Allow / Block thresholds"]): box(ax,.03+i*.24,.79,.225,.07,t,fc=P,fs=6.5)
ax.text(.03,.745,"[LIVE]  payments are arriving...        legend:  Allowed | Challenged | Blocked",fontsize=7,va="center")
for i,t in enumerate(["Payments checked","Alerts raised","Blocked","Fraud flagged x/y","Good customers flagged"]): box(ax,.02+i*.195,.64,.185,.08,t,fc=P,fs=6.5)
box(ax,.02,.58,.96,.04,"BLINKING ALERT BANNER for the latest challenged / blocked payment",fc="#EF4444",fs=7,bold=True,tc="white")
box(ax,.02,.29,.96,.27,"",fc="#FFFFFF"); ax.text(.03,.545,"Time | Payment | Amount | Actual (hidden) | Predicted | Risk | Decision | Speed",fontsize=6.8,va="top",weight="bold")
for i,(c,t) in enumerate([("#BFEBD9","row: ALLOW"),("#FBE3AE","row: CHALLENGE"),("#F7B4B4","row: HARD BLOCK"),("#BFEBD9","row: ALLOW")]): box(ax,.03,.49-i*.05,.94,.04,t,fc=c,ec="none",fs=6.5)
box(ax,.02,.05,.47,.22,"Risk-score line chart (last 60)\nwith threshold lines",fs=7); box(ax,.51,.05,.47,.22,"Latest alerts: why + what to do (cards)",fs=7)
save(fig,"wire_live")
print("ok")
