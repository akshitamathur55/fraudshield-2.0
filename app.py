import os, json, time, html, re, math
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd, networkx as nx, plotly.graph_objects as go, streamlit as st
import streamlit.components.v1 as components
from core.config import *
from core.scenarios import SCENARIOS
from core.stream_sim import StreamSimulator
from core.theme import THEMES, ROUTE, css, plot_layout
from core.narrative import summary, pipeline_steps, reasons, CLASS_EXPLAIN, ROUTE_EXPLAIN

st.set_page_config(page_title="FraudShield 2.0", page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
ss = st.session_state
for _k, _v in dict(page="dashboard", dark=True, result=None, payload=None, stream_on=False, sim=None, _thr=(ALLOW_BELOW, BLOCK_ABOVE), _secs=1.0, _atk=15).items():
    ss.setdefault(_k, _v)
MODE = "dark" if ss["dark"] else "light"; T = THEMES[MODE]

# ------------------------------------------------------------------ styling
st.markdown(css(MODE, ss["stream_on"], ss["page"]), unsafe_allow_html=True)
_raw = css(MODE, ss["stream_on"], ss["page"]).replace("<style>", "").replace("</style>", "")
components.html("<script>const d=window.parent.document;let e=d.getElementById('fs-theme');"
                "if(!e){e=d.createElement('style');e.id='fs-theme';d.head.appendChild(e);}"
                f"e.textContent={json.dumps(_raw)};</script>", height=0)

# ------------------------------------------------------------------ helpers
def inr(x):
    s = str(int(round(abs(x)))); head, tail = s[:-3], s[-3:]
    if head:
        parts = []
        while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if x < 0 else "") + "Rs " + s

def rgba(hex_, a):
    h = hex_.lstrip("#"); return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

def md2html(s): return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

def card(key):
    """A keyed container styled as a rounded card (plain container on older Streamlit)."""
    try: return st.container(key="card_" + key)
    except TypeError: return st.container()

# One highlight colour per module (used by the top bar, the page title, the cards and the main button)
MOD = {"dashboard": "#3B82F6", "check": "#8B5CF6", "live": "#F43F5E", "map": "#06B6D4", "start": "#F59E0B"}

def header(title, sub):
    st.markdown(f'<div class="pagehead"><p class="pt">{title}</p><p class="ps">{sub}</p></div>', unsafe_allow_html=True)

def module_css(page):
    c = MOD[page]; nav = ""
    for k, col in MOD.items():
        on = k == page
        nav += (f".st-key-nav_{k}{{--c:{col}}}"
                f".st-key-nav_{k} button{{{'background:' + col + '!important;color:#fff!important;box-shadow:0 4px 14px ' + rgba(col, .35) + ';' if on else ''}}}"
                f".st-key-nav_{k} button:hover{{background:{rgba(col, .2) if not on else col}!important}}")
    return ("<style>.stApp{--mod:" + c + "}"
            ".block-container,[data-testid='stMainBlockContainer']{padding-top:3.6rem!important}header[data-testid='stHeader']{background:transparent!important}"                      # pulls the page up into the empty header band
            ".st-key-topnav{margin-bottom:.4rem}"
            "[class*='st-key-nav_'] button{width:100%;min-height:2.6rem;border-radius:12px;font-weight:600;padding:.35rem .4rem;"
            "background:var(--surface,transparent)!important;color:var(--text)!important;border:1px solid var(--border)!important;border-bottom:3px solid var(--c)!important}"
            "[class*='st-key-nav_'] button p{font-weight:600;white-space:nowrap}"
            + nav +
            f".pagehead{{border-left:5px solid {c};padding:.35rem 0 .35rem 1rem;margin:.6rem 0 1rem;border-radius:0 12px 12px 0;"
            f"background:linear-gradient(90deg,{rgba(c, .14)},transparent 70%)}}.pagehead p{{margin:0}}"
            f"[class*='st-key-card_']{{border-top:3px solid {c}!important}}"
            f".kpi{{border-top:3px solid {c}}}"
            f"button[kind='primary'],button[data-testid='stBaseButton-primary']{{background:{c}!important;border-color:{c}!important;color:#fff!important}}"
            ".zbar{display:flex;border-radius:10px;overflow:hidden;font-size:.78rem;font-weight:700;text-align:center;margin:.2rem 0 .5rem}"
            ".zbar div{padding:.38rem .2rem;white-space:nowrap;overflow:hidden}"
            ".rl{font-weight:700;margin:.2rem 0 0}.rh{font-size:.8rem;opacity:.75;margin:0 0 .3rem}"
            ".emptyhint{border:1.5px dashed var(--border);border-radius:14px;padding:.9rem 1.1rem;margin-bottom:.8rem}"
            "</style>")

def threshold_control(key):
    """Risk-score cut-offs: ONE two-handle slider + a live colour bar that shows what the numbers mean."""
    st.markdown('<p class="rl">Decision cut-offs (risk score 0-100)</p><p class="rh">Every payment gets a risk score. Drag the two handles to choose where '
                'it is allowed, challenged or blocked.</p>', unsafe_allow_html=True)
    lo, hi = st.slider("Left handle = Allow below this score · Right handle = Block above this score", 0, 100, ss["_thr"], key=key,
                       help="Lower numbers = stricter (more customers are challenged or blocked). Higher numbers = more relaxed (more fraud may slip through). "
                            "Default: Allow below 30, Block above 70.")
    ss["_thr"] = (lo, hi)
    seg = lambda r, w, t: (f'<div style="flex:{w};background:{ROUTE[r][0]};color:{ROUTE[r][1]}">{t}</div>' if w > 0 else "")
    st.markdown('<div class="zbar">' + seg("ALLOW", lo, f"Allow &lt; {lo}") + seg("CHALLENGE", hi - lo, f"Challenge {lo}-{hi}") + seg("HARD BLOCK", 100 - hi, f"Block &gt; {hi}") + "</div>"
                f'<p class="rh">Scores under <b>{lo}</b> go through · <b>{lo}-{hi}</b> ask the customer for an OTP / 3-D Secure · above <b>{hi}</b> are stopped.</p>', unsafe_allow_html=True)
    return lo, hi

def ct(title, sub=None):
    st.markdown(f'<p class="ct">{title}</p>' + (f'<p class="cs">{sub}</p>' if sub else ""), unsafe_allow_html=True)

def kpis(items):
    return '<div class="kpis">' + "".join(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="s {c}">{s}</div></div>' for l, v, s, c in items) + "</div>"

def pill(route, text):
    bg, fg = ROUTE[route]; return f'<span class="pill" style="background:{bg};color:{fg}">{html.escape(text)}</span>'

def html_table(rows, cols, bg=None):
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    body = "".join((f'<tr style="background:{bg(r)}">' if bg else "<tr>") + "".join(f"<td>{html.escape(str(r.get(c, '')))}</td>" for c in cols) + "</tr>" for r in rows)
    return f'<div style="overflow-x:auto"><table class="feed"><tr>{head}</tr>{body}</table></div>'

WORD = {"ALLOW": "LOW RISK", "CHALLENGE": "MEDIUM RISK", "HARD BLOCK": "HIGH RISK"}
ICON = {"ALLOW": "✔", "CHALLENGE": "!", "HARD BLOCK": "⛔"}
STATUS = {"ALLOW": "Allowed", "CHALLENGE": "Challenged", "HARD BLOCK": "Blocked"}

@st.cache_resource(show_spinner="Loading engine (first run trains the model, ~30 s)...")
def load_engine():
    if not os.path.exists(MODEL_PATH):
        from core.data_gen import generate; import train_pipeline
        generate(); train_pipeline.main()
    from core.model_wrapper import FraudShieldEngine
    return FraudShieldEngine()

engine = load_engine()
metrics = json.load(open(METRICS_PATH)) if os.path.exists(METRICS_PATH) else {}

def make_event(p, truth, res, ts):
    return dict(ts=ts, time=time.strftime("%H:%M:%S", time.localtime(ts)), txn=p["transaction_id"], user=p["user_id"], device=p["device_id"], amount=float(p["amount"]),
                truth=truth, pred=res["predicted_class"], risk=float(res["risk_score"]), route=res["route"], lat=float(res["latency_ms"]),
                why=reasons(res, p)[:3], fix=res["mitigation"])

# The feed starts EMPTY on every visit: nothing is pre-scored. Payments appear only when you run the demo
# (Check a payment / Live feed -> Live stream or Simulate fraud).
if "feed" not in ss: ss["feed"] = []

def add_event(p, truth):
    lo, hi = ss["_thr"]; res = engine.score(p, lo, hi)
    if res["valid"]:
        ss["feed"] = (ss["feed"] + [make_event(p, truth, res, time.time())])[-600:]
        if res["route"] == "HARD BLOCK": st.toast(f"BLOCKED {p['transaction_id']} - {res['predicted_class']} (risk {res['risk_score']})", icon="🚨")

def tick():
    """Advance the simulated stream by one payment (only when the Live stream switch is ON)."""
    if not ss["stream_on"]: return
    if ss["sim"] is None: ss["sim"] = StreamSimulator()
    ss["sim"].attack_prob = ss["_atk"] / 100
    p, truth = ss["sim"].next(); add_event(p, truth)

def inject_attack():
    if ss["sim"] is None: ss["sim"] = StreamSimulator()
    ss["sim"]._start_attack()
    while ss["sim"].queue:
        p, truth = ss["sim"].queue.popleft(); add_event(p, truth)

def fig_area(vals, lo, hi):
    fig = go.Figure(go.Scatter(y=vals, mode="lines", line=dict(color=T["accent"], width=2), fill="tozeroy", fillcolor=rgba(T["accent"], .16)))
    fig.add_hline(y=lo, line_dash="dash", line_color=ROUTE["CHALLENGE"][0]); fig.add_hline(y=hi, line_dash="dash", line_color=ROUTE["HARD BLOCK"][0])
    fig.update_layout(**plot_layout(MODE, 250, margin=dict(t=10, b=10, l=10, r=10))); fig.update_yaxes(range=[0, 100], gridcolor=T["border"]); fig.update_xaxes(visible=False)
    return fig

def fig_bars(labels, values, colors, height=250):
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, text=values, textposition="outside"))
    fig.update_layout(**plot_layout(MODE, height, margin=dict(t=20, b=10, l=10, r=10))); fig.update_yaxes(gridcolor=T["border"]); return fig

CFG = {"displayModeBar": False}

st.markdown(module_css(ss["page"]), unsafe_allow_html=True)   # module colours + top bar styling (after the theme CSS so it wins)

# ------------------------------------------------------------------ sidebar
NAV = [("dashboard", "📊", "Dashboard", "MAIN"), ("check", "⚡", "Check a payment", None), ("live", "📡", "Live feed", None),
       ("map", "🕸️", "Connections map", "ANALYTICS"), ("start", "🏠", "Start here", "HELP")]
with st.sidebar:
    st.markdown(f'<p class="brand">{APP_ICON} FraudShield 2.0</p><p class="brand-sub">Real-time, explainable fraud decisions</p>', unsafe_allow_html=True)
    st.markdown('<div class="navlabel">APPEARANCE</div>', unsafe_allow_html=True)
    st.button("🌙 Dark mode" if ss["dark"] else "☀️ Light mode", key="theme_btn", on_click=lambda: ss.update(dark=not ss["dark"]), help="Switch between dark and light mode.")
    ev_ = ss["feed"]; avg_ = sum(e["lat"] for e in ev_) / max(len(ev_), 1)
    _f1 = metrics.get("simulated_macro_f1", metrics.get("macro_f1", 0))
    _ieee = (f'<br>Real data (IEEE-CIS) ROC-AUC: <b>{metrics["ieee_roc_auc"]:.2f}</b><br>Trained on: <b>{metrics.get("rows", 0):,}</b> payments incl. <b>{metrics["ieee_rows"]:,}</b> real'
             if metrics.get("ieee_rows") else "")
    st.markdown(f'<div class="sidecard"><b>Engine status</b><br>Model: gradient-boosted trees<br>Accuracy (macro-F1, simulated): <b>{_f1 * 100:.1f}%</b>{_ieee}<br>Avg decision time: <b>{avg_:.1f} ms</b><br>Payments checked: <b>{len(ev_):,}</b></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ top navigation bar (fills the header band)
def top_nav():
    try: box = st.container(key="topnav")
    except TypeError: box = st.container()
    with box:
        for col, (key, icon, label, _sec) in zip(st.columns(len(NAV)), NAV):
            col.button(f"{icon} {label}", key=f"nav_{key}", on_click=lambda k=key: ss.update(page=k))

# ================================================================== PAGES
def page_dashboard():
    header("Fraud detection overview", "What the engine has seen and decided. Payments are simulated; every decision is made by the real engine.")
    def body():
        tick()
        ev = ss["feed"]; n = max(len(ev), 1); lo, hi = ss["_thr"]
        if not ev:
            st.markdown('<div class="emptyhint"><b>Nothing has been checked yet.</b> This dashboard fills up as payments are scored. '
                        'Open <b>⚡ Check a payment</b> to test one payment, or <b>📡 Live feed</b> and press <b>Live stream</b> / <b>Simulate fraud</b> to watch the engine work.</div>', unsafe_allow_html=True)
        alerts = [e for e in ev if e["route"] != "ALLOW"]; blocks = [e for e in ev if e["route"] == "HARD BLOCK"]; avg = sum(e["lat"] for e in ev) / n
        main, side = st.columns([3, 1.25])
        with main:
            st.markdown(kpis([("Payments checked", f"{len(ev):,}", "simulated + live", ""), ("Alerts raised", f"{len(alerts):,}", f"{len(alerts) / n * 100:.1f}% challenged or blocked", ""),
                              ("Hard blocks", f"{len(blocks):,}", f"{len(blocks) / n * 100:.1f}% of payments", "down" if blocks else ""), ("Avg decision time", f"{avg:.1f} ms", "budget: 100 ms", "up")]), unsafe_allow_html=True)
            a, b = st.columns(2)
            with a:
                with card("risk"):
                    ct("Risk score over time", "Last 80 payments; dashed lines are your thresholds"); st.plotly_chart(fig_area([e["risk"] for e in ev[-80:]], lo, hi), key="dash_area", config=CFG)
            with b:
                with card("dec"):
                    ct("Decisions by type", "How every payment was routed")
                    cnt = [sum(e["route"] == r for e in ev) for r in ("ALLOW", "CHALLENGE", "HARD BLOCK")]
                    st.plotly_chart(fig_bars(["Allowed", "Challenged", "Blocked"], cnt, [ROUTE[r][0] for r in ("ALLOW", "CHALLENGE", "HARD BLOCK")]), key="dash_bar", config=CFG)
            with card("recent"):
                ct("Recent decisions (audit log)", "Latest 8 payments")
                rows = [{"Time": e["time"], "Payment": e["txn"], "Amount": inr(e["amount"]), "Predicted": e["pred"], "Risk": f"{e['risk']:.0f}", "Decision": STATUS[e["route"]]} for e in reversed(ev[-8:])]
                st.markdown(html_table(rows, list(rows[0]), bg=lambda r: rgba(ROUTE[{v: k for k, v in STATUS.items()}[r["Decision"]]][0], .14)) if rows else "No payments yet.", unsafe_allow_html=True)
        with side:
            with card("cats"):
                ct("Fraud types detected", "By the AI model")
                for name, col in (("Credit Card Fraud", "#EF4444"), ("Account Takeover", "#F59E0B"), ("APP Scam", T["accent2"]), ("Card Testing", T["accent"])):
                    k_ = sum(e["pred"] == name for e in ev)
                    st.markdown(f'<div class="cat"><span><span style="color:{col}">●</span>&nbsp; {name}</span><b>{k_}</b></div>', unsafe_allow_html=True)
            with card("alerts"):
                ct("Latest alerts", "Newest first")
                last = [e for e in ev if e["route"] != "ALLOW"][-4:][::-1]
                st.markdown("".join(f'<div class="ar"><b>{e["pred"]} - {STATUS[e["route"]]}</b><span>{html.escape(("; ".join(e["why"]) or "-")[:120])}</span><br><em>{e["time"]} · {e["txn"]} · {inr(e["amount"])}</em></div>' for e in last) or '<span class="muted">No alerts yet.</span>', unsafe_allow_html=True)
            st.download_button("⬇ Download audit CSV", pd.DataFrame([{k: v for k, v in e.items() if k not in ("why", "fix", "ts")} for e in ev]).to_csv(index=False), "audit_log.csv", "text/csv", key="dl_audit")
    st.fragment(run_every=(ss["_secs"] if ss["stream_on"] else None))(body)()

SCEN_INFO = {
    "Normal everyday purchase": "A regular customer buys something at a normal amount from their usual device.",
    "Launch Card Testing Automated Script Attack": "A bot fires 5 tiny payments on one card within a minute to see if a stolen card works.",
    "Account Takeover (new device + payee change)": "A criminal logs in from a new device, adds a new payee minutes ago and sends a big amount.",
    "APP Scam (trusted device, big transfer to new payee)": "The real customer, tricked by a scammer, sends a large amount to a brand-new payee.",
    "Card-Not-Present Credit Card Fraud": "Stolen card details used online from a foreign IP address, at night, for a high-value order.",
    "Custom transaction": "Edit any value yourself and watch how the decision changes."}

def page_check():
    header("Check a payment", "Pick a scenario, change any value, and see exactly how FraudShield decides - and why.")
    L, Rr = st.columns([1, 1.1])
    with L:
        with card("inputs"):
            ct("💳 Transaction details")
            names = list(SCENARIOS) + ["Custom transaction"]
            scen = st.selectbox("Ready-made scenario", names, help="Pick an example. You can still edit every value below.")
            st.markdown(f'<div class="ex">{SCEN_INFO[scen]}</div>', unsafe_allow_html=True)
            base = SCENARIOS[scen] if scen in SCENARIOS else SCENARIOS["Normal everyday purchase"]; k = lambda f: f"{f}|{scen}"
            a, b = st.columns(2)
            amount = a.number_input("Payment amount (Rs)", min_value=-1000.0, value=float(base["amount"]), key=k("amount"), help="Must be above 0 - try a negative value to see validation work.")
            velocity = b.number_input("Payments on this card in last 60 s", value=int(base["velocity_1m"]), step=1, key=k("vel"), help="3+ tiny payments in a minute is a classic bot pattern.")
            payee = a.number_input("Hours since payee was changed", min_value=-1.0, value=float(base["payee_changed_hours"]), key=k("payee"), help="A very recent change followed by a big payment is suspicious.")
            age = b.number_input("Account age (days)", value=int(base["account_age_days"]), step=1, key=k("age"))
            ip = a.text_input("IP country (2 letters)", base["ip_country"], key=k("ip"), help="e.g. IN, US, GB. The customer's home country is IN.")
            new_dev = b.checkbox("From a new / unrecognised device", base["is_new_device"], key=k("nd"))
            with st.expander("More fields (IDs, device, customer's usual spend)"):
                tid = st.text_input("Transaction ID", base["transaction_id"], key=k("tid")); uid = st.text_input("User ID", base["user_id"], key=k("uid"))
                cid = st.text_input("Card ID", base["card_id"], key=k("cid")); dev = st.text_input("Device ID (hex)", base["device_id"], key=k("dev"))
                avg = st.number_input("Customer's usual payment (Rs)", value=float(base["user_avg_amount"]), key=k("avg")); hour = st.number_input("Hour of day (0-23)", value=int(base["hour"]), step=1, key=k("hour"))
            lo_t, hi_t = threshold_control("c_thr")
            if st.button("Analyze transaction", type="primary", key="analyze"):
                payload = dict(transaction_id=tid, user_id=uid, card_id=cid, amount=amount, device_id=dev, ip_country=ip, velocity_1m=int(velocity), account_age_days=int(age),
                               payee_changed_hours=payee, is_new_device=new_dev, user_avg_amount=avg, hour=int(hour))
                res = engine.score(payload, lo_t, hi_t); ss["result"], ss["payload"], ss["rthr"] = res, payload, (lo_t, hi_t)
                if res["valid"]: ss["feed"] = (ss["feed"] + [make_event(payload, "(manual check)", res, time.time())])[-600:]
    res, p = ss["result"], ss["payload"]
    with Rr:
        with card("result"):
            ct("✨ AI analysis results")
            if res is None:
                st.markdown('<div class="ex">👈 Choose a scenario and press <b>Analyze transaction</b>. The decision, the reasons and the recommended action will appear here.</div>', unsafe_allow_html=True)
            elif not res["valid"]:
                st.error("This payment was rejected before scoring because some fields are invalid:")
                for e in res["errors"]: st.write("• " + e)
                st.caption("Validation protects the engine from bad data. Fix the fields and run again.")
            else:
                bg, fg = ROUTE[res["route"]]; pr = max(res["probabilities"].values()) * 100
                st.markdown(f'<div class="banner" style="background:{bg};color:{fg}"><div><div class="k">Risk assessment</div><div class="t">{WORD[res["route"]]}</div></div><div class="t">{ICON[res["route"]]}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tile"><b>Fraud probability</b><div class="bar"><div style="width:{res["risk_score"]:.1f}%;background:{bg}"></div></div><div class="big">{res["risk_score"]:.1f}%</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tile" style="margin-top:12px"><b>Model insights</b><div class="mi" style="margin-top:10px"><div><div class="l">Confidence</div><div class="v">{pr:.1f}%</div></div><div><div class="l">Processing time</div><div class="v">{res["latency_ms"]} ms</div></div>'
                            f'<div><div class="l">Predicted class</div><div class="v">{res["predicted_class"]}</div></div><div><div class="l">Status</div><div class="v">{STATUS[res["route"]]}</div></div></div></div>', unsafe_allow_html=True)
                why = reasons(res, p)
                st.markdown('<div class="tile" style="margin-top:12px"><b>AI explanation</b>' + f'<div class="ex">{md2html(summary(res, p))}</div>' + "".join(f'<div class="ex">• {html.escape(w)}</div>' for w in why[:4]) + "</div>", unsafe_allow_html=True)
                st.download_button("⬇ Download result (JSON)", json.dumps(res, indent=2, default=str), "fraudshield_result.json", "application/json", key="dl_res")
    if res is not None and res["valid"]:
        lo, hi = ss.get("rthr", (ALLOW_BELOW, BLOCK_ABOVE)); col = ROUTE[res["route"]][0]
        a, b = st.columns(2)
        with a:
            with card("steps"):
                ct("How we got here", "What each stage of the pipeline did")
                st.markdown("".join(f'<div class="step {"flag" if fl else ""}">{ic} <b>{ti}</b><br><span class="muted">{md2html(de)}</span></div>' for ic, ti, de, fl in pipeline_steps(res, p, lo, hi)), unsafe_allow_html=True)
        with b:
            with card("drivers"):
                ct("What pushed the risk up?", "Share of the risk push, %")
                if not res["explain_ok"]: st.warning("The explanation module failed, so the decision used rules and the AI only (the system keeps working even if explanations fail).")
                elif res["drivers"]:
                    d = res["drivers"][::-1]
                    f2 = go.Figure(go.Bar(x=[x["impact"] for x in d], y=[x["label"] for x in d], orientation="h", marker_color=ROUTE["HARD BLOCK"][0]))
                    f2.update_layout(**plot_layout(MODE, 230)); f2.update_xaxes(gridcolor=T["border"]); st.plotly_chart(f2, key="chk_drv", config=CFG)
                else: st.markdown('<span class="muted">Nothing pushed the risk up - a normal payment.</span>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            with card("conf"):
                ct("AI confidence per outcome", "Chance of each class, %")
                prb = res["probabilities"]; nm = list(prb)[::-1]
                f3 = go.Figure(go.Bar(x=[prb[n] * 100 for n in nm], y=nm, orientation="h", marker_color=[T["accent"] if n == res["predicted_class"] else T["border"] for n in nm]))
                f3.update_layout(**plot_layout(MODE, 230)); f3.update_xaxes(range=[0, 100], gridcolor=T["border"]); st.plotly_chart(f3, key="chk_conf", config=CFG)
        with c2:
            with card("action"):
                ct("What should the team do?")
                st.markdown(f'<div class="ex" style="border-left-color:{col}">{res["mitigation"] if res["route"] != "ALLOW" else "Nothing - the payment goes through with no extra steps."}</div>', unsafe_allow_html=True)
                st.caption(f"Decided in {res['latency_ms']} ms (budget {LATENCY_BUDGET_MS} ms).")

def feed_card(e):
    bg, fg = ROUTE[e["route"]]; why = ("; ".join(e["why"]) or "")[:110]
    return (f'<div class="fc" style="border-left-color:{bg}"><div class="h"><span>{e["txn"]}</span><span class="pill" style="background:{rgba(bg, .22)};color:{bg}">{e["risk"]:.1f}% Risk</span></div>'
            f'<div class="g"><div><span class="l">User</span><span class="v">{e["user"]}</span></div><div><span class="l">Amount</span><span class="v">{inr(e["amount"])}</span></div><div><span class="l">Decision</span><span class="v">{STATUS[e["route"]]}</span></div>'
            f'<div><span class="l">Predicted</span><span class="v">{e["pred"]}</span></div><div><span class="l">Actual (hidden)</span><span class="v">{html.escape(e["truth"])}</span></div><div><span class="l">Time</span><span class="v">{e["time"]}</span></div></div>'
            + (f'<div class="muted" style="font-size:.78rem;margin-top:8px">Why: {html.escape(why)}</div>' if why and e["route"] != "ALLOW" else "") + "</div>")

def page_live():
    header("Live payment feed", "A simulator plays the payment gateway; every payment is scored the moment it arrives.")
    L, Rr = st.columns([1, 1.35])
    with L:
        with card("sim"):
            ct("⚙️ Transaction simulator")
            st.button("Live stream: ON" if ss["stream_on"] else "Live stream: OFF", key="stream_btn", on_click=lambda: ss.update(stream_on=not ss["stream_on"]), help="Start / pause the simulated feed.")
            st.markdown('<span class="live" style="background:#EF4444;color:#fff">● LIVE</span> payments are arriving…' if ss["stream_on"] else '<span class="live" style="background:var(--surface2);color:var(--muted)">⏸ PAUSED</span> press the switch above to start', unsafe_allow_html=True)
            st.markdown('<p class="rl">Simulator settings</p>', unsafe_allow_html=True)
            ss["_secs"] = st.slider("Speed: seconds between payments (0.5 = fast, 3 = slow)", 0.5, 3.0, float(ss["_secs"]), 0.5, key="w_secs", help="How often a new payment arrives while the Live stream is ON.")
            ss["_atk"] = st.slider("Fraud attacks: % of the stream (0 = none, 50 = half)", 0, 50, int(ss["_atk"]), key="w_atk", help="How often the simulator starts a fraud attack instead of a normal payment.")
            threshold_control("w_thr")
            b1, b2 = st.columns(2)
            if b1.button("⚡ Simulate fraud", key="simfraud", help="Inject one attack right now."): inject_attack()
            if b2.button("🗑 Clear all", key="clearall"): ss["feed"] = []; ss["sim"] = None
        with st.expander("ℹ️ What am I looking at?"):
            st.markdown("- Each card is one payment. **Actual** is what the simulator really made it (the engine never sees this); **Predicted** is what FraudShield thinks.\n"
                        "- Card colour = decision: green Allowed, amber Challenged, red Blocked. A pop-up appears for every block.\n"
                        "- Card-testing bursts are usually only caught from the 3rd payment, because the rule needs 3 tiny payments in a minute. That is a real limit of rule-based detection.")
    with Rr:
        with card("feed"):
            ct("📡 Live transaction feed")
            flt = st.radio("Filter", ["All", "Flagged", "Allowed"], horizontal=True, label_visibility="collapsed", key="w_flt")
            def body():
                tick(); ev = ss["feed"]
                if not ev: st.markdown('<div class="ex">No payments yet. Press the <b>Live stream</b> switch or <b>Simulate fraud</b>.</div>', unsafe_allow_html=True); return
                att = [e for e in ev if e["truth"] not in ("Legitimate", "(manual check)")]; good = [e for e in ev if e["truth"] == "Legitimate"]
                caught = sum(e["route"] != "ALLOW" for e in att); fa = sum(e["route"] != "ALLOW" for e in good)
                st.markdown(kpis([("Checked", f"{len(ev):,}", "", ""), ("Alerts", f"{sum(e['route'] != 'ALLOW' for e in ev):,}", "challenged or blocked", ""), ("Fraud flagged", f"{caught}/{len(att)}", "real attacks caught", "up"), ("Good flagged", f"{fa}/{len(good)}", "false alarms", "down" if fa else "")]), unsafe_allow_html=True)
                last = ev[-1]
                if last["route"] != "ALLOW":
                    bg, fg = ROUTE[last["route"]]
                    st.markdown(f'<div class="banner blink" style="background:{bg};color:{fg}"><div><div class="k">Latest alert · {last["time"]}</div><div class="t" style="font-size:1.15rem">{STATUS[last["route"]].upper()}: {last["txn"]} · {last["pred"]} · risk {last["risk"]:.0f}</div></div></div>', unsafe_allow_html=True)
                shown = [e for e in reversed(ev) if flt == "All" or (flt == "Flagged" and e["route"] != "ALLOW") or (flt == "Allowed" and e["route"] == "ALLOW")][:14]
                st.markdown('<div class="feedwrap">' + "".join(feed_card(e) for e in shown) + "</div>", unsafe_allow_html=True)
            st.fragment(run_every=(ss["_secs"] if ss["stream_on"] else None))(body)()

def short(i): return i[:4] + "…" + i[-4:]

def page_map():
    header("Connections map", "Who shares a device with whom. A device used by many customers or cards is a classic sign of a bot or fraud ring.")
    G = engine.graph.G
    sus = [(n[1], sum(1 for m in G.neighbors(n) if m[0] == "user"), sum(1 for m in G.neighbors(n) if m[0] == "card")) for n in G if n[0] == "device"]
    sus = sorted(sus, key=lambda r: -(r[1] + r[2]))[:15]
    options = {f"{d[:8]}…  ({u} customers, {c} cards)": d for d, u, c in sus}
    if ss["payload"]: options = {f"Device from your last check ({ss['payload']['device_id'][:8]}…)": ss["payload"]["device_id"], **options}
    pick = st.selectbox("Choose a device to inspect", list(options), help="The list shows the most widely shared devices first.")
    dev = options[pick]; centre = ("device", dev)
    users = sorted(m[1] for m in G.neighbors(centre) if m[0] == "user") if centre in G else []
    cards = sorted(m[1] for m in G.neighbors(centre) if m[0] == "card") if centre in G else []
    bad = len(users) >= 3 or len(cards) >= 3
    L, Rr = st.columns([1.7, 1])
    with L:
        with card("graph"):
            ct("Device network", "Green = customers, grey = cards, large circle = the device (red when suspicious)")
            if centre not in G:
                st.markdown('<div class="ex">This device has never been seen before, so it has no connections yet - being brand new is itself a mild warning sign.</div>', unsafe_allow_html=True)
            else:
                U, C = users[:60], cards[:40]; pos = {centre: (0.0, 0.0)}
                for i, u in enumerate(U): a_ = 2 * math.pi * i / max(len(U), 1); pos[("user", u)] = (math.cos(a_), math.sin(a_))
                for j, c_ in enumerate(C): a_ = 2 * math.pi * (j + .5) / max(len(C), 1); pos[("card", c_)] = (1.7 * math.cos(a_), 1.7 * math.sin(a_))
                ex, ey = [], []
                for u_, v_ in G.subgraph(list(pos)).edges(): ex += [pos[u_][0], pos[v_][0], None]; ey += [pos[u_][1], pos[v_][1], None]
                fig = go.Figure(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=T["accent2"], width=1), hoverinfo="none", showlegend=False))
                lab = len(U) + len(C) <= 45
                for kind, col, ids, nm in (("user", T["accent"], U, "Customer"), ("card", T["muted"], C, "Card")):
                    fig.add_trace(go.Scatter(x=[pos[(kind, i)][0] for i in ids], y=[pos[(kind, i)][1] for i in ids], mode="markers+text" if lab else "markers", name=nm, text=[short(i) for i in ids],
                                             textposition="bottom center", textfont=dict(size=9, color=T["text"]), marker=dict(size=20 if kind == "user" else 14, color=col), hovertext=ids))
                fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", name="Device", text=["DEVICE"], textfont=dict(size=10, color="#FFFFFF"), marker=dict(size=70, color="#EF4444" if bad else T["accent"]), hovertext=[dev]))
                fig.update_layout(**plot_layout(MODE, 560, margin=dict(t=10, b=10, l=10, r=10))); fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x")
                st.plotly_chart(fig, key="map_fig", config=CFG)
    with Rr:
        with card("nodes"):
            ct("Node details")
            tone = "#EF4444" if bad else T["accent"]
            st.markdown(f'<div class="tile" style="border-left:5px solid {tone}"><b>{"⚠️ Suspicious device" if bad else "✅ Looks normal"}</b><br><span class="muted">Device ID</span> <code>{dev}</code>'
                        f'<div class="mi" style="margin-top:8px"><div><div class="l">Customers</div><div class="v">{len(users)}</div></div><div><div class="l">Cards</div><div class="v">{len(cards)}</div></div></div></div>', unsafe_allow_html=True)
            t1, t2, t3 = st.tabs([f"Customers ({len(users)})", f"Cards ({len(cards)})", "Signals"])
            with t1: st.markdown("".join(f'<div class="cat"><span>👤 {u}</span></div>' for u in users[:25]) or '<span class="muted">None</span>', unsafe_allow_html=True)
            with t2: st.markdown("".join(f'<div class="cat"><span>💳 {c_}</span></div>' for c_ in cards[:25]) or '<span class="muted">None</span>', unsafe_allow_html=True)
            with t3:
                sig = []
                if len(users) >= 3: sig.append(("#EF4444", "More than two customers use this device", f"{len(users)} different customers"))
                if len(cards) >= 3: sig.append(("#EF4444", "Many cards used on one device", f"{len(cards)} different cards"))
                if not sig: sig.append((T["accent"], "No sharing pattern", "One device, few customers - what we expect"))
                for e in [e for e in ss["feed"] if e["device"] == dev][-5:]: sig.append((ROUTE[e["route"]][0], f"Payment {e['txn']} was {STATUS[e['route']].lower()}", f"{e['pred']} · risk {e['risk']:.0f} · {e['time']}"))
                st.markdown("".join(f'<div class="sig"><i style="background:{c_}"></i><div><b>{html.escape(t_)}</b><span>{html.escape(d_)}</span></div></div>' for c_, t_, d_ in sig), unsafe_allow_html=True)

def page_start():
    header("Start here", "A two-minute guide to what FraudShield does and how to read it.")
    st.markdown('<div class="hero"><h2>What does FraudShield do?</h2><p>When a payment arrives, FraudShield looks at who is paying, from which device, how much and how fast - and within a fraction of a second decides what to do with it. Try it in <b>Check a payment</b>, or watch it work on its own in <b>Live feed</b>.</p></div>', unsafe_allow_html=True)
    with card("dec3"):
        ct("The 3 possible decisions")
        st.markdown('<div class="grid">' + "".join(f'<div class="tile" style="border-top:5px solid {ROUTE[r][0]}"><b>{t}</b><br><span class="muted">{ROUTE_EXPLAIN[r]}</span></div>' for r, t in [("ALLOW", "Allow"), ("CHALLENGE", "Challenge"), ("HARD BLOCK", "Block")]) + "</div>", unsafe_allow_html=True)
    with card("steps5"):
        ct("How a payment is checked (5 steps, ~10 milliseconds)")
        steps = [("Check the data", "Is the payment information complete and valid?"), ("Safety rules", "Instant yes/no rules, e.g. 3+ tiny payments in a minute."), ("Connection check", "Is one device or card linked to many customers?"), ("AI model", "Estimates the chance of each type of fraud."), ("Decision", "Allow, Challenge or Block - with reasons you can read.")]
        st.markdown('<div class="grid">' + "".join(f'<div class="tile"><span class="num">{i}</span><b>{t}</b><br><span class="muted">{d}</span></div>' for i, (t, d) in enumerate(steps, 1)) + "</div>", unsafe_allow_html=True)
    with card("types4"):
        ct("The 4 kinds of fraud it recognises")
        fr = [("Card Testing", "🤖"), ("Account Takeover", "🔑"), ("APP Scam", "🎭"), ("Credit Card Fraud", "💳")]
        st.markdown('<div class="grid">' + "".join(f'<div class="tile"><b>{ic} {n}</b><br><span class="muted">{CLASS_EXPLAIN[n][0].upper() + CLASS_EXPLAIN[n][1:]}.</span></div>' for n, ic in fr) + "</div>", unsafe_allow_html=True)
    with card("try3"):
        ct("Try it in 3 steps")
        st.markdown("1. Open **⚡ Check a payment** and choose a ready-made scenario.\n2. Press **Analyze transaction**.\n3. Read the explanation and the *How we got here* steps. Then change some values and run it again to see what changes the decision.")
    with st.expander("📘 Glossary - words used in this app"):
        gl = {"Risk score": "0-100. How suspicious the payment looks. Higher = more suspicious.", "Threshold": "The score cut-offs that turn a risk score into a decision. You can move them with the slider.",
              "Challenge (OTP / 3-D Secure)": "Asking the customer to confirm with a one-time code or their bank app.", "Velocity": "How many payments happened on the same card in a short time.",
              "Payee / beneficiary": "The person or account receiving the money.", "Chargeback": "When a customer disputes a payment and the money is taken back from the merchant, often with a fee.",
              "False positive": "A good customer wrongly flagged as a fraudster. It costs sales and trust.", "Macro-F1": "An accuracy score (0-1) that treats every fraud type equally, even rare ones."}
        for k_, v_ in gl.items(): st.markdown(f"**{k_}** - {v_}")

top_nav()
{"dashboard": page_dashboard, "check": page_check, "live": page_live, "map": page_map, "start": page_start}[ss["page"]]()


# import os, json, time, html, re, math
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

# import pandas as pd, networkx as nx, plotly.graph_objects as go, streamlit as st
# import streamlit.components.v1 as components
# from core.config import *
# from core.scenarios import SCENARIOS
# from core.roi_calc import compute_roi
# from core.stream_sim import StreamSimulator
# from core.theme import THEMES, ROUTE, css, plot_layout
# from core.narrative import summary, pipeline_steps, reasons, CLASS_EXPLAIN, ROUTE_EXPLAIN

# st.set_page_config(page_title="FraudShield 2.0", page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
# ss = st.session_state
# for _k, _v in dict(page="dashboard", dark=True, result=None, payload=None, stream_on=False, sim=None, _thr=(ALLOW_BELOW, BLOCK_ABOVE), _secs=1.0, _atk=15).items():
#     ss.setdefault(_k, _v)
# MODE = "dark" if ss["dark"] else "light"; T = THEMES[MODE]

# # ------------------------------------------------------------------ styling
# st.markdown(css(MODE, ss["stream_on"], ss["page"]), unsafe_allow_html=True)
# _raw = css(MODE, ss["stream_on"], ss["page"]).replace("<style>", "").replace("</style>", "")
# components.html("<script>const d=window.parent.document;let e=d.getElementById('fs-theme');"
#                 "if(!e){e=d.createElement('style');e.id='fs-theme';d.head.appendChild(e);}"
#                 f"e.textContent={json.dumps(_raw)};</script>", height=0)

# # ------------------------------------------------------------------ helpers
# def inr(x):
#     s = str(int(round(abs(x)))); head, tail = s[:-3], s[-3:]
#     if head:
#         parts = []
#         while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
#         if head: parts.insert(0, head)
#         s = ",".join(parts) + "," + tail
#     return ("-" if x < 0 else "") + "Rs " + s

# def rgba(hex_, a):
#     h = hex_.lstrip("#"); return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

# def md2html(s): return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

# def card(key):
#     """A keyed container styled as a rounded card (plain container on older Streamlit)."""
#     try: return st.container(key="card_" + key)
#     except TypeError: return st.container()

# def header(title, sub):
#     st.markdown(f'<p class="pt">{title}</p><p class="ps">{sub}</p>', unsafe_allow_html=True)

# def ct(title, sub=None):
#     st.markdown(f'<p class="ct">{title}</p>' + (f'<p class="cs">{sub}</p>' if sub else ""), unsafe_allow_html=True)

# def kpis(items):
#     return '<div class="kpis">' + "".join(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="s {c}">{s}</div></div>' for l, v, s, c in items) + "</div>"

# def pill(route, text):
#     bg, fg = ROUTE[route]; return f'<span class="pill" style="background:{bg};color:{fg}">{html.escape(text)}</span>'

# def html_table(rows, cols, bg=None):
#     head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
#     body = "".join((f'<tr style="background:{bg(r)}">' if bg else "<tr>") + "".join(f"<td>{html.escape(str(r.get(c, '')))}</td>" for c in cols) + "</tr>" for r in rows)
#     return f'<div style="overflow-x:auto"><table class="feed"><tr>{head}</tr>{body}</table></div>'

# WORD = {"ALLOW": "LOW RISK", "CHALLENGE": "MEDIUM RISK", "HARD BLOCK": "HIGH RISK"}
# ICON = {"ALLOW": "✔", "CHALLENGE": "!", "HARD BLOCK": "⛔"}
# STATUS = {"ALLOW": "Allowed", "CHALLENGE": "Challenged", "HARD BLOCK": "Blocked"}

# @st.cache_resource(show_spinner="Loading engine (first run trains the model, ~30 s)...")
# def load_engine():
#     if not os.path.exists(MODEL_PATH):
#         from core.data_gen import generate; import train_pipeline
#         generate(); train_pipeline.main()
#     from core.model_wrapper import FraudShieldEngine
#     return FraudShieldEngine()

# engine = load_engine()
# metrics = json.load(open(METRICS_PATH)) if os.path.exists(METRICS_PATH) else {}

# def make_event(p, truth, res, ts):
#     return dict(ts=ts, time=time.strftime("%H:%M:%S", time.localtime(ts)), txn=p["transaction_id"], user=p["user_id"], device=p["device_id"], amount=float(p["amount"]),
#                 truth=truth, pred=res["predicted_class"], risk=float(res["risk_score"]), route=res["route"], lat=float(res["latency_ms"]),
#                 why=reasons(res, p)[:3], fix=res["mitigation"])

# @st.cache_data(show_spinner="Preparing demo data (scoring 240 simulated payments)...")
# def seed_events():
#     sim = StreamSimulator(seed=7, attack_prob=0.15); out = []; now = time.time()
#     for i in range(240):
#         p, truth = sim.next(); res = engine.score(p)
#         if res["valid"]: out.append(make_event(p, truth, res, now - (240 - i) * 2))
#     return out

# if "feed" not in ss: ss["feed"] = list(seed_events())

# def add_event(p, truth):
#     lo, hi = ss["_thr"]; res = engine.score(p, lo, hi)
#     if res["valid"]:
#         ss["feed"] = (ss["feed"] + [make_event(p, truth, res, time.time())])[-600:]
#         if res["route"] == "HARD BLOCK": st.toast(f"BLOCKED {p['transaction_id']} - {res['predicted_class']} (risk {res['risk_score']})", icon="🚨")

# def tick():
#     """Advance the simulated stream by one payment (only when the Live stream switch is ON)."""
#     if not ss["stream_on"]: return
#     if ss["sim"] is None: ss["sim"] = StreamSimulator()
#     ss["sim"].attack_prob = ss["_atk"] / 100
#     p, truth = ss["sim"].next(); add_event(p, truth)

# def inject_attack():
#     if ss["sim"] is None: ss["sim"] = StreamSimulator()
#     ss["sim"]._start_attack()
#     while ss["sim"].queue:
#         p, truth = ss["sim"].queue.popleft(); add_event(p, truth)

# def fig_area(vals, lo, hi):
#     fig = go.Figure(go.Scatter(y=vals, mode="lines", line=dict(color=T["accent"], width=2), fill="tozeroy", fillcolor=rgba(T["accent"], .16)))
#     fig.add_hline(y=lo, line_dash="dash", line_color=ROUTE["CHALLENGE"][0]); fig.add_hline(y=hi, line_dash="dash", line_color=ROUTE["HARD BLOCK"][0])
#     fig.update_layout(**plot_layout(MODE, 250, margin=dict(t=10, b=10, l=10, r=10))); fig.update_yaxes(range=[0, 100], gridcolor=T["border"]); fig.update_xaxes(visible=False)
#     return fig

# def fig_bars(labels, values, colors, height=250):
#     fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, text=values, textposition="outside"))
#     fig.update_layout(**plot_layout(MODE, height, margin=dict(t=20, b=10, l=10, r=10))); fig.update_yaxes(gridcolor=T["border"]); return fig

# CFG = {"displayModeBar": False}

# # ------------------------------------------------------------------ sidebar
# NAV = [("dashboard", "📊", "Dashboard", "MAIN"), ("check", "⚡", "Check a payment", None), ("live", "📡", "Live feed", None),
#        ("map", "🕸️", "Connections map", "ANALYTICS"), ("roi", "💰", "Money saved", None), ("start", "🏠", "Start here", "HELP")]
# with st.sidebar:
#     st.markdown(f'<p class="brand">{APP_ICON} FraudShield 2.0</p><p class="brand-sub">Real-time, explainable fraud decisions</p>', unsafe_allow_html=True)
#     for key, icon, label, sec in NAV:
#         if sec: st.markdown(f'<div class="navlabel">{sec}</div>', unsafe_allow_html=True)
#         st.button(f"{icon}  {label}", key=f"nav_{key}", on_click=lambda k=key: ss.update(page=k))
#     st.markdown('<div class="navlabel">APPEARANCE</div>', unsafe_allow_html=True)
#     st.button("🌙 Dark mode" if ss["dark"] else "☀️ Light mode", key="theme_btn", on_click=lambda: ss.update(dark=not ss["dark"]), help="Switch between dark and light mode.")
#     ev_ = ss["feed"]; avg_ = sum(e["lat"] for e in ev_) / max(len(ev_), 1)
#     st.markdown(f'<div class="sidecard"><b>Engine status</b><br>Model: gradient-boosted trees<br>Accuracy (macro-F1): <b>{metrics.get("macro_f1", 0) * 100:.1f}%</b><br>Avg decision time: <b>{avg_:.1f} ms</b><br>Payments checked: <b>{len(ev_):,}</b></div>', unsafe_allow_html=True)

# # ================================================================== PAGES
# def page_dashboard():
#     header("Fraud detection overview", "What the engine has seen and decided. Payments are simulated; every decision is made by the real engine.")
#     def body():
#         tick()
#         ev = ss["feed"]; n = max(len(ev), 1); lo, hi = ss["_thr"]
#         alerts = [e for e in ev if e["route"] != "ALLOW"]; blocks = [e for e in ev if e["route"] == "HARD BLOCK"]; avg = sum(e["lat"] for e in ev) / n
#         main, side = st.columns([3, 1.25])
#         with main:
#             st.markdown(kpis([("Payments checked", f"{len(ev):,}", "simulated + live", ""), ("Alerts raised", f"{len(alerts):,}", f"{len(alerts) / n * 100:.1f}% challenged or blocked", ""),
#                               ("Hard blocks", f"{len(blocks):,}", f"{len(blocks) / n * 100:.1f}% of payments", "down" if blocks else ""), ("Avg decision time", f"{avg:.1f} ms", "budget: 100 ms", "up")]), unsafe_allow_html=True)
#             a, b = st.columns(2)
#             with a:
#                 with card("risk"):
#                     ct("Risk score over time", "Last 80 payments; dashed lines are your thresholds"); st.plotly_chart(fig_area([e["risk"] for e in ev[-80:]], lo, hi), key="dash_area", config=CFG)
#             with b:
#                 with card("dec"):
#                     ct("Decisions by type", "How every payment was routed")
#                     cnt = [sum(e["route"] == r for e in ev) for r in ("ALLOW", "CHALLENGE", "HARD BLOCK")]
#                     st.plotly_chart(fig_bars(["Allowed", "Challenged", "Blocked"], cnt, [ROUTE[r][0] for r in ("ALLOW", "CHALLENGE", "HARD BLOCK")]), key="dash_bar", config=CFG)
#             with card("recent"):
#                 ct("Recent decisions (audit log)", "Latest 8 payments")
#                 rows = [{"Time": e["time"], "Payment": e["txn"], "Amount": inr(e["amount"]), "Predicted": e["pred"], "Risk": f"{e['risk']:.0f}", "Decision": STATUS[e["route"]]} for e in reversed(ev[-8:])]
#                 st.markdown(html_table(rows, list(rows[0]), bg=lambda r: rgba(ROUTE[{v: k for k, v in STATUS.items()}[r["Decision"]]][0], .14)) if rows else "No payments yet.", unsafe_allow_html=True)
#         with side:
#             with card("cats"):
#                 ct("Fraud types detected", "By the AI model")
#                 for name, col in (("Credit Card Fraud", "#EF4444"), ("Account Takeover", "#F59E0B"), ("APP Scam", T["accent2"]), ("Card Testing", T["accent"])):
#                     k_ = sum(e["pred"] == name for e in ev)
#                     st.markdown(f'<div class="cat"><span><span style="color:{col}">●</span>&nbsp; {name}</span><b>{k_}</b></div>', unsafe_allow_html=True)
#             with card("alerts"):
#                 ct("Latest alerts", "Newest first")
#                 last = [e for e in ev if e["route"] != "ALLOW"][-4:][::-1]
#                 st.markdown("".join(f'<div class="ar"><b>{e["pred"]} - {STATUS[e["route"]]}</b><span>{html.escape(("; ".join(e["why"]) or "-")[:120])}</span><br><em>{e["time"]} · {e["txn"]} · {inr(e["amount"])}</em></div>' for e in last) or '<span class="muted">No alerts yet.</span>', unsafe_allow_html=True)
#             st.download_button("⬇ Download audit CSV", pd.DataFrame([{k: v for k, v in e.items() if k not in ("why", "fix", "ts")} for e in ev]).to_csv(index=False), "audit_log.csv", "text/csv", key="dl_audit")
#     st.fragment(run_every=(ss["_secs"] if ss["stream_on"] else None))(body)()

# SCEN_INFO = {
#     "Normal everyday purchase": "A regular customer buys something at a normal amount from their usual device.",
#     "Launch Card Testing Automated Script Attack": "A bot fires 5 tiny payments on one card within a minute to see if a stolen card works.",
#     "Account Takeover (new device + payee change)": "A criminal logs in from a new device, adds a new payee minutes ago and sends a big amount.",
#     "APP Scam (trusted device, big transfer to new payee)": "The real customer, tricked by a scammer, sends a large amount to a brand-new payee.",
#     "Card-Not-Present Credit Card Fraud": "Stolen card details used online from a foreign IP address, at night, for a high-value order.",
#     "Custom transaction": "Edit any value yourself and watch how the decision changes."}

# def page_check():
#     header("Check a payment", "Pick a scenario, change any value, and see exactly how FraudShield decides - and why.")
#     L, Rr = st.columns([1, 1.1])
#     with L:
#         with card("inputs"):
#             ct("💳 Transaction details")
#             names = list(SCENARIOS) + ["Custom transaction"]
#             scen = st.selectbox("Ready-made scenario", names, help="Pick an example. You can still edit every value below.")
#             st.markdown(f'<div class="ex">{SCEN_INFO[scen]}</div>', unsafe_allow_html=True)
#             base = SCENARIOS[scen] if scen in SCENARIOS else SCENARIOS["Normal everyday purchase"]; k = lambda f: f"{f}|{scen}"
#             a, b = st.columns(2)
#             amount = a.number_input("Payment amount (Rs)", min_value=-1000.0, value=float(base["amount"]), key=k("amount"), help="Must be above 0 - try a negative value to see validation work.")
#             velocity = b.number_input("Payments on this card in last 60 s", value=int(base["velocity_1m"]), step=1, key=k("vel"), help="3+ tiny payments in a minute is a classic bot pattern.")
#             payee = a.number_input("Hours since payee was changed", min_value=-1.0, value=float(base["payee_changed_hours"]), key=k("payee"), help="A very recent change followed by a big payment is suspicious.")
#             age = b.number_input("Account age (days)", value=int(base["account_age_days"]), step=1, key=k("age"))
#             ip = a.text_input("IP country (2 letters)", base["ip_country"], key=k("ip"), help="e.g. IN, US, GB. The customer's home country is IN.")
#             new_dev = b.checkbox("From a new / unrecognised device", base["is_new_device"], key=k("nd"))
#             with st.expander("More fields (IDs, device, customer's usual spend)"):
#                 tid = st.text_input("Transaction ID", base["transaction_id"], key=k("tid")); uid = st.text_input("User ID", base["user_id"], key=k("uid"))
#                 cid = st.text_input("Card ID", base["card_id"], key=k("cid")); dev = st.text_input("Device ID (hex)", base["device_id"], key=k("dev"))
#                 avg = st.number_input("Customer's usual payment (Rs)", value=float(base["user_avg_amount"]), key=k("avg")); hour = st.number_input("Hour of day (0-23)", value=int(base["hour"]), step=1, key=k("hour"))
#             lo_t, hi_t = st.slider("How strict? Allow below the first number, Block above the second", 0, 100, ss["_thr"], help="Lower numbers = stricter (more challenges, more annoyed customers). Higher = more relaxed (more fraud may slip through).")
#             ss["_thr"] = (lo_t, hi_t)
#             if st.button("Analyze transaction", type="primary", key="analyze"):
#                 payload = dict(transaction_id=tid, user_id=uid, card_id=cid, amount=amount, device_id=dev, ip_country=ip, velocity_1m=int(velocity), account_age_days=int(age),
#                                payee_changed_hours=payee, is_new_device=new_dev, user_avg_amount=avg, hour=int(hour))
#                 res = engine.score(payload, lo_t, hi_t); ss["result"], ss["payload"], ss["rthr"] = res, payload, (lo_t, hi_t)
#                 if res["valid"]: ss["feed"] = (ss["feed"] + [make_event(payload, "(manual check)", res, time.time())])[-600:]
#     res, p = ss["result"], ss["payload"]
#     with Rr:
#         with card("result"):
#             ct("✨ AI analysis results")
#             if res is None:
#                 st.markdown('<div class="ex">👈 Choose a scenario and press <b>Analyze transaction</b>. The decision, the reasons and the recommended action will appear here.</div>', unsafe_allow_html=True)
#             elif not res["valid"]:
#                 st.error("This payment was rejected before scoring because some fields are invalid:")
#                 for e in res["errors"]: st.write("• " + e)
#                 st.caption("Validation protects the engine from bad data. Fix the fields and run again.")
#             else:
#                 bg, fg = ROUTE[res["route"]]; pr = max(res["probabilities"].values()) * 100
#                 st.markdown(f'<div class="banner" style="background:{bg};color:{fg}"><div><div class="k">Risk assessment</div><div class="t">{WORD[res["route"]]}</div></div><div class="t">{ICON[res["route"]]}</div></div>', unsafe_allow_html=True)
#                 st.markdown(f'<div class="tile"><b>Fraud probability</b><div class="bar"><div style="width:{res["risk_score"]:.1f}%;background:{bg}"></div></div><div class="big">{res["risk_score"]:.1f}%</div></div>', unsafe_allow_html=True)
#                 st.markdown(f'<div class="tile" style="margin-top:12px"><b>Model insights</b><div class="mi" style="margin-top:10px"><div><div class="l">Confidence</div><div class="v">{pr:.1f}%</div></div><div><div class="l">Processing time</div><div class="v">{res["latency_ms"]} ms</div></div>'
#                             f'<div><div class="l">Predicted class</div><div class="v">{res["predicted_class"]}</div></div><div><div class="l">Status</div><div class="v">{STATUS[res["route"]]}</div></div></div></div>', unsafe_allow_html=True)
#                 why = reasons(res, p)
#                 st.markdown('<div class="tile" style="margin-top:12px"><b>AI explanation</b>' + f'<div class="ex">{md2html(summary(res, p))}</div>' + "".join(f'<div class="ex">• {html.escape(w)}</div>' for w in why[:4]) + "</div>", unsafe_allow_html=True)
#                 st.download_button("⬇ Download result (JSON)", json.dumps(res, indent=2, default=str), "fraudshield_result.json", "application/json", key="dl_res")
#     if res is not None and res["valid"]:
#         lo, hi = ss.get("rthr", (ALLOW_BELOW, BLOCK_ABOVE)); col = ROUTE[res["route"]][0]
#         a, b = st.columns(2)
#         with a:
#             with card("steps"):
#                 ct("How we got here", "What each stage of the pipeline did")
#                 st.markdown("".join(f'<div class="step {"flag" if fl else ""}">{ic} <b>{ti}</b><br><span class="muted">{md2html(de)}</span></div>' for ic, ti, de, fl in pipeline_steps(res, p, lo, hi)), unsafe_allow_html=True)
#         with b:
#             with card("drivers"):
#                 ct("What pushed the risk up?", "Share of the risk push, %")
#                 if not res["explain_ok"]: st.warning("The explanation module failed, so the decision used rules and the AI only (the system keeps working even if explanations fail).")
#                 elif res["drivers"]:
#                     d = res["drivers"][::-1]
#                     f2 = go.Figure(go.Bar(x=[x["impact"] for x in d], y=[x["label"] for x in d], orientation="h", marker_color=ROUTE["HARD BLOCK"][0]))
#                     f2.update_layout(**plot_layout(MODE, 230)); f2.update_xaxes(gridcolor=T["border"]); st.plotly_chart(f2, key="chk_drv", config=CFG)
#                 else: st.markdown('<span class="muted">Nothing pushed the risk up - a normal payment.</span>', unsafe_allow_html=True)
#         c1, c2 = st.columns(2)
#         with c1:
#             with card("conf"):
#                 ct("AI confidence per outcome", "Chance of each class, %")
#                 prb = res["probabilities"]; nm = list(prb)[::-1]
#                 f3 = go.Figure(go.Bar(x=[prb[n] * 100 for n in nm], y=nm, orientation="h", marker_color=[T["accent"] if n == res["predicted_class"] else T["border"] for n in nm]))
#                 f3.update_layout(**plot_layout(MODE, 230)); f3.update_xaxes(range=[0, 100], gridcolor=T["border"]); st.plotly_chart(f3, key="chk_conf", config=CFG)
#         with c2:
#             with card("action"):
#                 ct("What should the team do?")
#                 st.markdown(f'<div class="ex" style="border-left-color:{col}">{res["mitigation"] if res["route"] != "ALLOW" else "Nothing - the payment goes through with no extra steps."}</div>', unsafe_allow_html=True)
#                 st.caption(f"Decided in {res['latency_ms']} ms (budget {LATENCY_BUDGET_MS} ms).")

# def feed_card(e):
#     bg, fg = ROUTE[e["route"]]; why = ("; ".join(e["why"]) or "")[:110]
#     return (f'<div class="fc" style="border-left-color:{bg}"><div class="h"><span>{e["txn"]}</span><span class="pill" style="background:{rgba(bg, .22)};color:{bg}">{e["risk"]:.1f}% Risk</span></div>'
#             f'<div class="g"><div><span class="l">User</span><span class="v">{e["user"]}</span></div><div><span class="l">Amount</span><span class="v">{inr(e["amount"])}</span></div><div><span class="l">Decision</span><span class="v">{STATUS[e["route"]]}</span></div>'
#             f'<div><span class="l">Predicted</span><span class="v">{e["pred"]}</span></div><div><span class="l">Actual (hidden)</span><span class="v">{html.escape(e["truth"])}</span></div><div><span class="l">Time</span><span class="v">{e["time"]}</span></div></div>'
#             + (f'<div class="muted" style="font-size:.78rem;margin-top:8px">Why: {html.escape(why)}</div>' if why and e["route"] != "ALLOW" else "") + "</div>")

# def page_live():
#     header("Live payment feed", "A simulator plays the payment gateway; every payment is scored the moment it arrives.")
#     L, Rr = st.columns([1, 1.35])
#     with L:
#         with card("sim"):
#             ct("⚙️ Transaction simulator")
#             st.button("Live stream: ON" if ss["stream_on"] else "Live stream: OFF", key="stream_btn", on_click=lambda: ss.update(stream_on=not ss["stream_on"]), help="Start / pause the simulated feed.")
#             st.markdown('<span class="live" style="background:#EF4444;color:#fff">● LIVE</span> payments are arriving…' if ss["stream_on"] else '<span class="live" style="background:var(--surface2);color:var(--muted)">⏸ PAUSED</span> press the switch above to start', unsafe_allow_html=True)
#             ss["_secs"] = st.slider("Seconds per payment", 0.5, 3.0, float(ss["_secs"]), 0.5, key="w_secs", help="How fast new payments arrive.")
#             ss["_atk"] = st.slider("Share of attacks (%)", 0, 50, int(ss["_atk"]), key="w_atk", help="How often the simulator starts a fraud attack.")
#             ss["_thr"] = st.slider("Allow below / Block above", 0, 100, ss["_thr"], key="w_thr", help="Same strictness slider as in Check a payment.")
#             b1, b2 = st.columns(2)
#             if b1.button("⚡ Simulate fraud", key="simfraud", help="Inject one attack right now."): inject_attack()
#             if b2.button("🗑 Clear all", key="clearall"): ss["feed"] = []; ss["sim"] = None
#         with st.expander("ℹ️ What am I looking at?"):
#             st.markdown("- Each card is one payment. **Actual** is what the simulator really made it (the engine never sees this); **Predicted** is what FraudShield thinks.\n"
#                         "- Card colour = decision: green Allowed, amber Challenged, red Blocked. A pop-up appears for every block.\n"
#                         "- Card-testing bursts are usually only caught from the 3rd payment, because the rule needs 3 tiny payments in a minute. That is a real limit of rule-based detection.")
#     with Rr:
#         with card("feed"):
#             ct("📡 Live transaction feed")
#             flt = st.radio("Filter", ["All", "Flagged", "Allowed"], horizontal=True, label_visibility="collapsed", key="w_flt")
#             def body():
#                 tick(); ev = ss["feed"]
#                 if not ev: st.markdown('<div class="ex">No payments yet. Press the <b>Live stream</b> switch or <b>Simulate fraud</b>.</div>', unsafe_allow_html=True); return
#                 att = [e for e in ev if e["truth"] not in ("Legitimate", "(manual check)")]; good = [e for e in ev if e["truth"] == "Legitimate"]
#                 caught = sum(e["route"] != "ALLOW" for e in att); fa = sum(e["route"] != "ALLOW" for e in good)
#                 st.markdown(kpis([("Checked", f"{len(ev):,}", "", ""), ("Alerts", f"{sum(e['route'] != 'ALLOW' for e in ev):,}", "challenged or blocked", ""), ("Fraud flagged", f"{caught}/{len(att)}", "real attacks caught", "up"), ("Good flagged", f"{fa}/{len(good)}", "false alarms", "down" if fa else "")]), unsafe_allow_html=True)
#                 last = ev[-1]
#                 if last["route"] != "ALLOW":
#                     bg, fg = ROUTE[last["route"]]
#                     st.markdown(f'<div class="banner blink" style="background:{bg};color:{fg}"><div><div class="k">Latest alert · {last["time"]}</div><div class="t" style="font-size:1.15rem">{STATUS[last["route"]].upper()}: {last["txn"]} · {last["pred"]} · risk {last["risk"]:.0f}</div></div></div>', unsafe_allow_html=True)
#                 shown = [e for e in reversed(ev) if flt == "All" or (flt == "Flagged" and e["route"] != "ALLOW") or (flt == "Allowed" and e["route"] == "ALLOW")][:14]
#                 st.markdown('<div class="feedwrap">' + "".join(feed_card(e) for e in shown) + "</div>", unsafe_allow_html=True)
#             st.fragment(run_every=(ss["_secs"] if ss["stream_on"] else None))(body)()

# def short(i): return i[:4] + "…" + i[-4:]

# def page_map():
#     header("Connections map", "Who shares a device with whom. A device used by many customers or cards is a classic sign of a bot or fraud ring.")
#     G = engine.graph.G
#     sus = [(n[1], sum(1 for m in G.neighbors(n) if m[0] == "user"), sum(1 for m in G.neighbors(n) if m[0] == "card")) for n in G if n[0] == "device"]
#     sus = sorted(sus, key=lambda r: -(r[1] + r[2]))[:15]
#     options = {f"{d[:8]}…  ({u} customers, {c} cards)": d for d, u, c in sus}
#     if ss["payload"]: options = {f"Device from your last check ({ss['payload']['device_id'][:8]}…)": ss["payload"]["device_id"], **options}
#     pick = st.selectbox("Choose a device to inspect", list(options), help="The list shows the most widely shared devices first.")
#     dev = options[pick]; centre = ("device", dev)
#     users = sorted(m[1] for m in G.neighbors(centre) if m[0] == "user") if centre in G else []
#     cards = sorted(m[1] for m in G.neighbors(centre) if m[0] == "card") if centre in G else []
#     bad = len(users) >= 3 or len(cards) >= 3
#     L, Rr = st.columns([1.7, 1])
#     with L:
#         with card("graph"):
#             ct("Device network", "Green = customers, grey = cards, large circle = the device (red when suspicious)")
#             if centre not in G:
#                 st.markdown('<div class="ex">This device has never been seen before, so it has no connections yet - being brand new is itself a mild warning sign.</div>', unsafe_allow_html=True)
#             else:
#                 U, C = users[:60], cards[:40]; pos = {centre: (0.0, 0.0)}
#                 for i, u in enumerate(U): a_ = 2 * math.pi * i / max(len(U), 1); pos[("user", u)] = (math.cos(a_), math.sin(a_))
#                 for j, c_ in enumerate(C): a_ = 2 * math.pi * (j + .5) / max(len(C), 1); pos[("card", c_)] = (1.7 * math.cos(a_), 1.7 * math.sin(a_))
#                 ex, ey = [], []
#                 for u_, v_ in G.subgraph(list(pos)).edges(): ex += [pos[u_][0], pos[v_][0], None]; ey += [pos[u_][1], pos[v_][1], None]
#                 fig = go.Figure(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=T["accent2"], width=1), hoverinfo="none", showlegend=False))
#                 lab = len(U) + len(C) <= 45
#                 for kind, col, ids, nm in (("user", T["accent"], U, "Customer"), ("card", T["muted"], C, "Card")):
#                     fig.add_trace(go.Scatter(x=[pos[(kind, i)][0] for i in ids], y=[pos[(kind, i)][1] for i in ids], mode="markers+text" if lab else "markers", name=nm, text=[short(i) for i in ids],
#                                              textposition="bottom center", textfont=dict(size=9, color=T["text"]), marker=dict(size=20 if kind == "user" else 14, color=col), hovertext=ids))
#                 fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", name="Device", text=["DEVICE"], textfont=dict(size=10, color="#FFFFFF"), marker=dict(size=70, color="#EF4444" if bad else T["accent"]), hovertext=[dev]))
#                 fig.update_layout(**plot_layout(MODE, 560, margin=dict(t=10, b=10, l=10, r=10))); fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x")
#                 st.plotly_chart(fig, key="map_fig", config=CFG)
#     with Rr:
#         with card("nodes"):
#             ct("Node details")
#             tone = "#EF4444" if bad else T["accent"]
#             st.markdown(f'<div class="tile" style="border-left:5px solid {tone}"><b>{"⚠️ Suspicious device" if bad else "✅ Looks normal"}</b><br><span class="muted">Device ID</span> <code>{dev}</code>'
#                         f'<div class="mi" style="margin-top:8px"><div><div class="l">Customers</div><div class="v">{len(users)}</div></div><div><div class="l">Cards</div><div class="v">{len(cards)}</div></div></div></div>', unsafe_allow_html=True)
#             t1, t2, t3 = st.tabs([f"Customers ({len(users)})", f"Cards ({len(cards)})", "Signals"])
#             with t1: st.markdown("".join(f'<div class="cat"><span>👤 {u}</span></div>' for u in users[:25]) or '<span class="muted">None</span>', unsafe_allow_html=True)
#             with t2: st.markdown("".join(f'<div class="cat"><span>💳 {c_}</span></div>' for c_ in cards[:25]) or '<span class="muted">None</span>', unsafe_allow_html=True)
#             with t3:
#                 sig = []
#                 if len(users) >= 3: sig.append(("#EF4444", "More than two customers use this device", f"{len(users)} different customers"))
#                 if len(cards) >= 3: sig.append(("#EF4444", "Many cards used on one device", f"{len(cards)} different cards"))
#                 if not sig: sig.append((T["accent"], "No sharing pattern", "One device, few customers - what we expect"))
#                 for e in [e for e in ss["feed"] if e["device"] == dev][-5:]: sig.append((ROUTE[e["route"]][0], f"Payment {e['txn']} was {STATUS[e['route']].lower()}", f"{e['pred']} · risk {e['risk']:.0f} · {e['time']}"))
#                 st.markdown("".join(f'<div class="sig"><i style="background:{c_}"></i><div><b>{html.escape(t_)}</b><span>{html.escape(d_)}</span></div></div>' for c_, t_, d_ in sig), unsafe_allow_html=True)

# def page_roi():
#     header("How much money does this save?", "Describe a business, and compare FraudShield with an older, weaker system. All numbers are example assumptions, not real data.")
#     with card("roiin"):
#         ct("Business settings")
#         PRE = {"Mid-size fintech": (50, 1500), "Small online shop": (5, 800), "Large bank / marketplace": (400, 3500)}
#         pre = st.selectbox("Start from an example business", list(PRE), help="Sets the two sliders below. You can still change them.")
#         a, b = st.columns(2)
#         vol_cr = a.slider("Monthly payments processed (Rs crore)", 1, 500, PRE[pre][0], key=f"vol|{pre}", help="1 crore = 10 million rupees.")
#         ticket = b.slider("Average payment size (Rs)", 100, 20000, PRE[pre][1], step=100, key=f"tkt|{pre}")
#         with st.expander("Fraud levels and how good the old system is (optional)", expanded=True):
#             x1, x2, x3 = st.columns(3)
#             fraud_rate = x1.number_input("Share of payments that are fraud (%)", 0.1, 10.0, 2.0, 0.1) / 100
#             legacy_det = x2.number_input("Old system catches (% of fraud)", 0.0, 100.0, 50.0, 1.0) / 100
#             new_det = x3.number_input("FraudShield catches (% of fraud)", 0.0, 100.0, 92.0, 1.0) / 100
#             legacy_fpr = x1.number_input("Old system wrongly flags good customers (%)", 0.0, 20.0, 2.0, 0.1) / 100
#             new_fpr = x2.number_input("FraudShield wrongly flags good customers (%)", 0.0, 20.0, 0.12, 0.01) / 100
#             fee = x3.number_input("Fee per chargeback (Rs)", 0.0, 10000.0, 1250.0, 50.0)
#     r = compute_roi(vol_cr * 1e7, ticket, fraud_rate, legacy_det, new_det, legacy_fpr, new_fpr, chargeback_fee=fee)
#     st.markdown(f'<div class="hero"><h2>About {inr(r["total_monthly_benefit"])} saved every month</h2><p>That is {r["extra_fraud_caught"]:,.0f} extra fraud payments stopped and about {r["false_positives_old"] - r["false_positives_new"]:,.0f} fewer good customers wrongly flagged.</p></div>', unsafe_allow_html=True)
#     st.markdown(kpis([("Stock not lost to fraud", inr(r["inventory_loss_avoided"]), "goods valued at cost", "up"), ("Chargeback fees avoided", inr(r["chargeback_fees_avoided"]), "fees per disputed payment", "up"),
#                       ("Penalty fine avoided", inr(r["monitoring_fine_avoided"]), "card-network monitoring", "up"), ("Happier customers", inr(r["friction_savings"]), "fewer false alarms", "up")]), unsafe_allow_html=True)
#     c1, c2 = st.columns([1.4, 1])
#     with c1:
#         with card("roichart"):
#             ct("Where the monthly saving comes from (Rs)")
#             parts = {"Stock not lost": r["inventory_loss_avoided"], "Chargeback fees": r["chargeback_fees_avoided"], "Penalty fine": r["monitoring_fine_avoided"], "Fewer false alarms": r["friction_savings"]}
#             fig = go.Figure(go.Bar(x=list(parts), y=list(parts.values()), marker_color=[T["accent"], T["accent2"], T["muted"], T["border"]]))
#             fig.update_layout(**plot_layout(MODE, 300)); fig.update_yaxes(gridcolor=T["border"]); st.plotly_chart(fig, key="roi_fig", config=CFG)
#     with c2:
#         with card("roinote"):
#             ct("Chargeback rate")
#             over = r["chargeback_ratio_old_pct"] >= 0.9
#             st.markdown(f'<div class="big">{r["chargeback_ratio_old_pct"]:.2f}% → {r["chargeback_ratio_new_pct"]:.2f}%</div><p class="muted" style="text-align:center">old system → FraudShield</p>'
#                         f'<div class="ex">{"The old rate is above the ~0.9% line where card networks start fining merchants." if over else "The old rate was already below the ~0.9% fine line."}</div>', unsafe_allow_html=True)

# def page_start():
#     header("Start here", "A two-minute guide to what FraudShield does and how to read it.")
#     st.markdown('<div class="hero"><h2>What does FraudShield do?</h2><p>When a payment arrives, FraudShield looks at who is paying, from which device, how much and how fast - and within a fraction of a second decides what to do with it. Try it in <b>Check a payment</b>, or watch it work on its own in <b>Live feed</b>.</p></div>', unsafe_allow_html=True)
#     with card("dec3"):
#         ct("The 3 possible decisions")
#         st.markdown('<div class="grid">' + "".join(f'<div class="tile" style="border-top:5px solid {ROUTE[r][0]}"><b>{t}</b><br><span class="muted">{ROUTE_EXPLAIN[r]}</span></div>' for r, t in [("ALLOW", "Allow"), ("CHALLENGE", "Challenge"), ("HARD BLOCK", "Block")]) + "</div>", unsafe_allow_html=True)
#     with card("steps5"):
#         ct("How a payment is checked (5 steps, ~10 milliseconds)")
#         steps = [("Check the data", "Is the payment information complete and valid?"), ("Safety rules", "Instant yes/no rules, e.g. 3+ tiny payments in a minute."), ("Connection check", "Is one device or card linked to many customers?"), ("AI model", "Estimates the chance of each type of fraud."), ("Decision", "Allow, Challenge or Block - with reasons you can read.")]
#         st.markdown('<div class="grid">' + "".join(f'<div class="tile"><span class="num">{i}</span><b>{t}</b><br><span class="muted">{d}</span></div>' for i, (t, d) in enumerate(steps, 1)) + "</div>", unsafe_allow_html=True)
#     with card("types4"):
#         ct("The 4 kinds of fraud it recognises")
#         fr = [("Card Testing", "🤖"), ("Account Takeover", "🔑"), ("APP Scam", "🎭"), ("Credit Card Fraud", "💳")]
#         st.markdown('<div class="grid">' + "".join(f'<div class="tile"><b>{ic} {n}</b><br><span class="muted">{CLASS_EXPLAIN[n][0].upper() + CLASS_EXPLAIN[n][1:]}.</span></div>' for n, ic in fr) + "</div>", unsafe_allow_html=True)
#     with card("try3"):
#         ct("Try it in 3 steps")
#         st.markdown("1. Open **⚡ Check a payment** and choose a ready-made scenario.\n2. Press **Analyze transaction**.\n3. Read the explanation and the *How we got here* steps. Then change some values and run it again to see what changes the decision.")
#     with st.expander("📘 Glossary - words used in this app"):
#         gl = {"Risk score": "0-100. How suspicious the payment looks. Higher = more suspicious.", "Threshold": "The score cut-offs that turn a risk score into a decision. You can move them with the slider.",
#               "Challenge (OTP / 3-D Secure)": "Asking the customer to confirm with a one-time code or their bank app.", "Velocity": "How many payments happened on the same card in a short time.",
#               "Payee / beneficiary": "The person or account receiving the money.", "Chargeback": "When a customer disputes a payment and the money is taken back from the merchant, often with a fee.",
#               "False positive": "A good customer wrongly flagged as a fraudster. It costs sales and trust.", "Macro-F1": "An accuracy score (0-1) that treats every fraud type equally, even rare ones."}
#         for k_, v_ in gl.items(): st.markdown(f"**{k_}** - {v_}")

# {"dashboard": page_dashboard, "check": page_check, "live": page_live, "map": page_map, "roi": page_roi, "start": page_start}[ss["page"]]()

# import os, json, time, html, re, math
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

# import pandas as pd, networkx as nx, plotly.graph_objects as go, streamlit as st
# import streamlit.components.v1 as components
# from core.config import *
# from core.scenarios import SCENARIOS
# from core.roi_calc import compute_roi
# from core.stream_sim import StreamSimulator
# from core.theme import THEMES, ROUTE, css, plot_layout
# from core.narrative import summary, pipeline_steps, reasons, CLASS_EXPLAIN, ROUTE_EXPLAIN

# st.set_page_config(page_title="FraudShield 2.0", page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")
# ss = st.session_state
# for _k, _v in dict(page="dashboard", dark=True, result=None, payload=None, stream_on=False, sim=None, _thr=(ALLOW_BELOW, BLOCK_ABOVE), _secs=1.0, _atk=15).items():
#     ss.setdefault(_k, _v)
# MODE = "dark" if ss["dark"] else "light"; T = THEMES[MODE]

# # ------------------------------------------------------------------ styling
# st.markdown(css(MODE, ss["stream_on"], ss["page"]), unsafe_allow_html=True)
# _raw = css(MODE, ss["stream_on"], ss["page"]).replace("<style>", "").replace("</style>", "")
# components.html("<script>const d=window.parent.document;let e=d.getElementById('fs-theme');"
#                 "if(!e){e=d.createElement('style');e.id='fs-theme';d.head.appendChild(e);}"
#                 f"e.textContent={json.dumps(_raw)};</script>", height=0)

# # ------------------------------------------------------------------ helpers
# def inr(x):
#     s = str(int(round(abs(x)))); head, tail = s[:-3], s[-3:]
#     if head:
#         parts = []
#         while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
#         if head: parts.insert(0, head)
#         s = ",".join(parts) + "," + tail
#     return ("-" if x < 0 else "") + "Rs " + s

# def rgba(hex_, a):
#     h = hex_.lstrip("#"); return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

# def md2html(s): return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

# def card(key):
#     """A keyed container styled as a rounded card (plain container on older Streamlit)."""
#     try: return st.container(key="card_" + key)
#     except TypeError: return st.container()

# # One highlight colour per module (used by the top bar, the page title, the cards and the main button)
# MOD = {"dashboard": "#3B82F6", "check": "#8B5CF6", "live": "#F43F5E", "map": "#06B6D4", "roi": "#10B981", "start": "#F59E0B"}

# def header(title, sub):
#     st.markdown(f'<div class="pagehead"><p class="pt">{title}</p><p class="ps">{sub}</p></div>', unsafe_allow_html=True)

# def module_css(page):
#     c = MOD[page]; nav = ""
#     for k, col in MOD.items():
#         on = k == page
#         nav += (f".st-key-nav_{k}{{--c:{col}}}"
#                 f".st-key-nav_{k} button{{{'background:' + col + '!important;color:#fff!important;box-shadow:0 4px 14px ' + rgba(col, .35) + ';' if on else ''}}}"
#                 f".st-key-nav_{k} button:hover{{background:{rgba(col, .2) if not on else col}!important}}")
#     return ("<style>.stApp{--mod:" + c + "}"
#             ".block-container,[data-testid='stMainBlockContainer']{padding-top:3.6rem!important}header[data-testid='stHeader']{background:transparent!important}"                      # pulls the page up into the empty header band
#             ".st-key-topnav{margin-bottom:.4rem}"
#             "[class*='st-key-nav_'] button{width:100%;min-height:2.6rem;border-radius:12px;font-weight:600;padding:.35rem .4rem;"
#             "background:var(--surface,transparent)!important;color:var(--text)!important;border:1px solid var(--border)!important;border-bottom:3px solid var(--c)!important}"
#             "[class*='st-key-nav_'] button p{font-weight:600;white-space:nowrap}"
#             + nav +
#             f".pagehead{{border-left:5px solid {c};padding:.35rem 0 .35rem 1rem;margin:.6rem 0 1rem;border-radius:0 12px 12px 0;"
#             f"background:linear-gradient(90deg,{rgba(c, .14)},transparent 70%)}}.pagehead p{{margin:0}}"
#             f"[class*='st-key-card_']{{border-top:3px solid {c}!important}}"
#             f".kpi{{border-top:3px solid {c}}}"
#             f"button[kind='primary'],button[data-testid='stBaseButton-primary']{{background:{c}!important;border-color:{c}!important;color:#fff!important}}"
#             ".zbar{display:flex;border-radius:10px;overflow:hidden;font-size:.78rem;font-weight:700;text-align:center;margin:.2rem 0 .5rem}"
#             ".zbar div{padding:.38rem .2rem;white-space:nowrap;overflow:hidden}"
#             ".rl{font-weight:700;margin:.2rem 0 0}.rh{font-size:.8rem;opacity:.75;margin:0 0 .3rem}"
#             ".emptyhint{border:1.5px dashed var(--border);border-radius:14px;padding:.9rem 1.1rem;margin-bottom:.8rem}"
#             "</style>")

# def threshold_control(key):
#     """Risk-score cut-offs: ONE two-handle slider + a live colour bar that shows what the numbers mean."""
#     st.markdown('<p class="rl">Decision cut-offs (risk score 0-100)</p><p class="rh">Every payment gets a risk score. Drag the two handles to choose where '
#                 'it is allowed, challenged or blocked.</p>', unsafe_allow_html=True)
#     lo, hi = st.slider("Left handle = Allow below this score · Right handle = Block above this score", 0, 100, ss["_thr"], key=key,
#                        help="Lower numbers = stricter (more customers are challenged or blocked). Higher numbers = more relaxed (more fraud may slip through). "
#                             "Default: Allow below 30, Block above 70.")
#     ss["_thr"] = (lo, hi)
#     seg = lambda r, w, t: (f'<div style="flex:{w};background:{ROUTE[r][0]};color:{ROUTE[r][1]}">{t}</div>' if w > 0 else "")
#     st.markdown('<div class="zbar">' + seg("ALLOW", lo, f"Allow &lt; {lo}") + seg("CHALLENGE", hi - lo, f"Challenge {lo}-{hi}") + seg("HARD BLOCK", 100 - hi, f"Block &gt; {hi}") + "</div>"
#                 f'<p class="rh">Scores under <b>{lo}</b> go through · <b>{lo}-{hi}</b> ask the customer for an OTP / 3-D Secure · above <b>{hi}</b> are stopped.</p>', unsafe_allow_html=True)
#     return lo, hi

# def ct(title, sub=None):
#     st.markdown(f'<p class="ct">{title}</p>' + (f'<p class="cs">{sub}</p>' if sub else ""), unsafe_allow_html=True)

# def kpis(items):
#     return '<div class="kpis">' + "".join(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="s {c}">{s}</div></div>' for l, v, s, c in items) + "</div>"

# def pill(route, text):
#     bg, fg = ROUTE[route]; return f'<span class="pill" style="background:{bg};color:{fg}">{html.escape(text)}</span>'

# def html_table(rows, cols, bg=None):
#     head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
#     body = "".join((f'<tr style="background:{bg(r)}">' if bg else "<tr>") + "".join(f"<td>{html.escape(str(r.get(c, '')))}</td>" for c in cols) + "</tr>" for r in rows)
#     return f'<div style="overflow-x:auto"><table class="feed"><tr>{head}</tr>{body}</table></div>'

# WORD = {"ALLOW": "LOW RISK", "CHALLENGE": "MEDIUM RISK", "HARD BLOCK": "HIGH RISK"}
# ICON = {"ALLOW": "✔", "CHALLENGE": "!", "HARD BLOCK": "⛔"}
# STATUS = {"ALLOW": "Allowed", "CHALLENGE": "Challenged", "HARD BLOCK": "Blocked"}

# @st.cache_resource(show_spinner="Loading engine (first run trains the model, ~30 s)...")
# def load_engine():
#     if not os.path.exists(MODEL_PATH):
#         from core.data_gen import generate; import train_pipeline
#         generate(); train_pipeline.main()
#     from core.model_wrapper import FraudShieldEngine
#     return FraudShieldEngine()

# engine = load_engine()
# metrics = json.load(open(METRICS_PATH)) if os.path.exists(METRICS_PATH) else {}

# def make_event(p, truth, res, ts):
#     return dict(ts=ts, time=time.strftime("%H:%M:%S", time.localtime(ts)), txn=p["transaction_id"], user=p["user_id"], device=p["device_id"], amount=float(p["amount"]),
#                 truth=truth, pred=res["predicted_class"], risk=float(res["risk_score"]), route=res["route"], lat=float(res["latency_ms"]),
#                 why=reasons(res, p)[:3], fix=res["mitigation"])

# # The feed starts EMPTY on every visit: nothing is pre-scored. Payments appear only when you run the demo
# # (Check a payment / Live feed -> Live stream or Simulate fraud).
# if "feed" not in ss: ss["feed"] = []

# def add_event(p, truth):
#     lo, hi = ss["_thr"]; res = engine.score(p, lo, hi)
#     if res["valid"]:
#         ss["feed"] = (ss["feed"] + [make_event(p, truth, res, time.time())])[-600:]
#         if res["route"] == "HARD BLOCK": st.toast(f"BLOCKED {p['transaction_id']} - {res['predicted_class']} (risk {res['risk_score']})", icon="🚨")

# def tick():
#     """Advance the simulated stream by one payment (only when the Live stream switch is ON)."""
#     if not ss["stream_on"]: return
#     if ss["sim"] is None: ss["sim"] = StreamSimulator()
#     ss["sim"].attack_prob = ss["_atk"] / 100
#     p, truth = ss["sim"].next(); add_event(p, truth)

# def inject_attack():
#     if ss["sim"] is None: ss["sim"] = StreamSimulator()
#     ss["sim"]._start_attack()
#     while ss["sim"].queue:
#         p, truth = ss["sim"].queue.popleft(); add_event(p, truth)

# def fig_area(vals, lo, hi):
#     fig = go.Figure(go.Scatter(y=vals, mode="lines", line=dict(color=T["accent"], width=2), fill="tozeroy", fillcolor=rgba(T["accent"], .16)))
#     fig.add_hline(y=lo, line_dash="dash", line_color=ROUTE["CHALLENGE"][0]); fig.add_hline(y=hi, line_dash="dash", line_color=ROUTE["HARD BLOCK"][0])
#     fig.update_layout(**plot_layout(MODE, 250, margin=dict(t=10, b=10, l=10, r=10))); fig.update_yaxes(range=[0, 100], gridcolor=T["border"]); fig.update_xaxes(visible=False)
#     return fig

# def fig_bars(labels, values, colors, height=250):
#     fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, text=values, textposition="outside"))
#     fig.update_layout(**plot_layout(MODE, height, margin=dict(t=20, b=10, l=10, r=10))); fig.update_yaxes(gridcolor=T["border"]); return fig

# CFG = {"displayModeBar": False}

# st.markdown(module_css(ss["page"]), unsafe_allow_html=True)   # module colours + top bar styling (after the theme CSS so it wins)

# # ------------------------------------------------------------------ sidebar
# NAV = [("dashboard", "📊", "Dashboard", "MAIN"), ("check", "⚡", "Check a payment", None), ("live", "📡", "Live feed", None),
#        ("map", "🕸️", "Connections map", "ANALYTICS"), ("roi", "💰", "Money saved", None), ("start", "🏠", "Start here", "HELP")]
# with st.sidebar:
#     st.markdown(f'<p class="brand">{APP_ICON} FraudShield 2.0</p><p class="brand-sub">Real-time, explainable fraud decisions</p>', unsafe_allow_html=True)
#     st.markdown('<div class="navlabel">APPEARANCE</div>', unsafe_allow_html=True)
#     st.button("🌙 Dark mode" if ss["dark"] else "☀️ Light mode", key="theme_btn", on_click=lambda: ss.update(dark=not ss["dark"]), help="Switch between dark and light mode.")
#     ev_ = ss["feed"]; avg_ = sum(e["lat"] for e in ev_) / max(len(ev_), 1)
#     _f1 = metrics.get("simulated_macro_f1", metrics.get("macro_f1", 0))
#     _ieee = (f'<br>Real data (IEEE-CIS) ROC-AUC: <b>{metrics["ieee_roc_auc"]:.2f}</b><br>Trained on: <b>{metrics.get("rows", 0):,}</b> payments incl. <b>{metrics["ieee_rows"]:,}</b> real'
#              if metrics.get("ieee_rows") else "")
#     st.markdown(f'<div class="sidecard"><b>Engine status</b><br>Model: gradient-boosted trees<br>Accuracy (macro-F1, simulated): <b>{_f1 * 100:.1f}%</b>{_ieee}<br>Avg decision time: <b>{avg_:.1f} ms</b><br>Payments checked: <b>{len(ev_):,}</b></div>', unsafe_allow_html=True)

# # ------------------------------------------------------------------ top navigation bar (fills the header band)
# def top_nav():
#     try: box = st.container(key="topnav")
#     except TypeError: box = st.container()
#     with box:
#         for col, (key, icon, label, _sec) in zip(st.columns(len(NAV)), NAV):
#             col.button(f"{icon} {label}", key=f"nav_{key}", on_click=lambda k=key: ss.update(page=k))

# # ================================================================== PAGES
# def page_dashboard():
#     header("Fraud detection overview", "What the engine has seen and decided. Payments are simulated; every decision is made by the real engine.")
#     def body():
#         tick()
#         ev = ss["feed"]; n = max(len(ev), 1); lo, hi = ss["_thr"]
#         if not ev:
#             st.markdown('<div class="emptyhint"><b>Nothing has been checked yet.</b> This dashboard fills up as payments are scored. '
#                         'Open <b>⚡ Check a payment</b> to test one payment, or <b>📡 Live feed</b> and press <b>Live stream</b> / <b>Simulate fraud</b> to watch the engine work.</div>', unsafe_allow_html=True)
#         alerts = [e for e in ev if e["route"] != "ALLOW"]; blocks = [e for e in ev if e["route"] == "HARD BLOCK"]; avg = sum(e["lat"] for e in ev) / n
#         main, side = st.columns([3, 1.25])
#         with main:
#             st.markdown(kpis([("Payments checked", f"{len(ev):,}", "simulated + live", ""), ("Alerts raised", f"{len(alerts):,}", f"{len(alerts) / n * 100:.1f}% challenged or blocked", ""),
#                               ("Hard blocks", f"{len(blocks):,}", f"{len(blocks) / n * 100:.1f}% of payments", "down" if blocks else ""), ("Avg decision time", f"{avg:.1f} ms", "budget: 100 ms", "up")]), unsafe_allow_html=True)
#             a, b = st.columns(2)
#             with a:
#                 with card("risk"):
#                     ct("Risk score over time", "Last 80 payments; dashed lines are your thresholds"); st.plotly_chart(fig_area([e["risk"] for e in ev[-80:]], lo, hi), key="dash_area", config=CFG)
#             with b:
#                 with card("dec"):
#                     ct("Decisions by type", "How every payment was routed")
#                     cnt = [sum(e["route"] == r for e in ev) for r in ("ALLOW", "CHALLENGE", "HARD BLOCK")]
#                     st.plotly_chart(fig_bars(["Allowed", "Challenged", "Blocked"], cnt, [ROUTE[r][0] for r in ("ALLOW", "CHALLENGE", "HARD BLOCK")]), key="dash_bar", config=CFG)
#             with card("recent"):
#                 ct("Recent decisions (audit log)", "Latest 8 payments")
#                 rows = [{"Time": e["time"], "Payment": e["txn"], "Amount": inr(e["amount"]), "Predicted": e["pred"], "Risk": f"{e['risk']:.0f}", "Decision": STATUS[e["route"]]} for e in reversed(ev[-8:])]
#                 st.markdown(html_table(rows, list(rows[0]), bg=lambda r: rgba(ROUTE[{v: k for k, v in STATUS.items()}[r["Decision"]]][0], .14)) if rows else "No payments yet.", unsafe_allow_html=True)
#         with side:
#             with card("cats"):
#                 ct("Fraud types detected", "By the AI model")
#                 for name, col in (("Credit Card Fraud", "#EF4444"), ("Account Takeover", "#F59E0B"), ("APP Scam", T["accent2"]), ("Card Testing", T["accent"])):
#                     k_ = sum(e["pred"] == name for e in ev)
#                     st.markdown(f'<div class="cat"><span><span style="color:{col}">●</span>&nbsp; {name}</span><b>{k_}</b></div>', unsafe_allow_html=True)
#             with card("alerts"):
#                 ct("Latest alerts", "Newest first")
#                 last = [e for e in ev if e["route"] != "ALLOW"][-4:][::-1]
#                 st.markdown("".join(f'<div class="ar"><b>{e["pred"]} - {STATUS[e["route"]]}</b><span>{html.escape(("; ".join(e["why"]) or "-")[:120])}</span><br><em>{e["time"]} · {e["txn"]} · {inr(e["amount"])}</em></div>' for e in last) or '<span class="muted">No alerts yet.</span>', unsafe_allow_html=True)
#             st.download_button("⬇ Download audit CSV", pd.DataFrame([{k: v for k, v in e.items() if k not in ("why", "fix", "ts")} for e in ev]).to_csv(index=False), "audit_log.csv", "text/csv", key="dl_audit")
#     st.fragment(run_every=(ss["_secs"] if ss["stream_on"] else None))(body)()

# SCEN_INFO = {
#     "Normal everyday purchase": "A regular customer buys something at a normal amount from their usual device.",
#     "Launch Card Testing Automated Script Attack": "A bot fires 5 tiny payments on one card within a minute to see if a stolen card works.",
#     "Account Takeover (new device + payee change)": "A criminal logs in from a new device, adds a new payee minutes ago and sends a big amount.",
#     "APP Scam (trusted device, big transfer to new payee)": "The real customer, tricked by a scammer, sends a large amount to a brand-new payee.",
#     "Card-Not-Present Credit Card Fraud": "Stolen card details used online from a foreign IP address, at night, for a high-value order.",
#     "Custom transaction": "Edit any value yourself and watch how the decision changes."}

# def page_check():
#     header("Check a payment", "Pick a scenario, change any value, and see exactly how FraudShield decides - and why.")
#     L, Rr = st.columns([1, 1.1])
#     with L:
#         with card("inputs"):
#             ct("💳 Transaction details")
#             names = list(SCENARIOS) + ["Custom transaction"]
#             scen = st.selectbox("Ready-made scenario", names, help="Pick an example. You can still edit every value below.")
#             st.markdown(f'<div class="ex">{SCEN_INFO[scen]}</div>', unsafe_allow_html=True)
#             base = SCENARIOS[scen] if scen in SCENARIOS else SCENARIOS["Normal everyday purchase"]; k = lambda f: f"{f}|{scen}"
#             a, b = st.columns(2)
#             amount = a.number_input("Payment amount (Rs)", min_value=-1000.0, value=float(base["amount"]), key=k("amount"), help="Must be above 0 - try a negative value to see validation work.")
#             velocity = b.number_input("Payments on this card in last 60 s", value=int(base["velocity_1m"]), step=1, key=k("vel"), help="3+ tiny payments in a minute is a classic bot pattern.")
#             payee = a.number_input("Hours since payee was changed", min_value=-1.0, value=float(base["payee_changed_hours"]), key=k("payee"), help="A very recent change followed by a big payment is suspicious.")
#             age = b.number_input("Account age (days)", value=int(base["account_age_days"]), step=1, key=k("age"))
#             ip = a.text_input("IP country (2 letters)", base["ip_country"], key=k("ip"), help="e.g. IN, US, GB. The customer's home country is IN.")
#             new_dev = b.checkbox("From a new / unrecognised device", base["is_new_device"], key=k("nd"))
#             with st.expander("More fields (IDs, device, customer's usual spend)"):
#                 tid = st.text_input("Transaction ID", base["transaction_id"], key=k("tid")); uid = st.text_input("User ID", base["user_id"], key=k("uid"))
#                 cid = st.text_input("Card ID", base["card_id"], key=k("cid")); dev = st.text_input("Device ID (hex)", base["device_id"], key=k("dev"))
#                 avg = st.number_input("Customer's usual payment (Rs)", value=float(base["user_avg_amount"]), key=k("avg")); hour = st.number_input("Hour of day (0-23)", value=int(base["hour"]), step=1, key=k("hour"))
#             lo_t, hi_t = threshold_control("c_thr")
#             if st.button("Analyze transaction", type="primary", key="analyze"):
#                 payload = dict(transaction_id=tid, user_id=uid, card_id=cid, amount=amount, device_id=dev, ip_country=ip, velocity_1m=int(velocity), account_age_days=int(age),
#                                payee_changed_hours=payee, is_new_device=new_dev, user_avg_amount=avg, hour=int(hour))
#                 res = engine.score(payload, lo_t, hi_t); ss["result"], ss["payload"], ss["rthr"] = res, payload, (lo_t, hi_t)
#                 if res["valid"]: ss["feed"] = (ss["feed"] + [make_event(payload, "(manual check)", res, time.time())])[-600:]
#     res, p = ss["result"], ss["payload"]
#     with Rr:
#         with card("result"):
#             ct("✨ AI analysis results")
#             if res is None:
#                 st.markdown('<div class="ex">👈 Choose a scenario and press <b>Analyze transaction</b>. The decision, the reasons and the recommended action will appear here.</div>', unsafe_allow_html=True)
#             elif not res["valid"]:
#                 st.error("This payment was rejected before scoring because some fields are invalid:")
#                 for e in res["errors"]: st.write("• " + e)
#                 st.caption("Validation protects the engine from bad data. Fix the fields and run again.")
#             else:
#                 bg, fg = ROUTE[res["route"]]; pr = max(res["probabilities"].values()) * 100
#                 st.markdown(f'<div class="banner" style="background:{bg};color:{fg}"><div><div class="k">Risk assessment</div><div class="t">{WORD[res["route"]]}</div></div><div class="t">{ICON[res["route"]]}</div></div>', unsafe_allow_html=True)
#                 st.markdown(f'<div class="tile"><b>Fraud probability</b><div class="bar"><div style="width:{res["risk_score"]:.1f}%;background:{bg}"></div></div><div class="big">{res["risk_score"]:.1f}%</div></div>', unsafe_allow_html=True)
#                 st.markdown(f'<div class="tile" style="margin-top:12px"><b>Model insights</b><div class="mi" style="margin-top:10px"><div><div class="l">Confidence</div><div class="v">{pr:.1f}%</div></div><div><div class="l">Processing time</div><div class="v">{res["latency_ms"]} ms</div></div>'
#                             f'<div><div class="l">Predicted class</div><div class="v">{res["predicted_class"]}</div></div><div><div class="l">Status</div><div class="v">{STATUS[res["route"]]}</div></div></div></div>', unsafe_allow_html=True)
#                 why = reasons(res, p)
#                 st.markdown('<div class="tile" style="margin-top:12px"><b>AI explanation</b>' + f'<div class="ex">{md2html(summary(res, p))}</div>' + "".join(f'<div class="ex">• {html.escape(w)}</div>' for w in why[:4]) + "</div>", unsafe_allow_html=True)
#                 st.download_button("⬇ Download result (JSON)", json.dumps(res, indent=2, default=str), "fraudshield_result.json", "application/json", key="dl_res")
#     if res is not None and res["valid"]:
#         lo, hi = ss.get("rthr", (ALLOW_BELOW, BLOCK_ABOVE)); col = ROUTE[res["route"]][0]
#         a, b = st.columns(2)
#         with a:
#             with card("steps"):
#                 ct("How we got here", "What each stage of the pipeline did")
#                 st.markdown("".join(f'<div class="step {"flag" if fl else ""}">{ic} <b>{ti}</b><br><span class="muted">{md2html(de)}</span></div>' for ic, ti, de, fl in pipeline_steps(res, p, lo, hi)), unsafe_allow_html=True)
#         with b:
#             with card("drivers"):
#                 ct("What pushed the risk up?", "Share of the risk push, %")
#                 if not res["explain_ok"]: st.warning("The explanation module failed, so the decision used rules and the AI only (the system keeps working even if explanations fail).")
#                 elif res["drivers"]:
#                     d = res["drivers"][::-1]
#                     f2 = go.Figure(go.Bar(x=[x["impact"] for x in d], y=[x["label"] for x in d], orientation="h", marker_color=ROUTE["HARD BLOCK"][0]))
#                     f2.update_layout(**plot_layout(MODE, 230)); f2.update_xaxes(gridcolor=T["border"]); st.plotly_chart(f2, key="chk_drv", config=CFG)
#                 else: st.markdown('<span class="muted">Nothing pushed the risk up - a normal payment.</span>', unsafe_allow_html=True)
#         c1, c2 = st.columns(2)
#         with c1:
#             with card("conf"):
#                 ct("AI confidence per outcome", "Chance of each class, %")
#                 prb = res["probabilities"]; nm = list(prb)[::-1]
#                 f3 = go.Figure(go.Bar(x=[prb[n] * 100 for n in nm], y=nm, orientation="h", marker_color=[T["accent"] if n == res["predicted_class"] else T["border"] for n in nm]))
#                 f3.update_layout(**plot_layout(MODE, 230)); f3.update_xaxes(range=[0, 100], gridcolor=T["border"]); st.plotly_chart(f3, key="chk_conf", config=CFG)
#         with c2:
#             with card("action"):
#                 ct("What should the team do?")
#                 st.markdown(f'<div class="ex" style="border-left-color:{col}">{res["mitigation"] if res["route"] != "ALLOW" else "Nothing - the payment goes through with no extra steps."}</div>', unsafe_allow_html=True)
#                 st.caption(f"Decided in {res['latency_ms']} ms (budget {LATENCY_BUDGET_MS} ms).")

# def feed_card(e):
#     bg, fg = ROUTE[e["route"]]; why = ("; ".join(e["why"]) or "")[:110]
#     return (f'<div class="fc" style="border-left-color:{bg}"><div class="h"><span>{e["txn"]}</span><span class="pill" style="background:{rgba(bg, .22)};color:{bg}">{e["risk"]:.1f}% Risk</span></div>'
#             f'<div class="g"><div><span class="l">User</span><span class="v">{e["user"]}</span></div><div><span class="l">Amount</span><span class="v">{inr(e["amount"])}</span></div><div><span class="l">Decision</span><span class="v">{STATUS[e["route"]]}</span></div>'
#             f'<div><span class="l">Predicted</span><span class="v">{e["pred"]}</span></div><div><span class="l">Actual (hidden)</span><span class="v">{html.escape(e["truth"])}</span></div><div><span class="l">Time</span><span class="v">{e["time"]}</span></div></div>'
#             + (f'<div class="muted" style="font-size:.78rem;margin-top:8px">Why: {html.escape(why)}</div>' if why and e["route"] != "ALLOW" else "") + "</div>")

# def page_live():
#     header("Live payment feed", "A simulator plays the payment gateway; every payment is scored the moment it arrives.")
#     L, Rr = st.columns([1, 1.35])
#     with L:
#         with card("sim"):
#             ct("⚙️ Transaction simulator")
#             st.button("Live stream: ON" if ss["stream_on"] else "Live stream: OFF", key="stream_btn", on_click=lambda: ss.update(stream_on=not ss["stream_on"]), help="Start / pause the simulated feed.")
#             st.markdown('<span class="live" style="background:#EF4444;color:#fff">● LIVE</span> payments are arriving…' if ss["stream_on"] else '<span class="live" style="background:var(--surface2);color:var(--muted)">⏸ PAUSED</span> press the switch above to start', unsafe_allow_html=True)
#             st.markdown('<p class="rl">Simulator settings</p>', unsafe_allow_html=True)
#             ss["_secs"] = st.slider("Speed: seconds between payments (0.5 = fast, 3 = slow)", 0.5, 3.0, float(ss["_secs"]), 0.5, key="w_secs", help="How often a new payment arrives while the Live stream is ON.")
#             ss["_atk"] = st.slider("Fraud attacks: % of the stream (0 = none, 50 = half)", 0, 50, int(ss["_atk"]), key="w_atk", help="How often the simulator starts a fraud attack instead of a normal payment.")
#             threshold_control("w_thr")
#             b1, b2 = st.columns(2)
#             if b1.button("⚡ Simulate fraud", key="simfraud", help="Inject one attack right now."): inject_attack()
#             if b2.button("🗑 Clear all", key="clearall"): ss["feed"] = []; ss["sim"] = None
#         with st.expander("ℹ️ What am I looking at?"):
#             st.markdown("- Each card is one payment. **Actual** is what the simulator really made it (the engine never sees this); **Predicted** is what FraudShield thinks.\n"
#                         "- Card colour = decision: green Allowed, amber Challenged, red Blocked. A pop-up appears for every block.\n"
#                         "- Card-testing bursts are usually only caught from the 3rd payment, because the rule needs 3 tiny payments in a minute. That is a real limit of rule-based detection.")
#     with Rr:
#         with card("feed"):
#             ct("📡 Live transaction feed")
#             flt = st.radio("Filter", ["All", "Flagged", "Allowed"], horizontal=True, label_visibility="collapsed", key="w_flt")
#             def body():
#                 tick(); ev = ss["feed"]
#                 if not ev: st.markdown('<div class="ex">No payments yet. Press the <b>Live stream</b> switch or <b>Simulate fraud</b>.</div>', unsafe_allow_html=True); return
#                 att = [e for e in ev if e["truth"] not in ("Legitimate", "(manual check)")]; good = [e for e in ev if e["truth"] == "Legitimate"]
#                 caught = sum(e["route"] != "ALLOW" for e in att); fa = sum(e["route"] != "ALLOW" for e in good)
#                 st.markdown(kpis([("Checked", f"{len(ev):,}", "", ""), ("Alerts", f"{sum(e['route'] != 'ALLOW' for e in ev):,}", "challenged or blocked", ""), ("Fraud flagged", f"{caught}/{len(att)}", "real attacks caught", "up"), ("Good flagged", f"{fa}/{len(good)}", "false alarms", "down" if fa else "")]), unsafe_allow_html=True)
#                 last = ev[-1]
#                 if last["route"] != "ALLOW":
#                     bg, fg = ROUTE[last["route"]]
#                     st.markdown(f'<div class="banner blink" style="background:{bg};color:{fg}"><div><div class="k">Latest alert · {last["time"]}</div><div class="t" style="font-size:1.15rem">{STATUS[last["route"]].upper()}: {last["txn"]} · {last["pred"]} · risk {last["risk"]:.0f}</div></div></div>', unsafe_allow_html=True)
#                 shown = [e for e in reversed(ev) if flt == "All" or (flt == "Flagged" and e["route"] != "ALLOW") or (flt == "Allowed" and e["route"] == "ALLOW")][:14]
#                 st.markdown('<div class="feedwrap">' + "".join(feed_card(e) for e in shown) + "</div>", unsafe_allow_html=True)
#             st.fragment(run_every=(ss["_secs"] if ss["stream_on"] else None))(body)()

# def short(i): return i[:4] + "…" + i[-4:]

# def page_map():
#     header("Connections map", "Who shares a device with whom. A device used by many customers or cards is a classic sign of a bot or fraud ring.")
#     G = engine.graph.G
#     sus = [(n[1], sum(1 for m in G.neighbors(n) if m[0] == "user"), sum(1 for m in G.neighbors(n) if m[0] == "card")) for n in G if n[0] == "device"]
#     sus = sorted(sus, key=lambda r: -(r[1] + r[2]))[:15]
#     options = {f"{d[:8]}…  ({u} customers, {c} cards)": d for d, u, c in sus}
#     if ss["payload"]: options = {f"Device from your last check ({ss['payload']['device_id'][:8]}…)": ss["payload"]["device_id"], **options}
#     pick = st.selectbox("Choose a device to inspect", list(options), help="The list shows the most widely shared devices first.")
#     dev = options[pick]; centre = ("device", dev)
#     users = sorted(m[1] for m in G.neighbors(centre) if m[0] == "user") if centre in G else []
#     cards = sorted(m[1] for m in G.neighbors(centre) if m[0] == "card") if centre in G else []
#     bad = len(users) >= 3 or len(cards) >= 3
#     L, Rr = st.columns([1.7, 1])
#     with L:
#         with card("graph"):
#             ct("Device network", "Green = customers, grey = cards, large circle = the device (red when suspicious)")
#             if centre not in G:
#                 st.markdown('<div class="ex">This device has never been seen before, so it has no connections yet - being brand new is itself a mild warning sign.</div>', unsafe_allow_html=True)
#             else:
#                 U, C = users[:60], cards[:40]; pos = {centre: (0.0, 0.0)}
#                 for i, u in enumerate(U): a_ = 2 * math.pi * i / max(len(U), 1); pos[("user", u)] = (math.cos(a_), math.sin(a_))
#                 for j, c_ in enumerate(C): a_ = 2 * math.pi * (j + .5) / max(len(C), 1); pos[("card", c_)] = (1.7 * math.cos(a_), 1.7 * math.sin(a_))
#                 ex, ey = [], []
#                 for u_, v_ in G.subgraph(list(pos)).edges(): ex += [pos[u_][0], pos[v_][0], None]; ey += [pos[u_][1], pos[v_][1], None]
#                 fig = go.Figure(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=T["accent2"], width=1), hoverinfo="none", showlegend=False))
#                 lab = len(U) + len(C) <= 45
#                 for kind, col, ids, nm in (("user", T["accent"], U, "Customer"), ("card", T["muted"], C, "Card")):
#                     fig.add_trace(go.Scatter(x=[pos[(kind, i)][0] for i in ids], y=[pos[(kind, i)][1] for i in ids], mode="markers+text" if lab else "markers", name=nm, text=[short(i) for i in ids],
#                                              textposition="bottom center", textfont=dict(size=9, color=T["text"]), marker=dict(size=20 if kind == "user" else 14, color=col), hovertext=ids))
#                 fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", name="Device", text=["DEVICE"], textfont=dict(size=10, color="#FFFFFF"), marker=dict(size=70, color="#EF4444" if bad else T["accent"]), hovertext=[dev]))
#                 fig.update_layout(**plot_layout(MODE, 560, margin=dict(t=10, b=10, l=10, r=10))); fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x")
#                 st.plotly_chart(fig, key="map_fig", config=CFG)
#     with Rr:
#         with card("nodes"):
#             ct("Node details")
#             tone = "#EF4444" if bad else T["accent"]
#             st.markdown(f'<div class="tile" style="border-left:5px solid {tone}"><b>{"⚠️ Suspicious device" if bad else "✅ Looks normal"}</b><br><span class="muted">Device ID</span> <code>{dev}</code>'
#                         f'<div class="mi" style="margin-top:8px"><div><div class="l">Customers</div><div class="v">{len(users)}</div></div><div><div class="l">Cards</div><div class="v">{len(cards)}</div></div></div></div>', unsafe_allow_html=True)
#             t1, t2, t3 = st.tabs([f"Customers ({len(users)})", f"Cards ({len(cards)})", "Signals"])
#             with t1: st.markdown("".join(f'<div class="cat"><span>👤 {u}</span></div>' for u in users[:25]) or '<span class="muted">None</span>', unsafe_allow_html=True)
#             with t2: st.markdown("".join(f'<div class="cat"><span>💳 {c_}</span></div>' for c_ in cards[:25]) or '<span class="muted">None</span>', unsafe_allow_html=True)
#             with t3:
#                 sig = []
#                 if len(users) >= 3: sig.append(("#EF4444", "More than two customers use this device", f"{len(users)} different customers"))
#                 if len(cards) >= 3: sig.append(("#EF4444", "Many cards used on one device", f"{len(cards)} different cards"))
#                 if not sig: sig.append((T["accent"], "No sharing pattern", "One device, few customers - what we expect"))
#                 for e in [e for e in ss["feed"] if e["device"] == dev][-5:]: sig.append((ROUTE[e["route"]][0], f"Payment {e['txn']} was {STATUS[e['route']].lower()}", f"{e['pred']} · risk {e['risk']:.0f} · {e['time']}"))
#                 st.markdown("".join(f'<div class="sig"><i style="background:{c_}"></i><div><b>{html.escape(t_)}</b><span>{html.escape(d_)}</span></div></div>' for c_, t_, d_ in sig), unsafe_allow_html=True)

# def page_roi():
#     header("How much money does this save?", "Describe a business, and compare FraudShield with an older, weaker system. All numbers are example assumptions, not real data.")
#     with card("roiin"):
#         ct("Business settings", "Step 1: choose an example business and drag the two sliders. Step 2 (optional): fine-tune the fraud levels. Results below update instantly.")
#         PRE = {"Mid-size fintech": (50, 1500), "Small online shop": (5, 800), "Large bank / marketplace": (400, 3500)}
#         pre = st.selectbox("Start from an example business", list(PRE), help="Sets the two sliders below. You can still change them.")
#         a, b = st.columns(2)
#         vol_cr = a.slider("Monthly payments processed (Rs crore) · range 1-500", 1, 500, PRE[pre][0], key=f"vol|{pre}", help="Total value of payments per month. 1 crore = 10 million rupees.")
#         ticket = b.slider("Average payment size (Rs) · range 100-20,000", 100, 20000, PRE[pre][1], step=100, key=f"tkt|{pre}", help="Typical value of one payment. Smaller payments = more transactions to protect.")
#         with st.expander("Fraud levels and how good the old system is (optional)", expanded=True):
#             x1, x2, x3 = st.columns(3)
#             fraud_rate = x1.number_input("Share of payments that are fraud (%) · 0.1-10", 0.1, 10.0, 2.0, 0.1, help="Out of every 100 payments, how many are fraud. Example assumption.") / 100
#             legacy_det = x2.number_input("Old system catches (% of fraud) · 0-100", 0.0, 100.0, 50.0, 1.0, help="Of all fraud, the share the current system stops. Example assumption.") / 100
#             new_det = x3.number_input("FraudShield catches (% of fraud) · 0-100", 0.0, 100.0, 92.0, 1.0, help="Of all fraud, the share FraudShield stops. Example assumption.") / 100
#             legacy_fpr = x1.number_input("Old system wrongly flags good customers (%) · 0-20", 0.0, 20.0, 2.0, 0.1, help="Share of genuine payments the old system wrongly challenges or blocks (false alarms).") / 100
#             new_fpr = x2.number_input("FraudShield wrongly flags good customers (%) · 0-20", 0.0, 20.0, 0.12, 0.01, help="Share of genuine payments FraudShield wrongly challenges or blocks (false alarms).") / 100
#             fee = x3.number_input("Fee per chargeback (Rs) · 0-10,000", 0.0, 10000.0, 1250.0, 50.0, help="What the bank charges the business each time a customer disputes a payment.")
#     r = compute_roi(vol_cr * 1e7, ticket, fraud_rate, legacy_det, new_det, legacy_fpr, new_fpr, chargeback_fee=fee)
#     st.markdown(f'<div class="hero"><h2>About {inr(r["total_monthly_benefit"])} saved every month</h2><p>That is {r["extra_fraud_caught"]:,.0f} extra fraud payments stopped and about {r["false_positives_old"] - r["false_positives_new"]:,.0f} fewer good customers wrongly flagged.</p></div>', unsafe_allow_html=True)
#     st.markdown(kpis([("Stock not lost to fraud", inr(r["inventory_loss_avoided"]), "goods valued at cost", "up"), ("Chargeback fees avoided", inr(r["chargeback_fees_avoided"]), "fees per disputed payment", "up"),
#                       ("Penalty fine avoided", inr(r["monitoring_fine_avoided"]), "card-network monitoring", "up"), ("Happier customers", inr(r["friction_savings"]), "fewer false alarms", "up")]), unsafe_allow_html=True)
#     c1, c2 = st.columns([1.4, 1])
#     with c1:
#         with card("roichart"):
#             ct("Where the monthly saving comes from (Rs)")
#             parts = {"Stock not lost": r["inventory_loss_avoided"], "Chargeback fees": r["chargeback_fees_avoided"], "Penalty fine": r["monitoring_fine_avoided"], "Fewer false alarms": r["friction_savings"]}
#             fig = go.Figure(go.Bar(x=list(parts), y=list(parts.values()), marker_color=[T["accent"], T["accent2"], T["muted"], T["border"]]))
#             fig.update_layout(**plot_layout(MODE, 300)); fig.update_yaxes(gridcolor=T["border"]); st.plotly_chart(fig, key="roi_fig", config=CFG)
#     with c2:
#         with card("roinote"):
#             ct("Chargeback rate")
#             over = r["chargeback_ratio_old_pct"] >= 0.9
#             st.markdown(f'<div class="big">{r["chargeback_ratio_old_pct"]:.2f}% → {r["chargeback_ratio_new_pct"]:.2f}%</div><p class="muted" style="text-align:center">old system → FraudShield</p>'
#                         f'<div class="ex">{"The old rate is above the ~0.9% line where card networks start fining merchants." if over else "The old rate was already below the ~0.9% fine line."}</div>', unsafe_allow_html=True)

# def page_start():
#     header("Start here", "A two-minute guide to what FraudShield does and how to read it.")
#     st.markdown('<div class="hero"><h2>What does FraudShield do?</h2><p>When a payment arrives, FraudShield looks at who is paying, from which device, how much and how fast - and within a fraction of a second decides what to do with it. Try it in <b>Check a payment</b>, or watch it work on its own in <b>Live feed</b>.</p></div>', unsafe_allow_html=True)
#     with card("dec3"):
#         ct("The 3 possible decisions")
#         st.markdown('<div class="grid">' + "".join(f'<div class="tile" style="border-top:5px solid {ROUTE[r][0]}"><b>{t}</b><br><span class="muted">{ROUTE_EXPLAIN[r]}</span></div>' for r, t in [("ALLOW", "Allow"), ("CHALLENGE", "Challenge"), ("HARD BLOCK", "Block")]) + "</div>", unsafe_allow_html=True)
#     with card("steps5"):
#         ct("How a payment is checked (5 steps, ~10 milliseconds)")
#         steps = [("Check the data", "Is the payment information complete and valid?"), ("Safety rules", "Instant yes/no rules, e.g. 3+ tiny payments in a minute."), ("Connection check", "Is one device or card linked to many customers?"), ("AI model", "Estimates the chance of each type of fraud."), ("Decision", "Allow, Challenge or Block - with reasons you can read.")]
#         st.markdown('<div class="grid">' + "".join(f'<div class="tile"><span class="num">{i}</span><b>{t}</b><br><span class="muted">{d}</span></div>' for i, (t, d) in enumerate(steps, 1)) + "</div>", unsafe_allow_html=True)
#     with card("types4"):
#         ct("The 4 kinds of fraud it recognises")
#         fr = [("Card Testing", "🤖"), ("Account Takeover", "🔑"), ("APP Scam", "🎭"), ("Credit Card Fraud", "💳")]
#         st.markdown('<div class="grid">' + "".join(f'<div class="tile"><b>{ic} {n}</b><br><span class="muted">{CLASS_EXPLAIN[n][0].upper() + CLASS_EXPLAIN[n][1:]}.</span></div>' for n, ic in fr) + "</div>", unsafe_allow_html=True)
#     with card("try3"):
#         ct("Try it in 3 steps")
#         st.markdown("1. Open **⚡ Check a payment** and choose a ready-made scenario.\n2. Press **Analyze transaction**.\n3. Read the explanation and the *How we got here* steps. Then change some values and run it again to see what changes the decision.")
#     with st.expander("📘 Glossary - words used in this app"):
#         gl = {"Risk score": "0-100. How suspicious the payment looks. Higher = more suspicious.", "Threshold": "The score cut-offs that turn a risk score into a decision. You can move them with the slider.",
#               "Challenge (OTP / 3-D Secure)": "Asking the customer to confirm with a one-time code or their bank app.", "Velocity": "How many payments happened on the same card in a short time.",
#               "Payee / beneficiary": "The person or account receiving the money.", "Chargeback": "When a customer disputes a payment and the money is taken back from the merchant, often with a fee.",
#               "False positive": "A good customer wrongly flagged as a fraudster. It costs sales and trust.", "Macro-F1": "An accuracy score (0-1) that treats every fraud type equally, even rare ones."}
#         for k_, v_ in gl.items(): st.markdown(f"**{k_}** - {v_}")

# top_nav()
# {"dashboard": page_dashboard, "check": page_check, "live": page_live, "map": page_map, "roi": page_roi, "start": page_start}[ss["page"]]()
