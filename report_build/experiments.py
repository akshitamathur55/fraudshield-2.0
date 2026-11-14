"""Runs every experiment used in the report and writes results.json + chart PNGs."""
import os, sys, json, time, pickle, warnings
warnings.filterwarnings("ignore")
ROOT = "/home/claude/FraudShield2.0"; sys.path.insert(0, ROOT); os.chdir(ROOT)
IMG = "/home/claude/report/img"
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, confusion_matrix, classification_report
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
from core.config import *
from core.features import FEATURES, NICE, build_features
from core.graph_engine import GraphEngine
from core.rules_engine import run_rules

G_, M_, L_, C_, D_ = "#00D084", "#006A4E", "#30BA8F", "#0B3B2E", "#A5C9BA"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 12, "axes.labelsize": 10, "figure.dpi": 100})
_orig=plt.subplots
def _sub(*a,**k):
    if 'figsize' in k: w,h=k['figsize']; k['figsize']=(w*.8,h*.8)
    return _orig(*a,**k)
plt.subplots=_sub
R = {}
CN = [CLASSES[i] for i in range(5)]

df = pd.read_csv(DATA_PATH)
graph = GraphEngine().build(df)
X = np.array([build_features(r, *graph.stats(r["user_id"], r["card_id"], r["device_id"])) for r in df.to_dict("records")], float)
y = df["label"].values
idx = np.arange(len(y))
Xtr, Xte, ytr, yte, itr, ite = train_test_split(X, y, idx, test_size=0.2, stratify=y, random_state=42)
R["dataset"] = {"rows": len(df), "train": len(ytr), "test": len(yte), "counts": {CLASSES[k]: int(v) for k, v in pd.Series(y).value_counts().sort_index().items()},
                "test_counts": {CLASSES[k]: int(v) for k, v in pd.Series(yte).value_counts().sort_index().items()},
                "users": int(df.user_id.nunique()), "cards": int(df.card_id.nunique()), "devices": int(df.device_id.nunique()),
                "graph_nodes": graph.G.number_of_nodes(), "graph_edges": graph.G.number_of_edges()}
# descriptive stats per class
desc = df.groupby("label").agg(amount_mean=("amount", "mean"), amount_median=("amount", "median"), vel_mean=("velocity_1m", "mean"),
        new_dev=("is_new_device", "mean"), foreign_ip=("ip_country", lambda s: (s != "IN").mean()), payee_med=("payee_changed_hours", "median"))
R["desc"] = {CLASSES[k]: {c: float(v) for c, v in row.items()} for k, row in desc.iterrows()}

def hgb(**kw):
    p = dict(max_iter=150, max_depth=5, learning_rate=0.1, random_state=42); p.update(kw)
    return HistGradientBoostingClassifier(**p)
def fit_w(m, Xa, ya): m.fit(Xa, ya, sample_weight=compute_sample_weight("balanced", ya)); return m
def met(yt, yp): return dict(acc=accuracy_score(yt, yp), prec=precision_score(yt, yp, average="macro"), rec=recall_score(yt, yp, average="macro"), f1=f1_score(yt, yp, average="macro"))

# ---------------- model comparison ----------------
models = {"Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced")),
          "Decision Tree (depth 8)": DecisionTreeClassifier(max_depth=8, class_weight="balanced", random_state=42),
          "Random Forest (200 trees)": RandomForestClassifier(n_estimators=200, class_weight="balanced", n_jobs=2, random_state=42),
          "Gradient Boosting (HGB, final)": hgb()}
comp = {}
for name, m in models.items():
    t0 = time.perf_counter()
    if name.startswith("Gradient"): fit_w(m, Xtr, ytr)
    else: m.fit(Xtr, ytr)
    ft = time.perf_counter() - t0
    yp = m.predict(Xte)
    x1 = Xte[:1]; m.predict_proba(x1)
    t0 = time.perf_counter()
    for _ in range(200): m.predict_proba(x1)
    lat = (time.perf_counter() - t0) / 200 * 1000
    comp[name] = dict(**met(yte, yp), fit_s=ft, lat_ms=lat)
R["comparison"] = comp
final = models["Gradient Boosting (HGB, final)"]
yp = final.predict(Xte); proba = final.predict_proba(Xte)
cm = confusion_matrix(yte, yp)
rep = classification_report(yte, yp, target_names=CN, output_dict=True, digits=4)
R["final"] = {"metrics": met(yte, yp), "cm": cm.tolist(), "report": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in rep.items() if isinstance(v, dict)}}

# cross validation
skf = StratifiedKFold(5, shuffle=True, random_state=42); cvs = []
for a, b in skf.split(X, y):
    m = fit_w(hgb(), X[a], y[a]); cvs.append(f1_score(y[b], m.predict(X[b]), average="macro"))
R["cv"] = {"folds": cvs, "mean": float(np.mean(cvs)), "std": float(np.std(cvs))}

# hyper-parameter grid (3-fold on training set)
grid = []
sk3 = StratifiedKFold(3, shuffle=True, random_state=42)
for d_ in (3, 5, 8):
    for lr in (0.05, 0.1, 0.2):
        for it in (100, 150, 300):
            sc = []
            for a, b in sk3.split(Xtr, ytr):
                m = fit_w(hgb(max_depth=d_, learning_rate=lr, max_iter=it), Xtr[a], ytr[a]); sc.append(f1_score(ytr[b], m.predict(Xtr[b]), average="macro"))
            grid.append(dict(depth=d_, lr=lr, iters=it, f1=float(np.mean(sc))))
R["grid"] = grid

# ---------------- ablations ----------------
te_rows = df.iloc[ite].to_dict("records")
def rule_pred(r):
    h = run_rules(r); return CLASS_IDS[h[0]["class"]] if h else 0
rp = np.array([rule_pred(r) for r in te_rows])
hy = yp.copy()
for i, r in enumerate(te_rows):
    h = run_rules(r)
    if h: hy[i] = CLASS_IDS[h[0]["class"]]
abl = {"Rules only (Rule 1 + Rule 2)": met(yte, rp), "ML model only": met(yte, yp), "Hybrid: rules override + ML": met(yte, hy)}
groups = {"Without graph features (device sharing)": ["device_user_count", "device_card_count"],
          "Without velocity / micro-amount features": ["velocity_1m", "is_micro"],
          "Without payee-change features": ["payee_changed_hours", "recent_payee_change"],
          "Without device / IP features": ["is_new_device", "ip_mismatch"],
          "Without amount features": ["amount_log", "amount_ratio"]}
feat_abl = {}
for nm, drop in groups.items():
    keep = [i for i, f in enumerate(FEATURES) if f not in drop]
    m = fit_w(hgb(), Xtr[:, keep], ytr); feat_abl[nm] = met(yte, m.predict(Xte[:, keep]))
R["ablation"] = abl; R["feature_ablation"] = feat_abl
hy_rep = classification_report(yte, hy, target_names=CN, output_dict=True)
R["hybrid_per_class_f1"] = {c: float(hy_rep[c]["f1-score"]) for c in CN}
R["rules_per_class_recall"] = {c: float(classification_report(yte, rp, target_names=CN, output_dict=True, zero_division=0)[c]["recall"]) for c in CN}

# permutation importance
pi = permutation_importance(final, Xte, yte, scoring="f1_macro", n_repeats=5, random_state=42)
imp = sorted(zip(FEATURES, pi.importances_mean, pi.importances_std), key=lambda t: -t[1])
R["perm_importance"] = [(f, float(m), float(s)) for f, m, s in imp]

# misclassified
mis = np.where(yp != yte)[0]
R["errors"] = {"n": int(len(mis)), "pairs": {}}
for i in mis:
    k = f"{CLASSES[int(yte[i])]} -> {CLASSES[int(yp[i])]}"; R["errors"]["pairs"][k] = R["errors"]["pairs"].get(k, 0) + 1
R["errors"]["examples"] = [dict(true=CLASSES[int(yte[i])], pred=CLASSES[int(yp[i])], amount=float(te_rows[i]["amount"]), ratio=float(Xte[i][1]), vel=int(te_rows[i]["velocity_1m"]),
                                payee=float(te_rows[i]["payee_changed_hours"]), new_dev=int(te_rows[i]["is_new_device"]), ip=te_rows[i]["ip_country"], p_legit=float(proba[i][0])) for i in mis[:6]]

# threshold sweep on test risk
risk = (1 - proba[:, 0]) * 100; fraud = yte != 0
sweep = []
for a in range(5, 100, 5):
    sweep.append(dict(allow=a, fraud_allowed=float((risk[fraud] < a).mean() * 100), legit_flagged=float((risk[~fraud] >= a).mean() * 100)))
R["sweep"] = sweep
combos = []
for a, b in ((20, 60), (30, 70), (40, 80), (50, 90)):
    combos.append(dict(allow=a, block=b, fraud_allowed=float((risk[fraud] < a).mean() * 100), fraud_blocked=float((risk[fraud] > b).mean() * 100),
                       legit_challenged=float(((risk[~fraud] >= a) & (risk[~fraud] <= b)).mean() * 100), legit_blocked=float((risk[~fraud] > b).mean() * 100)))
R["combos"] = combos

# ---------------- latency benchmark ----------------
from core.model_wrapper import FraudShieldEngine
from core.scenarios import SCENARIOS
from core.validation import validate_payload
eng = FraudShieldEngine(); sc = list(SCENARIOS.values())
for p in sc: eng.score(p)
lat = []
for i in range(1000): lat.append(eng.score(sc[i % 5])["latency_ms"])
lat = np.array(lat); R["latency"] = dict(mean=float(lat.mean()), p50=float(np.percentile(lat, 50)), p95=float(np.percentile(lat, 95)), p99=float(np.percentile(lat, 99)), max=float(lat.max()), min=float(lat.min()), n=1000)
comp_t = {k: [] for k in ["Schema validation", "Business rules", "Graph lookup", "Feature building", "ML inference", "Explanation"]}
for i in range(500):
    p = sc[i % 5]
    t = time.perf_counter(); v = validate_payload(p); comp_t["Schema validation"].append(time.perf_counter() - t)
    t = time.perf_counter(); run_rules(v); comp_t["Business rules"].append(time.perf_counter() - t)
    t = time.perf_counter(); du, dc = eng.graph.stats(v["user_id"], v["card_id"], v["device_id"]); comp_t["Graph lookup"].append(time.perf_counter() - t)
    t = time.perf_counter(); x = np.array(build_features(v, du, dc), float); comp_t["Feature building"].append(time.perf_counter() - t)
    t = time.perf_counter(); pr = eng.model.predict_proba(x.reshape(1, -1))[0]; comp_t["ML inference"].append(time.perf_counter() - t)
    t = time.perf_counter(); eng._explain(x, pr[0]); comp_t["Explanation"].append(time.perf_counter() - t)
R["latency_components_ms"] = {k: float(np.mean(v) * 1000) for k, v in comp_t.items()}

# ---------------- stream simulation ----------------
from core.stream_sim import StreamSimulator
sim = StreamSimulator(seed=11, attack_prob=0.15); ev = []
for _ in range(3000):
    p, truth = sim.next(); r = eng.score(p); ev.append(dict(truth=truth, route=r["route"], pred=r["predicted_class"], vel=p["velocity_1m"], lat=r["latency_ms"], risk=r["risk_score"]))
E = pd.DataFrame(ev); st = {}
for t_, g in E.groupby("truth"):
    st[t_] = dict(n=int(len(g)), flagged=float((g.route != "ALLOW").mean() * 100), blocked=float((g.route == "HARD BLOCK").mean() * 100), correct_class=float((g.pred == t_).mean() * 100), lat=float(g.lat.mean()))
R["stream"] = {"events": 3000, "by_class": st, "false_alarm_pct": float((E[E.truth == "Legitimate"].route != "ALLOW").mean() * 100),
               "attack_share": float((E.truth != "Legitimate").mean() * 100), "avg_lat": float(E.lat.mean()), "max_lat": float(E.lat.max())}
ct = E[E.truth == "Card Testing"]; R["stream"]["card_test_by_pos"] = {int(k): float((g.route != "ALLOW").mean() * 100) for k, g in ct.groupby("vel")}
R["stream"]["card_test_pos_n"] = {int(k): int(len(g)) for k, g in ct.groupby("vel")}

# ---------------- ROI ----------------
from core.roi_calc import compute_roi
base = compute_roi(50e7, 1500, 0.02, 0.5, 0.92, 0.02, 0.0012); R["roi"] = base
R["roi_rate"] = [(fr, compute_roi(50e7, 1500, fr / 100, 0.5, 0.92, 0.02, 0.0012)["total_monthly_benefit"]) for fr in (0.5, 1, 1.5, 2, 3, 4, 5)]
R["roi_vol"] = [(v, compute_roi(v * 1e7, 1500, 0.02, 0.5, 0.92, 0.02, 0.0012)["total_monthly_benefit"]) for v in (5, 25, 50, 100, 200, 400)]
json.dump(R, open("/home/claude/report/results.json", "w"), indent=1)

# ================= CHARTS =================
def save(fig, name): fig.tight_layout(); fig.savefig(f"{IMG}/{name}.png", dpi=200, bbox_inches="tight"); plt.close(fig)
# 1 class distribution
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
cnt = R["dataset"]["counts"]; cols = [D_, "#EF4444", "#F59E0B", L_, M_]
ax[0].bar(range(5), list(cnt.values()), color=cols); ax[0].set_xticks(range(5)); ax[0].set_xticklabels([c.replace(" ", "\n") for c in cnt], fontsize=8); ax[0].set_title("Rows per class"); ax[0].set_ylabel("Transactions")
for i, v in enumerate(cnt.values()): ax[0].text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
ax[1].pie(list(cnt.values()), labels=None, colors=cols, startangle=90, wedgeprops=dict(width=.45)); ax[1].set_title("Share of dataset")
ax[1].legend([f"{k} ({v/sum(cnt.values())*100:.1f}%)" for k, v in cnt.items()], loc="center left", bbox_to_anchor=(.95, .5), fontsize=8, frameon=False)
save(fig, "class_distribution")
# 2 feature behaviour by class (4 panels)
fig, ax = plt.subplots(2, 2, figsize=(9, 6)); d_ = R["desc"]; names = list(d_)
for a, (k, t) in zip(ax.ravel(), [("amount_median", "Median amount (Rs)"), ("vel_mean", "Mean velocity (txns / 60 s)"), ("new_dev", "Share from new device"), ("foreign_ip", "Share with foreign IP")]):
    a.bar(range(5), [d_[n][k] for n in names], color=cols); a.set_xticks(range(5)); a.set_xticklabels([n.replace(" ", "\n") for n in names], fontsize=7); a.set_title(t, fontsize=10)
save(fig, "feature_behaviour")
# 3 confusion matrix
fig, ax = plt.subplots(figsize=(6.2, 5)); im = ax.imshow(cm, cmap="Greens")
ax.set_xticks(range(5)); ax.set_yticks(range(5)); ax.set_xticklabels([c.replace(" ", "\n") for c in CN], fontsize=8); ax.set_yticklabels(CN, fontsize=8)
for i in range(5):
    for j in range(5): ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=10)
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title("Confusion matrix (test set, n = %d)" % len(yte)); ax.spines[:].set_visible(False)
save(fig, "confusion_matrix")
# 4 per-class P/R/F1
fig, ax = plt.subplots(figsize=(8, 3.6)); w = .26
for k, (m, c) in enumerate([("precision", M_), ("recall", G_), ("f1-score", C_)]):
    ax.bar(np.arange(5) + (k - 1) * w, [rep[c_][m] for c_ in CN], w, label=m.capitalize(), color=c)
ax.set_xticks(range(5)); ax.set_xticklabels(CN, fontsize=8); ax.set_ylim(.9, 1.005); ax.legend(frameon=False, ncol=3, loc="lower center"); ax.set_title("Per-class precision, recall and F1 (axis starts at 0.90)")
save(fig, "per_class_metrics")
# 5 model comparison
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6)); nm = list(comp)
ax[0].barh(nm[::-1], [comp[n]["f1"] for n in nm][::-1], color=[G_ if "final" in n else D_ for n in nm][::-1]); ax[0].set_xlim(.85, 1.0); ax[0].set_title("Macro F1 (test set)")
for i, n in enumerate(nm[::-1]): ax[0].text(comp[n]["f1"], i, f" {comp[n]['f1']:.3f}", va="center", fontsize=8)
ax[1].barh(nm[::-1], [comp[n]["lat_ms"] for n in nm][::-1], color=[G_ if "final" in n else D_ for n in nm][::-1]); ax[1].set_title("Single-row inference time (ms)"); ax[1].set_yticklabels([])
for i, n in enumerate(nm[::-1]): ax[1].text(comp[n]["lat_ms"], i, f" {comp[n]['lat_ms']:.2f}", va="center", fontsize=8)
save(fig, "model_comparison")
# 6 permutation importance
fig, ax = plt.subplots(figsize=(7.5, 4.2)); top = imp[:10][::-1]
ax.barh([NICE[f] for f, _, _ in top], [m for _, m, _ in top], xerr=[s for _, _, s in top], color=G_, ecolor=M_); ax.set_xlabel("Drop in macro F1 when the feature is shuffled"); ax.set_title("Permutation feature importance (top 10)")
save(fig, "feature_importance")
# 7 hyperparameter heatmap
fig, ax = plt.subplots(1, 3, figsize=(9.5, 3.2), sharey=True)
for a, it in zip(ax, (100, 150, 300)):
    M = np.array([[next(g["f1"] for g in grid if g["depth"] == d_ and g["lr"] == lr and g["iters"] == it) for lr in (0.05, 0.1, 0.2)] for d_ in (3, 5, 8)])
    a.imshow(M, cmap="Greens", vmin=min(g["f1"] for g in grid), vmax=max(g["f1"] for g in grid)); a.set_xticks(range(3)); a.set_xticklabels([0.05, 0.1, 0.2]); a.set_yticks(range(3)); a.set_yticklabels([3, 5, 8]); a.set_title(f"max_iter = {it}", fontsize=10); a.set_xlabel("learning rate")
    for i in range(3):
        for j in range(3): a.text(j, i, f"{M[i,j]:.4f}", ha="center", va="center", fontsize=7)
ax[0].set_ylabel("max_depth"); save(fig, "hyperparameter_grid")
# 8 ablation
fig, ax = plt.subplots(figsize=(8, 3.8)); lab = list(abl) + list(feat_abl); val = [abl[k]["f1"] for k in abl] + [feat_abl[k]["f1"] for k in feat_abl]
colr = [D_, M_, G_] + [L_] * len(feat_abl)
ax.barh(lab[::-1], val[::-1], color=colr[::-1]); ax.set_xlim(.0, 1.05)
for i, v in enumerate(val[::-1]): ax.text(v, i, f" {v:.3f}", va="center", fontsize=8)
ax.set_title("Macro F1: rules vs ML vs hybrid, and feature-group ablations"); ax.tick_params(axis="y", labelsize=8)
save(fig, "ablation")
# 9 threshold sweep
fig, ax = plt.subplots(figsize=(7.5, 3.8)); a_ = [s["allow"] for s in sweep]
ax.plot(a_, [s["fraud_allowed"] for s in sweep], "-o", color="#EF4444", label="Fraud wrongly allowed (%)", ms=4); ax.plot(a_, [s["legit_flagged"] for s in sweep], "-s", color=M_, label="Legitimate customers challenged/blocked (%)", ms=4)
ax.axvline(30, ls="--", color="#F59E0B"); ax.text(31, ax.get_ylim()[1] * .5, "default (30)", color="#B45309", fontsize=8); ax.set_xlabel("'Allow below' threshold (risk score)"); ax.set_ylabel("%"); ax.legend(frameon=False, fontsize=8); ax.set_title("Effect of the Allow threshold on fraud leakage vs. customer friction")
save(fig, "threshold_sweep")
# 10 latency histogram + components
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.5)); ax[0].hist(lat, bins=30, color=G_, edgecolor="white"); ax[0].set_xlim(lat.min() - 1, lat.max() + 2)
ax[0].axvline(R["latency"]["p50"], color=M_, ls="--"); ax[0].axvline(R["latency"]["p99"], color="#F59E0B", ls="--")
ax[0].text(.97, .95, f"median {R['latency']['p50']:.1f} ms\n99th pct {R['latency']['p99']:.1f} ms\nmax {R['latency']['max']:.1f} ms\n(budget: 100 ms)", transform=ax[0].transAxes, ha="right", va="top", fontsize=8)
ax[0].set_xlabel("End-to-end decision time (ms)"); ax[0].set_ylabel("Requests"); ax[0].set_title("Latency distribution (1,000 requests)")
lc = R["latency_components_ms"]; ax[1].barh(list(lc)[::-1], list(lc.values())[::-1], color=M_); ax[1].set_xlabel("Mean time (ms)"); ax[1].set_title("Where the time goes")
for i, v in enumerate(list(lc.values())[::-1]): ax[1].text(v, i, f" {v:.2f}", va="center", fontsize=8)
save(fig, "latency")
# 11 stream detection
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6)); cls = [c for c in CN if c in st]
ax[0].bar(range(len(cls)), [st[c]["flagged"] for c in cls], color=[D_ if c == "Legitimate" else G_ for c in cls]); ax[0].set_xticks(range(len(cls))); ax[0].set_xticklabels([c.replace(" ", "\n") for c in cls], fontsize=8)
ax[0].set_title("Share of transactions challenged or blocked (%)", fontsize=10)
for i, c in enumerate(cls): ax[0].text(i, st[c]["flagged"], f"{st[c]['flagged']:.1f}", ha="center", va="bottom", fontsize=8)
pos = sorted(R["stream"]["card_test_by_pos"]); ax[1].bar([str(p) for p in pos], [R["stream"]["card_test_by_pos"][p] for p in pos], color=[("#EF4444" if R["stream"]["card_test_by_pos"][p] < 50 else G_) for p in pos])
ax[1].set_xlabel("Payment number within the burst"); ax[1].set_title("Card-testing detection by burst position (%)", fontsize=10)
save(fig, "stream_detection")
# 12 ROI
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6)); parts = {"Stock not\nlost": base["inventory_loss_avoided"], "Chargeback\nfees": base["chargeback_fees_avoided"], "Penalty\nfine": base["monitoring_fine_avoided"], "Fewer false\nalarms": base["friction_savings"]}
ax[0].bar(list(parts), [v / 1e5 for v in parts.values()], color=[G_, M_, L_, D_]); ax[0].set_ylabel("Rs lakh / month"); ax[0].set_title("Monthly benefit by source (Rs 50 crore / month)", fontsize=10)
for i, v in enumerate(parts.values()): ax[0].text(i, v / 1e5, f"{v/1e5:.1f}", ha="center", va="bottom", fontsize=8)
ax[1].plot([r[0] for r in R["roi_rate"]], [r[1] / 1e5 for r in R["roi_rate"]], "-o", color=M_); ax[1].set_xlabel("Fraud rate (% of transactions)"); ax[1].set_ylabel("Total benefit (Rs lakh / month)"); ax[1].set_title("Sensitivity to fraud rate", fontsize=10)
save(fig, "roi")
# 13 palette
fig, ax = plt.subplots(figsize=(8, 1.9)); pal = [("Rich Black", "#04110F"), ("Dark Green", "#06231F"), ("Bangladesh", "#006A4E"), ("Mountain Meadow", "#30BA8F"), ("Caribbean", "#00D084"), ("Anti-Flash", "#F2F3F4"), ("Amber (warn)", "#F59E0B"), ("Red (danger)", "#EF4444")]
for i, (n, c) in enumerate(pal):
    ax.add_patch(plt.Rectangle((i, 0), .95, 1, color=c, ec="#999", lw=.5)); ax.text(i + .47, -.12, n, ha="center", va="top", fontsize=7); ax.text(i + .47, .5, c, ha="center", va="center", fontsize=7, color="white" if i < 4 or i == 7 else "black")
ax.set_xlim(0, 8); ax.set_ylim(-.4, 1); ax.axis("off"); save(fig, "palette")
print("done", R["final"]["metrics"], R["cv"]["mean"], R["latency"])
