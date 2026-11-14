from lib_docx import *
from content1 import sub, body, eq, c, IMG
import sys, os, json
ROOT = "/home/claude/FraudShield2.0"; sys.path.insert(0, ROOT)
def f3(x): return f"{x:.3f}"
def pc(x, d=1): return f"{x:.{d}f} %"

def build(D, R, T):
    S = {}; I = lambda n: IMG + n + ".png"; ds, fin, cv, lat, comp = R["dataset"], R["final"], R["cv"], R["latency"], R["comparison"]
    cwd = os.getcwd(); os.chdir(ROOT)
    from core.model_wrapper import FraudShieldEngine
    from core.scenarios import SCENARIOS
    from core.narrative import summary, reasons
    eng = FraudShieldEngine(); SC = {}
    for k, p in SCENARIOS.items(): SC[k] = (p, eng.score(p))
    os.chdir(cwd)
    npass = sum(t["ok"] for t in T); ncase = len(T)
    # ---------------- Chapter 6 ----------------
    S["Chapter 6: Testing and Validation"] = [body("This chapter describes how the system was verified. All tests in this chapter were executed against the working code, and the results quoted are the recorded outputs of those runs.")]
    S["6.1 Testing Strategy"] = [body(f"Testing followed the usual layered approach for software projects {c('somm')}. Because the engine is a set of small functions behind one interface, most tests call the engine directly with crafted payloads, which makes them fast, repeatable and independent of the browser.")] + D.table(["Level", "What is checked", "Method"], [
        ["Unit / boundary", "Rule thresholds (₹50.00 vs ₹50.01; 0.1666 h vs 0.17 h; 2 vs 3 payments), schema validators", "Crafted payloads, expected rule hits (TC-17 to TC-22, TC-06 to TC-16)"],
        ["Integration", "Validation → rules → graph → features → model → routing works as one chain", "Five demonstration scenarios (TC-01 to TC-05), graph lookup (TC-26)"],
        ["System", "Threshold configuration, repeatability, behaviour when a component fails", "TC-23, TC-24, TC-25, TC-28"],
        ["Performance", "End-to-end latency against the 100 ms budget; time per component", "1,000-request benchmark (TC-27, Section 6.5)"],
        ["Model validation", "Generalisation of the classifier", "20 % hold-out set, five-fold cross-validation, ablations (Chapter 7)"],
        ["Usability", "Whether a new user can understand the result", "Guided Start page, plain-English output, review by the developer (formal user study left as future work)"],
    ], [1.1, 2.7, 2.3], caption="Testing strategy", size=17)
    S["6.2 Test Cases"] = [body(f"{ncase} test cases were written from the requirements. Each case states the input, the expected behaviour (taken from the specification before running) and the category.")] + D.table(["ID", "Category", "Description", "Input", "Expected result"], [[t["id"], t["cat"], t["desc"], t["inp"], t["exp"]] for t in T], [0.55, 0.95, 2.0, 1.55, 1.6], caption="Test cases", size=15)
    S["6.3 Test Results"] = [body(f"All **{npass} of {ncase}** test cases passed. The table records the actual output for each case.")] + D.table(["ID", "Actual result", "Status"], [[t["id"], t["act"], "Pass" if t["ok"] else "FAIL"] for t in T], [0.6, 4.6, 0.8], caption="Test results", size=16, align=["left", "left", "center"]) + [
        body("Several results are worth noting. The validation cases (TC-06 to TC-16) show that every kind of bad input, including values that would silently pass in a naive implementation (a boolean amount, NaN, text numbers), is rejected with a list of errors. The boundary cases show that the rules fire exactly at the stated limits and not beyond them. TC-25 shows that when the explanation module is forced to fail, the engine still returns the correct decision and sets a flag, which is the behaviour required by NFR-2. TC-23 and TC-24 show that the same payment is routed differently when the user moves the thresholds, which confirms that routing is configurable as required by FR-5.")]
    bugs = [
        ["B1", "Explanation drivers showed 0.0 % impact for confidently predicted frauds (probability saturates near 0 or 1).", "Explanation moved to log-odds scale; positive contributions are normalised to a percentage share."],
        ["B2", "`python core/data_gen.py` failed with “No module named core”.", "Scripts are run as modules (`python -m core.data_gen`); documented in Appendix B."],
        ["B3", "Chart helper crashed because a caller passed its own `margin` argument (duplicate keyword).", "Defaults are built first and then updated by the caller’s values."],
        ["B4", "Streamlit warned about the deprecated `use_container_width` option.", "Option removed; full-width buttons are provided by the style sheet."],
        ["B5", "Theme switch could not be clicked: reduced page padding placed it under Streamlit’s invisible fixed header.", "Top padding increased and the empty header area set to ignore clicks."],
        ["B6", "Native toggle was invisible in light mode because its internal markup differs between Streamlit versions.", "Replaced by a self-drawn pill switch built from a button and CSS."],
        ["B7", "An edit accidentally removed the main style sheet block from `theme.py`, leaving the dashboard unstyled.", "Block restored from the last checkpoint; checkpoints are now taken after every stage."],
        ["B8", "First version of the latency histogram showed no bars because the 100 ms marker stretched the axis.", "Axis limited to the data range; the budget is written in the annotation."],
    ]
    S["6.4 Bug Fixes"] = [body("Defects found during development and how they were resolved are listed below. B1–B3 affected the engine and its helpers; B4–B7 affected the dashboard; B8 affected a figure for this report.")] + D.table(["ID", "Problem", "Resolution"], bugs, [0.5, 3.0, 2.6], caption="Defects found and fixed", size=17)
    lc = R["latency_components_ms"]
    S["6.5 Performance Evaluation"] = [body(f"Latency was measured over {lat['n']:,} consecutive requests, cycling through the five demonstration scenarios, after a warm-up pass. The measurement includes validation, rules, graph lookup, feature building, model inference, explanation and routing, and uses a high-resolution timer inside the engine.")] + D.table(["Statistic", "Decision time (ms)", "Budget / target"], [
        ["Mean", f"{lat['mean']:.1f}", "SRS ≤ 100 ms; PRD ≤ 80 ms"], ["Median (p50)", f"{lat['p50']:.1f}", "-"], ["95th percentile", f"{lat['p95']:.1f}", "-"], ["99th percentile", f"{lat['p99']:.1f}", "≤ 100 ms"], ["Maximum", f"{lat['max']:.1f}", "≤ 100 ms"], ["Minimum", f"{lat['min']:.1f}", "-"],
        ["Throughput (single thread, estimate)", f"≈ {1000 / lat['mean']:.0f} decisions per second", "-"],
    ], [2.4, 1.8, 1.9], caption="End-to-end latency over 1,000 requests", size=18, align=["left", "center", "center"]) + D.figure(I("latency"), "Latency distribution and time spent in each component", 5.9) + [
        body(f"The result is clear: model inference ({lc['ML inference']:.1f} ms) and explanation ({lc['Explanation']:.1f} ms) account for almost all of the time, while validation, rules, graph lookup and feature building together take well under 0.1 ms. The explanation costs as much as the prediction because it asks the model to score 14 slightly different rows in one batch. The slowest request ({lat['max']:.1f} ms) is still about five times faster than the 100 ms budget, so the system meets NFR-1 with a large margin. If explanations were produced only for flagged payments, the median time for normal traffic would roughly halve."),
        body(f"The trained model file is about {os.path.getsize(ROOT + '/fraud_detector.pkl') / 1024 / 1024:.1f} MB and loads once at start-up, so it adds no per-request cost.")]

    # ---------------- Chapter 7 ----------------
    rows = []
    for k, (p, r) in SC.items():
        rr = "; ".join(h["rule"] for h in r["rules_triggered"]) or "none"
        dr = ", ".join(d["label"] for d in r["drivers"]) or "none (normal payment)"
        rows.append([k.split(" (")[0], r["predicted_class"], f"{r['risk_score']:.0f}", r["route"], rr, dr])
    S["Chapter 7: Results and Discussion"] = [body("This chapter presents what the system produced, how well it performed on held-out and simulated data, how it compares with simpler alternatives and with the targets in the specifications, and what was learned.")]
    S["7.1 Outputs"] = [body("The five ready-made scenarios were scored with the default thresholds (Allow below 30, Block above 70). Each row shows the predicted class, the risk score, the route, the rules that fired, and the top risk drivers named by the explainer.")] + D.table(["Scenario", "Predicted class", "Risk", "Route", "Rules fired", "Top drivers"], rows, [1.55, 1.1, 0.4, 0.85, 0.85, 1.9], caption="Output for the five demonstration scenarios", size=16) + [
        body("Two of the plain-English summaries produced by the system are reproduced below exactly as a user sees them."),
    ] + D.callout(summary(SC["Launch Card Testing Automated Script Attack"][1] and SC["Launch Card Testing Automated Script Attack"][0], SC["Launch Card Testing Automated Script Attack"][1]).replace("**", "") if False else summary(SC["Launch Card Testing Automated Script Attack"][1], SC["Launch Card Testing Automated Script Attack"][0]).replace("**", ""), label="Card-testing scenario") + D.callout(
        summary(SC["APP Scam (trusted device, big transfer to new payee)"][1], SC["APP Scam (trusted device, big transfer to new payee)"][0]).replace("**", ""), label="APP-scam scenario") + [
        body("The APP-scam example is the most instructive. The device is the customer’s own and nothing in the login looks wrong, so only behaviour exposes it: an amount many times the customer’s usual spend, sent to a payee added a few hours earlier. The explanation names exactly those two reasons, which is what a support agent would need to tell the customer why the payment was paused.")]
    cm = fin["cm"]; rep = fin["report"]; CN = ["Legitimate", "Credit Card Fraud", "Account Takeover", "APP Scam", "Card Testing"]
    S["7.2 Performance Analysis"] = [
        sub("Hold-out test performance"),
        body(f"On the 20 % hold-out set ({ds['test']:,} transactions, never used for training) the model reached an accuracy of {fin['metrics']['acc']:.4f}, a macro precision of {fin['metrics']['prec']:.4f}, a macro recall of {fin['metrics']['rec']:.4f} and a **macro F1-score of {fin['metrics']['f1']:.4f}**, against the 0.90 target. Only {R['errors']['n']} of {ds['test']:,} test payments were classified wrongly."),
    ] + D.figure(I("confusion_matrix"), "Confusion matrix on the hold-out test set", 4.3) + D.table(["Class", "Precision", "Recall", "F1-score", "Support"], [[k, f"{rep[k]['precision']:.3f}", f"{rep[k]['recall']:.3f}", f"{rep[k]['f1-score']:.3f}", f"{int(rep[k]['support'])}"] for k in CN] + [["Macro average", f"{rep['macro avg']['precision']:.3f}", f"{rep['macro avg']['recall']:.3f}", f"{rep['macro avg']['f1-score']:.3f}", f"{int(rep['macro avg']['support'])}"]], [1.8, 1, 1, 1, 1], caption="Per-class test results", size=18, align=["left", "center", "center", "center", "center"], hl_rows=(5,)) + D.figure(I("per_class_metrics"), "Per-class precision, recall and F1-score", 5.4) + [
        body(f"Every Account Takeover, APP Scam and Card Testing payment in the test set was found (recall 1.000). The weakest class is Credit Card Fraud (F1 = {rep['Credit Card Fraud']['f1-score']:.3f}), whose members sometimes look like a legitimate high-value purchase from a known device. Six genuine payments were classified as some fraud type (four of them as Credit Card Fraud), a false-alarm rate of {6 / 2000 * 100:.2f} % on genuine traffic."),
        sub("Cross-validation"),
        body(f"To check that the result does not depend on one lucky split, the model was trained and tested on five stratified folds. The macro F1-scores were " + ", ".join(f3(x) for x in cv["folds"]) + f", giving a mean of **{cv['mean']:.4f}** and a standard deviation of {cv['std']:.4f}. The small spread shows stable behaviour on this dataset."),
        sub("Effect of the routing thresholds"),
        body("Moving the Allow threshold trades missed fraud against customer friction. The curves below were computed from the risk scores of the test set. Because the model is very confident on this clean synthetic data, the curves are flat over a wide range; with real, messier data they would separate and the threshold sliders would matter much more."),
    ] + D.figure(I("threshold_sweep"), "Fraud allowed through and genuine customers flagged versus the Allow threshold", 5.2) + D.table(["Allow / Block", "Fraud allowed", "Fraud blocked", "Genuine challenged", "Genuine blocked"], [[f"{x['allow']} / {x['block']}", pc(x["fraud_allowed"], 2), pc(x["fraud_blocked"], 2), pc(x["legit_challenged"], 2), pc(x["legit_blocked"], 2)] for x in R["combos"]], [1.2, 1.2, 1.2, 1.4, 1.2], caption="Outcome at four threshold settings (test set)", size=18, align=["center"] * 5) + [
        sub("Live-stream simulation"),
        body(f"The engine was also run on {R['stream']['events']:,} simulated stream events (attack scripts started with a probability of 0.15 per event; attacks made up {R['stream']['attack_share']:.0f} % of payments because card-testing bursts contain several payments). The simulator was written separately from the data generator, so this is a harder test than the hold-out set."),
    ] + D.table(["True type", "Payments", "Challenged or blocked", "Hard-blocked", "Correct class"], [[k, f"{v['n']}", pc(v["flagged"]), pc(v["blocked"]), pc(v["correct_class"])] for k, v in R["stream"]["by_class"].items()], [1.6, 0.9, 1.5, 1.2, 1.2], caption="Detection results in the live-stream simulation", size=18, align=["left"] + ["center"] * 4) + D.figure(I("stream_detection"), "Stream results: share flagged per class and card-testing detection by burst position", 5.8) + [
        body(f"Account takeover, APP scam and card-not-present fraud were all stopped, and only {R['stream']['false_alarm_pct']:.2f} % of genuine payments were flagged. Card testing is the exception: {R['stream']['by_class']['Card Testing']['flagged']:.0f} % of its payments were flagged. The right-hand chart explains why: the first two payments of each burst are missed and every payment from the third onwards is caught. The rule needs three payments in a minute, and the model cannot recognise a single tiny payment from a new device as an attack, because genuine small payments exist. This is an honest limit of velocity-based detection, discussed again in Section “Error Analysis”."),
        sub("Business value"),
        body(f"For a merchant processing ₹50 crore a month at an average ticket of ₹1,500, with 2 % fraud, an old system that catches 50 % of fraud and false-positive rates of 2 % (old) and 0.12 % (FraudShield), the ROI calculator estimates a monthly benefit of about ₹{R['roi']['total_monthly_benefit'] / 1e5:.1f} lakh. These figures are assumptions chosen for illustration, not measurements; the chart shows how the benefit grows with the fraud rate."),
    ] + D.figure(I("roi"), "Estimated monthly benefit by source and its sensitivity to fraud rate", 5.8) + D.table(["Source of benefit", "Monthly value (₹ lakh)"], [["Stock not lost to fraud", f"{R['roi']['inventory_loss_avoided'] / 1e5:.1f}"], ["Chargeback fees avoided", f"{R['roi']['chargeback_fees_avoided'] / 1e5:.1f}"], ["Monitoring-programme fine avoided", f"{R['roi']['monitoring_fine_avoided'] / 1e5:.1f}"], ["Fewer false alarms (customer friction)", f"{R['roi']['friction_savings'] / 1e5:.1f}"], ["**Total**", f"**{R['roi']['total_monthly_benefit'] / 1e5:.1f}**"]], [3.6, 2.0], caption="ROI example (illustrative assumptions)", size=18, align=["left", "center"])
    ab = R["ablation"]
    S["7.3 Comparison"] = [body("Table 25 compares the hybrid system with its two parts used alone; Table 26 compares the results with the targets in the project specifications.")] if False else [body("The first table compares the hybrid system with each of its two parts used alone. The second compares the measured results with the targets in the project specifications.")]
    S["7.3 Comparison"] += D.table(["Configuration", "Accuracy", "Macro precision", "Macro recall", "Macro F1"], [[k, f"{v['acc']:.4f}", f"{v['prec']:.4f}", f"{v['rec']:.4f}", f"{v['f1']:.4f}"] for k, v in ab.items()], [2.6, 0.9, 1.0, 1.0, 0.9], caption="Rules only, model only and hybrid (test set)", size=18, align=["left"] + ["center"] * 4) + [
        body(f"The two business rules alone reach a macro F1 of only {ab['Rules only (Rule 1 + Rule 2)']['f1']:.3f}: they never detect card-not-present fraud or APP scams and find only {R['rules_per_class_recall']['Account Takeover'] * 100:.0f} % of account takeovers and {R['rules_per_class_recall']['Card Testing'] * 100:.0f} % of card-testing payments. The model alone reaches {ab['ML model only']['f1']:.3f}. On the test set, adding the rules on top of the model does not change the score, because the model already finds these cases. The rules still earn their place for three reasons: they give a guaranteed, auditable response to two well-defined attack signatures; they fire in microseconds without the model; and they still protect the system if the model is retrained badly or replaced."),
    ] + D.table(["Requirement", "Target", "Achieved", "Met?"], [
        ["Macro F1-score (PRD, NFR-4)", "≥ 90 %", f"{fin['metrics']['f1'] * 100:.1f} % (CV {cv['mean'] * 100:.1f} %)", "Yes"],
        ["Pipeline latency (PRD)", "≤ 80 ms", f"mean {lat['mean']:.1f} ms, p99 {lat['p99']:.1f} ms", "Yes"],
        ["Pipeline latency (SRS NFR-1)", "≤ 100 ms", f"max {lat['max']:.1f} ms", "Yes"],
        ["Fault isolation (NFR-2)", "Decision survives explanation failure", "TC-25 passed", "Yes"],
        ["Fraud classes recognised", "4 fraud types + legitimate", "5 classes, all tested", "Yes"],
        ["Top-3 drivers for flagged payments (PRD story 2)", "Required", "Provided with plain-English text", "Yes"],
        ["Configurable thresholds (FR-5)", "Sliders", "Tested (TC-23, TC-24)", "Yes"],
        ["Card-testing coverage in stream", "All malicious payments", f"{R['stream']['by_class']['Card Testing']['flagged']:.0f} % (first two missed)", "Partly"],
    ], [2.4, 1.5, 1.8, 0.6], caption="Results against specification targets", size=17, align=["left", "left", "left", "center"], hl_rows=(7,)) + [body("Model comparisons with other algorithms (logistic regression, decision tree, random forest) are given in the AI/ML chapter.")]
    S["7.4 Challenges"] = D.bullets([
        "**No real data.** Real payment data are private, so a synthetic generator had to be designed with enough overlap (large genuine purchases, small genuine payments, genuine new devices and foreign IPs) to avoid a trivial problem.",
        "**Class imbalance.** Fraud makes up about 18 % of the generated rows, far more than in reality, but individual classes are still small. Class weights and macro-averaged metrics were needed so that rare classes were not ignored.",
        "**Keeping explanations fast and meaningful.** The first occlusion method gave zero impact for confident predictions; moving to log-odds fixed it, but the explanation still takes as long as the prediction.",
        "**Real-time behaviour in a web framework.** Streamlit re-runs the script on every interaction, so the live feed needed a fragment that refreshes only one region, and state had to be kept in session memory.",
        "**Interface consistency across themes and versions.** Styling Streamlit’s native widgets for light and dark modes proved fragile, which led to the self-drawn switch (Section 6.4).",
        "**Honest evaluation.** Very high scores on synthetic data can mislead. The report therefore adds ablations, a separately written stream simulator and an explicit list of limitations.",
    ])
    S["7.5 Lessons Learned"] = D.bullets([
        "A pipeline of small modules with a single configuration file made every change (new thresholds, new feature, new theme) local and safe.",
        "Using the same feature function for training and serving removes a whole class of silent bugs.",
        "Rules and models complement each other: rules guarantee behaviour on known signatures; models generalise to the rest.",
        "Accuracy is the wrong headline for imbalanced problems; per-class recall, macro-F1 and the cost of false alarms tell the real story.",
        "An explanation that is available for the user to read is as important as the score; plain language matters as much as the method behind it.",
        "Test the failure paths (bad input, failing explainer) as carefully as the success path.",
        "Take a checkpoint before every risky edit; one accidental deletion cost more time than the feature it was meant to improve.",
    ])

    # ---------------- Chapter 8 ----------------
    S["Chapter 8: Conclusion"] = [body("This chapter summarises the work, checks it against the stated objectives and lists its contributions.")]
    S["8.1 Summary"] = [
        body(f"FraudShield 2.0 shows that a compact, open-source system can cover the full path from a payment arriving to a decision, an explanation and a business case. A five-class gradient-boosted model, two deterministic business rules and a device-sharing graph work together inside one pipeline that produced an end-to-end decision in about {lat['mean']:.0f} ms on average. The model scored a macro F1 of {fin['metrics']['f1']:.3f} on a hold-out set and {cv['mean']:.3f} in cross-validation on a synthetic dataset of {ds['rows']:,} transactions, and all {ncase} test cases passed."),
        body("The system goes beyond a classifier. It routes payments to Allow, Challenge or Block with adjustable strictness, names the likely fraud type and recommended response, explains each decision in plain English, monitors itself through an audit log, and translates detection quality into rupees. The dashboard, with a guided Start page, a live simulated feed, a connection graph and light and dark themes, makes these functions understandable to a non-expert."),
        body("The work also records its limits. The data are synthetic, the explanation method is simple, the card-testing rule reacts only from the third payment, and the system has not been connected to any real payment network. These limits define the road map in Chapter 9."),
    ]
    S["8.2 Objectives Achieved"] = D.table(["Objective", "Evidence", "Status"], [
        ["O1 Dataset with four fraud signatures", f"{ds['rows']:,} rows, reproducible with a fixed seed (Appendix E)", "Achieved"],
        ["O2 Macro F1 ≥ 90 %", f"{fin['metrics']['f1'] * 100:.1f} % hold-out; {cv['mean'] * 100:.1f} % cross-validated", "Achieved"],
        ["O3 Rules engine", "Rule 1 and Rule 2 with boundary tests TC-17 to TC-22", "Achieved"],
        ["O4 Graph features", f"Device-sharing counts rank among the top features; removing them lowers macro F1 to {R['feature_ablation']['Without graph features (device sharing)']['f1']:.3f}", "Achieved"],
        ["O5 Decision ≤ 100 ms with fault isolation", f"Max {lat['max']:.1f} ms; TC-25 passed", "Achieved"],
        ["O6 Explanation for every flagged payment", "Top-3 drivers, plain-English summary, mitigation blueprint", "Achieved"],
        ["O7 Interactive dashboard", "Five tabs, live feed, thresholds, graph view, ROI simulator, themes", "Achieved"],
        ["O8 Documented tests and honest limits", f"{ncase} tests, Section 1.7, Section 7.2, Section “Error Analysis”", "Achieved"],
    ], [2.2, 3.1, 0.8], caption="Objectives and evidence", size=17, align=["left", "left", "center"])
    S["8.3 Contributions"] = D.bullets([
        "An **end-to-end, open reference implementation** of a real-time, multi-class, explainable fraud decision engine, with every stage measured.",
        "A **hybrid design** in which deterministic rules can override a probabilistic model and a fault-isolated explanation never blocks the decision.",
        "A **reproducible synthetic data generator** with four injected fraud signatures and deliberate overlap with genuine behaviour.",
        "A **light-weight local explanation method** in log-odds that fits inside the latency budget, plus a plain-English narrative layer.",
        "A **business ROI simulator** that links detection quality to chargeback fees, penalties, inventory and customer friction.",
        "A **beginner-friendly interface** (guide, glossary, step-by-step trace, light and dark themes, live simulator) for demonstration and teaching.",
        "A **transparent evaluation** with ablations, a separately written stream simulator, 28 tests and a candid record of defects and limitations.",
    ])

    # ---------------- Chapter 9 ----------------
    S["Chapter 9: Future Scope"] = [body("The prototype was built to be extended. This chapter outlines the most valuable next steps.")]
    S["9.1 Enhancements"] = D.table(["Area", "Enhancement", "Benefit"], [
        ["Data", "Train and test on real, anonymised transaction data from a partner bank or payment gateway; build the graph from training rows only", "Honest accuracy; removes the synthetic-data caveat"],
        ["Models", "Benchmark XGBoost and LightGBM " + c("xgb", "lgbm") + "; add an anomaly score " + c("iforest") + " for unseen attack types; calibrate probabilities", "Better recall on new attacks; trustworthy scores"],
        ["Card testing", "Count tiny payments per card, device and BIN across a wider window; add device reputation; lower the rule to 2 payments with a soft score", "Catch bursts from the second payment"],
        ["Explainability", "Use SHAP " + c("shap") + " values (batch or approximate) and show them in the same driver chart", "More rigorous, interaction-aware reasons"],
        ["Sequences and graphs", "Per-card history features and graph neural networks " + c("jurg", "gem"), "Detect slow and coordinated fraud"],
        ["Learning loop", "Analyst feedback buttons, delayed-label retraining, drift monitoring dashboard", "Keeps the model current as attackers adapt"],
        ["Service", "FastAPI scoring endpoint, authentication, request logging, gateway webhooks for alerts", "Integration with real payment flows"],
        ["Interface", "Role-based access, case management, multi-language text (Hindi and regional languages)", "Operational usability in India"],
    ], [1.0, 3.3, 1.8], caption="Planned enhancements", size=17)
    S["9.2 Scalability"] = [
        body("A production deployment would split the prototype into independently scalable parts. The scoring service would be stateless and replicated behind a load balancer, with the model loaded once per worker and requests handled concurrently; the measured single-thread throughput of roughly one hundred decisions per second per core suggests that a modest cluster can handle thousands of requests per second, subject to testing. Velocity and graph features would move from request fields and an in-memory graph to a low-latency feature store (for example an in-memory key-value store) updated from a message stream, and the relationship graph would move to a graph database that supports incremental updates."),
        body("To protect the latency budget at scale, explanations could be produced only for challenged or blocked payments (roughly halving the cost for normal traffic), model inference could be batched or compiled, and decisions that exceed a time limit could fall back to the rule-based response, in line with NFR-2. Model files should be stored in a model registry with version control and a safer serialisation format than pickle, and the service must meet payment-security requirements such as PCI DSS " + c("pci") + " and the data-protection rules that apply in India " + c("rbi") + "."),
    ]
    S["9.3 Commercial Applications"] = D.bullets([
        "**Banks and UPI apps:** scoring of transfers and new-payee additions, with scam-warning screens for APP-scam patterns.",
        "**Payment gateways and acquirers:** a pre-authorisation risk call that decides between approval, 3-D Secure " + c("emv") + " step-up and decline.",
        "**E-commerce and marketplaces:** reducing chargebacks and staying below card-network monitoring thresholds.",
        "**Wallets, lending and insurance apps:** account-takeover and synthetic-identity detection at onboarding and payout.",
        "**Software-as-a-service:** a multi-tenant fraud API priced per thousand decisions, with the ROI simulator as a sales and planning tool.",
        "**Education and training:** a safe, offline teaching tool for fraud analysts and data-science students.",
    ])
    return S
