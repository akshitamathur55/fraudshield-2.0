import subprocess, os, sys, json
IMG="/home/claude/report/img"
F='fontname="Helvetica"'
def dot(name, src):
    open(f"/tmp/{name}.dot","w").write(src)
    subprocess.run(["dot","-Tpng","-Gdpi=200",f"/tmp/{name}.dot","-o",f"{IMG}/{name}.png"],check=True)
G,DK,M,L,P="#00D084","#06231F","#006A4E","#30BA8F","#E3F0EA"
NODE=f'node [shape=box style="rounded,filled" fillcolor="{P}" color="{M}" {F} fontsize=11 margin="0.15,0.08"]; edge [{F} fontsize=9 color="#2F4F46"]; graph [{F} fontname="Helvetica" pad=0.2]'

# 1 architecture

# 2 use case
dot("usecase", f'''digraph U {{ rankdir=LR; {NODE}; nodesep=0.18; ranksep=0.55; node [fontsize=12];
subgraph cluster_a {{ label=""; style=invis; ro[label="Risk / Compliance\\nOfficer" shape=box style="filled" fillcolor="#FFFFFF"]; pm[label="Fintech Product\\nManager" shape=box style="filled" fillcolor="#FFFFFF"]; ad[label="System Administrator\\n(audit view)" shape=box style="filled" fillcolor="#FFFFFF"]; si[label="Stream Simulator\\n(system actor)" shape=box style="filled" fillcolor="#FFF3D6"]; }}
subgraph cluster_s {{ label="FraudShield 2.0"; style="rounded"; color="{M}"; fontsize=13;
 node [shape=ellipse style=filled fillcolor="{P}"];
 u1[label="Pick / edit a payment"]; u2[label="Score payment (Execute)"]; u3[label="Set Allow/Block thresholds"]; u4[label="View decision, risk score\\nand mitigation"]; u5[label="Read plain-English\\nexplanation + drivers"]; u6[label="Watch live payment feed"]; u7[label="Inspect device /\\ncard / user graph"]; u8[label="Simulate business ROI"]; u9[label="View & download audit log"]; u10[label="Switch dark / light theme"]; u11[label="Validate payload schema" fillcolor="#FFF3D6"]; }}
ro->u1; ro->u2; ro->u3; ro->u4; ro->u5; ro->u6; ro->u7; ro->u10; pm->u8; pm->u3; pm->u6; ad->u9; si->u6 [label="feeds events"];
u2->u11 [style=dashed label="«include»" constraint=false]; u4->u5 [style=dashed label="«extend»" constraint=false]; }}''')

# 3 activity
dot("activity", f'''digraph AC {{ rankdir=TB; {NODE}; nodesep=0.25; ranksep=0.2; node [fontsize=12]; edge [fontsize=11];
s[label="" shape=circle width=0.18 style=filled fillcolor=black]; e[label="" shape=doublecircle width=0.18 style=filled fillcolor=black];
a1[label="Analyst: select scenario, edit fields,\\nset thresholds, press Execute" fillcolor="#FFF3D6"]; a9[label="Analyst: read result,\\nexplanation and recommended actions" fillcolor="#FFF3D6"];
d1[label="Dashboard: build payload from form" fillcolor="#E3F0EA"]; d2[label="Dashboard: show validation errors" fillcolor="#FDE2E2"]; d3[label="Dashboard: render banner, gauge, summary,\\ndrivers; write audit log" fillcolor="#E3F0EA"];
v[label="Payload valid?" shape=diamond fillcolor="#FFFFFF"]; r[label="Run rules, graph lookup,\\nbuild 13 features"]; m[label="ML probabilities\\nrisk = (1 - P(legit)) x 100" fillcolor="{G}"]; ov[label="Rule fired?" shape=diamond fillcolor="#FFFFFF"]; ox[label="Raise score, force class"]; x[label="Explain (try / except), then\\nroute by thresholds"];
s->a1->d1->v; v->d2 [label="no"]; d2->a9; v->r [label="yes"]; r->m->ov; ov->ox [label="yes"]; ov->x [label="no"]; ox->x; x->d3->a9->e; }}''')

# 4 flowchart (decision logic)
dot("flowchart", f'''digraph FL {{ rankdir=TB; {NODE}; nodesep=0.35; ranksep=0.35;
st[label="Payment arrives" shape=oval fillcolor="{G}"]; v[label="Payload valid?" shape=diamond fillcolor="#FFFFFF"]; rej[label="Reject with\\nerror list" fillcolor="#FDE2E2"];
r1[label="amount <= Rs 50 AND\\n>= 3 txns / 60 s ?" shape=diamond fillcolor="#FFFFFF"]; r2[label="new device AND payee changed\\n<= 10 min ago ?" shape=diamond fillcolor="#FFFFFF"];
ml[label="ML: P(each class)\\nscore = (1 - P(legit)) x 100"]; ct[label="class = Card Testing\\nscore = max(score, 90)" fillcolor="#FFF3D6"]; at[label="class = Account Takeover\\nscore = max(score, 85)" fillcolor="#FFF3D6"];
t1[label="score < Allow\\nthreshold (30)?" shape=diamond fillcolor="#FFFFFF"]; t2[label="score > Block\\nthreshold (70)?" shape=diamond fillcolor="#FFFFFF"];
al[label="ALLOW" fillcolor="{G}" shape=oval]; ch[label="CHALLENGE\\n(OTP / 3-D Secure)" fillcolor="#F59E0B" shape=oval]; bl[label="HARD BLOCK" fillcolor="#EF4444" fontcolor=white shape=oval];
st->v; v->rej [label="no"]; v->ml [label="yes"]; ml->r1; r1->ct [label="yes"]; r1->r2 [label="no"]; ct->r2; r2->at [label="yes"]; r2->t1 [label="no"]; at->t1;
t1->al [label="yes"]; t1->t2 [label="no"]; t2->bl [label="yes"]; t2->ch [label="no"]; }}''')

# 5 ER
def ent(n, rows, color="#E3F0EA"):
    body="".join(f'<TR><TD ALIGN="LEFT" PORT="{p}">{t}</TD></TR>' for p,t in rows)
    return f'{n.lower()} [shape=plaintext label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" COLOR="{M}"><TR><TD BGCOLOR="{M}"><FONT COLOR="white"><B>{n}</B></FONT></TD></TR>{body}</TABLE>>];'
dot("er", f'''digraph ER {{ rankdir=TB; nodesep=0.5; ranksep=0.45; graph [{F}]; node [{F} fontsize=10]; edge [{F} fontsize=10 color="#2F4F46"];
{ent("CUSTOMER",[("a","<B>user_id</B> (PK)"),("b","account_age_days"),("c","user_avg_amount")])}
{ent("CARD",[("a","<B>card_id</B> (PK)"),("b","user_id (FK)")])}
{ent("DEVICE",[("a","<B>device_id</B> (PK)")])}
{ent("TRANSACTION",[("a","<B>transaction_id</B> (PK)"),("b","user_id (FK)"),("c","card_id (FK)"),("d","device_id (FK)"),("e","amount"),("f","ip_country, hour"),("g","velocity_1m"),("h","payee_changed_hours"),("i","is_new_device"),("j","timestamp, label")])}
{ent("DECISION",[("a","<B>decision_id</B> (PK)"),("b","transaction_id (FK)"),("c","risk_score"),("d","predicted_class"),("e","route"),("f","latency_ms")])}
{ent("RULE_HIT",[("a","<B>hit_id</B> (PK)"),("b","decision_id (FK)"),("c","rule_name, reason")])}
{ent("DRIVER",[("a","<B>driver_id</B> (PK)"),("b","decision_id (FK)"),("c","feature, impact_pct")])}
{{rank=same; customer; device}} {{rank=same; rule_hit; driver}} customer->card [label=" 1 : N  owns"]; customer->transaction [label=" 1 : N  makes"]; card->transaction [label=" 1 : N  used in"]; device->transaction [label=" 1 : N  used for"];
transaction->decision [label=" 1 : 1  produces"]; decision->rule_hit [label=" 1 : N  triggers"]; decision->driver [label=" 1 : N  explained by"]; }}''')

# 6 class diagram
def cls(n, attrs, meths, fill="#E3F0EA"):
    a="<BR ALIGN=\"LEFT\"/>".join(attrs)+"<BR ALIGN=\"LEFT\"/>" if attrs else ""
    m="<BR ALIGN=\"LEFT\"/>".join(meths)+"<BR ALIGN=\"LEFT\"/>" if meths else ""
    return f'"{n}" [shape=plaintext label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="{M}" BGCOLOR="{fill}"><TR><TD BGCOLOR="{M}"><FONT COLOR="white"><B>{n}</B></FONT></TD></TR><HR/><TR><TD ALIGN="LEFT">{a or " "}</TD></TR><HR/><TR><TD ALIGN="LEFT">{m or " "}</TD></TR></TABLE>>];'
dot("classdiagram", f'''digraph C {{ rankdir=TB; nodesep=0.35; ranksep=0.6; graph [{F}]; node [{F} fontsize=11]; edge [{F} fontsize=10 color="#2F4F46"];
{cls("StreamlitApp",["+ session_state : dict"],["+ tabs : Start / Check / Live / Map / ROI"],"#FFF3D6")}
{cls("FraudShieldEngine",["+ model : HistGradientBoostingClassifier","+ baseline : ndarray","+ graph : GraphEngine"],["+ score(payload, allow_below, block_above) : dict","- _explain(x, p_legit) : list"],"#C9F2E1")}
{cls("StreamSimulator",["+ users : list","+ queue : deque","+ attack_prob : float"],["+ next() : (payload, truth)","- _start_attack() : None"])}
{cls("GraphEngine",["+ G : networkx.Graph"],["+ build(df) : GraphEngine","+ stats(user, card, device) : (int, int)","+ ego_graph(device, radius) : Graph"])}
{cls("validation",["+ ValidationError(errors)"],["+ validate_payload(p) : dict"],"#F2F3F4")}
{cls("rules_engine + features",["+ FEATURES : list[str]"],["+ run_rules(p) : list[dict]","+ build_features(d, du, dc) : list"],"#F2F3F4")}
{cls("roi_calc + narrative",[],["+ compute_roi(volume, ticket, ...) : dict","+ summary(res, p) : str","+ pipeline_steps(res, p, lo, hi) : list"],"#F2F3F4")}
{{rank=same; FraudShieldEngine; StreamSimulator}} {{rank=same; GraphEngine; validation}} {{rank=same; "rules_engine + features"; "roi_calc + narrative"}} GraphEngine->"rules_engine + features" [style=invis]; validation->"roi_calc + narrative" [style=invis]; StreamlitApp->FraudShieldEngine [arrowhead=open label=" calls score()"]; StreamlitApp->StreamSimulator [arrowhead=open label=" pulls events"]; StreamlitApp->"roi_calc + narrative" [arrowhead=open constraint=false];
FraudShieldEngine->GraphEngine [arrowhead=diamond label=" owns"]; FraudShieldEngine->validation [style=dashed arrowhead=open label=" uses"]; FraudShieldEngine->"rules_engine + features" [style=dashed arrowhead=open label=" uses"]; }}''')

# 7 DFD0 and DFD1
dot("dfd0", f'''digraph D0 {{ rankdir=TB; {NODE}; nodesep=0.5; ranksep=0.9; node [fontsize=12]; edge [fontsize=11];
{{rank=same; b; a; c}} {{rank=same; d1; d2; d3}}
a[label="Risk / Compliance\\nOfficer" shape=box style=filled fillcolor="#FFFFFF"]; b[label="Payment source\\n(form or stream\\nsimulator)" shape=box style=filled fillcolor="#FFF3D6"]; c[label="Product Manager" shape=box style=filled fillcolor="#FFFFFF"];
p[label="0\\nFraudShield 2.0\\nReal-time risk engine" shape=circle style=filled fillcolor="{G}" width=1.9 fixedsize=true];
d1[label="D1  Transaction\\nhistory (graph)" shape=cylinder]; d2[label="D2  Trained model" shape=cylinder]; d3[label="D3  Audit log" shape=cylinder];
b->p [label="payment\\npayload"]; a->p [label="scenario,\\nthresholds"]; c->p [label="volume, ticket,\\nfraud profile"]; p->a [label="decision, score,\\nreasons" constraint=false]; p->c [label="monthly benefit" constraint=false];
d1->p [label="known links" dir=back]; d2->p [label="probabilities" dir=back]; p->d3 [label="decision record"]; }}''')


# 8 module dependency
dot("modules", f'''digraph MD {{ rankdir=LR; {NODE}; nodesep=0.22; ranksep=0.7;
app[label="app.py\\n(dashboard)" fillcolor="#FFF3D6"]; tr[label="train_pipeline.py" fillcolor="#FFF3D6"]; te[label="test_engine.py" fillcolor="#FFF3D6"];
mw[label="model_wrapper.py" fillcolor="{G}"]; dg[label="data_gen.py"]; ss[label="stream_sim.py"]; nr[label="narrative.py"]; rc[label="roi_calc.py"]; th[label="theme.py"]; sc[label="scenarios.py"];
va[label="validation.py"]; ru[label="rules_engine.py"]; ge[label="graph_engine.py"]; fe[label="features.py"]; cf[label="config.py\\n(constants)" fillcolor="#E3F0EA"];
app->mw; app->ss; app->nr; app->rc; app->th; app->sc; app->cf; tr->dg; tr->ge; tr->fe; te->mw; mw->va; mw->ru; mw->ge; mw->fe; mw->cf; ru->cf; fe->cf; nr->cf; ss->cf; dg->cf; }}''')

# 9 training pipeline

# 10 feature engineering
dot("features", f'''digraph FE {{ rankdir=LR; {NODE}; nodesep=0.18; ranksep=0.9; node [fontsize=10];
raw[label="Raw payload\\n(amount, user_avg_amount, velocity_1m,\\naccount_age_days, payee_changed_hours,\\nis_new_device, ip_country, hour,\\ndevice/user/card ids)" fillcolor="#FFFFFF"];
subgraph cluster_g {{ label="Derived feature groups (13)"; style="rounded"; color="{M}";
 g1[label="Amount\\namount_log, amount_ratio"]; g2[label="Velocity\\nvelocity_1m, is_micro"]; g3[label="Payee\\npayee_changed_hours,\\nrecent_payee_change"]; g4[label="Device & location\\nis_new_device, ip_mismatch"]; g5[label="Time\\nhour, is_night"]; g6[label="Account\\naccount_age_days"]; g7[label="Network (graph)\\ndevice_user_count,\\ndevice_card_count" fillcolor="{G}"]; }}
vec[label="13-element\\nfeature vector" fillcolor="{G}"]; raw->g1; raw->g2; raw->g3; raw->g4; raw->g5; raw->g6; raw->g7; g1->vec; g2->vec; g3->vec; g4->vec; g5->vec; g6->vec; g7->vec; }}''')

# 11 deployment
dot("deployment", f'''digraph DP {{ rankdir=TB; {NODE}; nodesep=0.4; ranksep=0.5; node [fontsize=12];
subgraph cluster_c {{ label="Client: web browser"; style="rounded,filled"; fillcolor="#F2F3F4"; color="{M}"; b[label="Dashboard UI\\nhttp://localhost:8501"]; }}
subgraph cluster_s {{ label="Developer laptop (Windows / Python 3.x virtual environment)"; style="rounded,filled"; fillcolor="#E8F5EF"; color="{M}";
 st[label="Streamlit server\\n(app.py)" fillcolor="{G}"]; en[label="FraudShieldEngine\\n(in-process Python)"]; fs[label="Project files\\nCSV, model .pkl, metrics .json" shape=cylinder]; }}
b->st [label="HTTP / WebSocket"]; st->en [label="function call"]; en->fs [label="load at start-up"]; }}''')

# 12 navigation map
dot("navmap", f'''digraph NV {{ rankdir=LR; {NODE}; nodesep=0.25; ranksep=0.6;
h[label="Header\\n(logo, title,\\ntheme switch)" fillcolor="#FFFFFF"]; m[label="Top metrics bar\\nlatency, accuracy, count" fillcolor="#FFFFFF"];
t0[label="Start here"]; t1[label="Check a payment" fillcolor="{G}"]; t2[label="Live feed"]; t3[label="Connections map"]; t4[label="Money saved"]; au[label="Audit log (admin)\\nexpander" fillcolor="#FFF3D6"];
h->m; m->t0; m->t1; m->t2; m->t3; m->t4; t1->au [style=dashed]; t2->au [style=dashed]; }}''')
print("graphviz done")
