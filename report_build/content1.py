from lib_docx import *
IMG = "/home/claude/report/img/"
def sub(t): return P(t, jc="left", bold=True, keep=True, before=140, after=60, color="365F91")
def body(t, **k): return P(t, after=140, **k)
def eq(t): return P(t, jc="center", italic=True, after=140, before=60)
REF = dict(bishop=1, esl=2, geron=3, molnar=4, somm=5, han=6, bolton=7, dalp18=8, dalp15=9, xgb=10, lgbm=11, rf=12, fried=13, shap=14, lime=15, skl=16, nx=17, smote=18, abd=19, phua=20, jurg=21, iforest=22, carc=23, gem=24,
           sklw=25, stw=26, nxw=27, plw=28, xgw=29, emv=30, npci=31, rbi=32, bs=33, utq=34, gv=35, pci=36)
def c(*k): return "[" + ", ".join(str(REF[x]) for x in k) + "]"

def build(D, R, T):
    S = {}
    ds, cv, fin = R["dataset"], R["cv"], R["final"]
    # ---------------- front matter ----------------
    S["Certificate"] = D.box("CERTIFICATE", ["[ Insert the signed project certificate here ]", "(Certificate text signed by the project guide, Head of Department and, if required, the external examiner)", "Space reserved: one full page"], height=9000)
    S["Student Declaration"] = D.box("STUDENT DECLARATION", ["[ Insert the student declaration here ]", "(Declaration of originality, with names, roll numbers, signatures and date)", "Space reserved: one full page"], height=7500)
    S["Acknowledgement"] = D.box("ACKNOWLEDGEMENT", ["[ Write the acknowledgement here ]", "(Thanks to the project guide, Head of Department, faculty, institution, family and friends)", "Space reserved: one full page"], height=7500)
    S["Abstract"] = [
        body(f"Digital payments in India now run at a scale of more than twenty billion transactions every month {c('utq')}, and fraud has grown with them. Most open-source fraud projects are offline notebooks that answer a single question, “fraud or not?”, long after the payment has been made. They rarely explain their answers, they ignore the different shapes that fraud takes, and they say nothing about what a wrong decision costs a business."),
        body(f"This project presents **FraudShield 2.0**, a real-time, explainable and multi-class transaction risk engine built entirely in Python. Each payment passes through a five-stage pipeline: strict schema validation, deterministic business rules (card-testing and account-takeover signatures), a NetworkX graph lookup that detects devices shared by many customers, a 13-feature engineering layer, and a class-weighted gradient-boosted classifier that returns a probability for five outcomes: Legitimate, Credit Card Fraud, Account Takeover, APP Scam and Card Testing. The probability of fraud becomes a 0–100 risk score that is routed to **Allow**, **Challenge** (OTP / 3-D Secure) or **Hard Block** using thresholds the user can change. Every decision is accompanied by a local explanation (the top risk drivers), a plain-English summary and a mitigation blueprint."),
        body(f"A Streamlit dashboard with a light/dark theme provides a guided “Check a payment” console, a live simulated payment feed with alerts, a device-connection graph and a business ROI simulator. On a synthetic dataset of {ds['rows']:,} transactions the model reaches a macro F1-score of **{fin['metrics']['f1']:.3f}** on a held-out test set ({cv['mean']:.3f} ± {cv['std']:.3f} in five-fold cross-validation) with a mean end-to-end decision time of **{R['latency']['mean']:.1f} ms** against a 100 ms budget. All 28 functional, validation, rule-boundary and fault-isolation test cases pass."),
        body("The report also records the weaknesses honestly: the data are synthetic, so the scores are optimistic; a rule that needs three payments in a minute can only react from the third payment of a card-testing burst; and the explanation method is a simple one-feature-at-a-time occlusion. The work shows that a small, modular, explainable system can cover the full path from detection to decision to business value, and it leaves a clear road map towards real data, a service API and production-scale deployment."),
        P("**Keywords:** fraud detection, multi-class classification, gradient boosting, explainable AI, business rules engine, graph analysis, risk scoring, Streamlit, UPI, account takeover, APP scam, card testing.", jc="both", after=120, before=120),
    ]
    S["Table of Contents"] = "TOC"; S["List of Figures"] = "LOF"; S["List of Tables"] = "LOT"

    # ---------------- Chapter 1 ----------------
    S["Chapter 1: Introduction"] = [body("This chapter introduces the context of the project, the problem it addresses, the way fraud is handled today and the solution proposed in this work. It then lists the objectives, the scope and the limitations, and explains how the rest of the report is organised.")]
    S["1.1 Background"] = [
        body(f"India has become one of the largest real-time payment markets in the world. According to National Payments Corporation of India (NPCI) data reported in the press, the Unified Payments Interface (UPI) processed about 24 billion transactions worth roughly ₹29 lakh crore in September 2026 alone {c('utq')}, and the full financial year 2025-26 closed with UPI value of about ₹314 trillion {c('bs')}. A system that moves this much money, this fast, through mobile phones and cards is an attractive target. Criminals no longer attack with one stolen card; they use bots, stolen credentials, remote-access scams and social engineering at scale."),
        body("Four attack patterns are especially important for payment platforms, and they are the four patterns that FraudShield 2.0 recognises:"),
    ] + D.bullets([
        "**Credit-card (card-not-present) fraud:** stolen card details are used for an online purchase, usually for a high value, from an unfamiliar device or country.",
        "**Card testing:** bots send many tiny payments, often just a few rupees, to find out whether a stolen card is still active before it is used for a large purchase.",
        "**Account takeover (ATO):** a criminal logs in to a genuine customer’s account from a new device, quickly adds a new beneficiary and moves money out.",
        "**Authorised push payment (APP) scam:** the genuine customer is tricked into sending money to a fraudster. The device and the login are real, so only the behaviour (a large transfer to a brand-new payee) gives the scam away.",
    ]) + [
        body(f"Fraud is not only a loss of money. Merchants pay a fee for every disputed payment (a chargeback), and card networks place merchants whose dispute ratio stays too high into monitoring programmes that carry fines. At the same time, every genuine customer who is wrongly blocked is a lost sale and a damaged relationship. A fraud system therefore has to be judged on two scales at once: how much fraud it stops, and how little it disturbs honest customers. When a payment is stopped, regulators and customers also expect a reason that a human can understand, which a bare “risk = 0.93” does not give."),
    ]
    S["1.2 Problem Statement"] = [
        body("Existing open-source fraud-detection projects and tutorials share several weaknesses that make them unsuitable for a real payment flow:"),
    ] + D.bullets([
        "They run as **offline, batch-processed scripts** that are disconnected from a live request path and give no information about response time, whereas a payment gateway needs a decision within a few tens of milliseconds.",
        "They treat fraud as a **single yes/no label**, so they cannot tell an analyst which kind of attack is happening, and cannot recommend a matching response.",
        "They return a **hard approve/decline** choice. Wrongly declining a genuine customer is costly, but there is no middle option such as asking for an OTP.",
        "They provide **little or no explanation**, so a compliance officer cannot justify a blocked payment during a dispute.",
        "They never connect detection to **money**, so a product manager cannot judge the trade-off between fraud prevented and customer friction.",
    ]) + [
        body("**Problem statement:** to design, build and evaluate a real-time, explainable fraud decision engine that classifies a payment into one of five outcomes, routes it to a graded action within 100 ms, explains the reason in plain language, and quantifies the business value of the result, using only open-source tools and a reproducible synthetic dataset."),
    ]
    S["1.3 Existing Scenario"] = [
        body(f"Fraud teams today combine three layers. The first is a **rule engine** of hand-written thresholds (for example “block if more than three payments are made in a minute”). Rules are fast and easy to audit, but they must be updated by hand and attackers learn to stay just below them {c('bolton')}. The second is a **supervised machine-learning model**, usually a tree ensemble or a neural network, trained on labelled history {c('dalp18')}. Such models find subtle patterns, but most published work and most public datasets are binary and offline. The widely used public credit-card dataset, for example, contains anonymised principal-component features and a single fraud flag, which makes it impossible to build features such as device sharing or payee changes. The third layer is **commercial platforms** from payment networks and specialist vendors. They combine rules, models and consortium data but are closed, expensive and not available for study."),
        body("For a student, researcher or small fintech, the practical result is a gap: there is no small, open, end-to-end example that shows the whole chain from a payment arriving to a decision, an explanation and a business case."),
    ]
    S["1.4 Proposed Solution"] = [
        body("FraudShield 2.0 is an **active decision-orchestration engine**, not a single call to a prediction function. A payment travels through the following stages, each in its own module so that it can be tested and replaced independently:"),
    ] + D.bullets([
        "**Validation** of every field against a strict schema (IDs, amount, country code, velocity) so that bad input is rejected with a clear message.",
        "**Business rules** that fire instantly on two well-known signatures: card testing (three or more payments of ₹50 or less on one card in 60 seconds) and account takeover (a new device within ten minutes of a payee change).",
        "**Graph analysis** with NetworkX that counts how many customers and cards have used the same device, which exposes bots and fraud rings.",
        "**Machine learning** with a class-weighted gradient-boosted classifier that returns a probability for each of five classes; the risk score is 100 × (1 − P(Legitimate)).",
        "**Explainability** through a local occlusion method that names the top three features that pushed the score up, followed by a plain-English summary.",
        "**Routing** to Allow, Challenge or Hard Block using user-adjustable thresholds, with a mitigation blueprint matched to the predicted fraud type.",
        "**Business value** through an ROI simulator that converts detection performance into rupees saved.",
    ]) + [body("A Streamlit dashboard wraps the engine in a guided interface with light and dark themes, a live payment-stream simulator with alerts, a connection graph and the ROI tool, so that a non-expert can see and understand what is happening at every step.")]
    S["1.5 Objectives"] = [body("The project has the following measurable objectives:")] + D.bullets([
        "**O1.** Generate a reproducible synthetic dataset of at least 10,000 transactions with four injected fraud signatures.",
        "**O2.** Train a multi-class classifier that reaches a macro F1-score of at least 90 % (target taken from the Product Requirement Document).",
        "**O3.** Implement a deterministic rules engine for card-testing and account-takeover signatures that runs before the model.",
        "**O4.** Use graph relationships between users, cards and devices as model features.",
        "**O5.** Deliver an end-to-end decision (validation to routing) in 100 ms or less, and keep the decision available if the explanation component fails.",
        "**O6.** Provide an explanation for every flagged payment: top three drivers, a plain-English summary and a mitigation blueprint.",
        "**O7.** Build an interactive dashboard with a live simulated feed, configurable thresholds, a graph view and an ROI calculator.",
        "**O8.** Verify the system with a documented set of functional, validation, boundary, fault-isolation and performance tests, and report limitations honestly.",
    ], ordered=True)
    S["1.6 Scope"] = D.table(["In scope", "Out of scope"], [
        ["Synthetic data generator with four fraud signatures", "Real customer or bank data (privacy and access restrictions)"],
        ["Rules engine, graph analysis, ML classifier, explanations", "Distributed streaming (Kafka, hosted feature stores)"],
        ["Allow / Challenge / Block routing with configurable thresholds", "Live SMS / OTP or 3-D Secure integration (Twilio, bank networks)"],
        ["Streamlit dashboard, live stream simulator, graph view, ROI tool", "Connection to a real UPI / GPay account (not offered to third parties)"],
        ["Automated tests, experiments and written documentation", "Model re-training on live feedback; production monitoring"],
    ], [1, 1], caption="Scope of the project", size=19)
    S["1.7 Limitations"] = [body("The following limitations apply to the work and should be kept in mind when reading the results:")] + D.bullets([
        "**Synthetic data.** The dataset is generated from stated rules, so the classes are cleaner and easier to separate than real fraud. The reported F1-scores are therefore optimistic and should not be quoted as real-world accuracy.",
        "**No live integration.** The “live” feed is produced by a simulator. The engine is ready to be wrapped in a service, but no payment gateway, bank or UPI app is connected.",
        "**Simple explanation method.** Drivers are computed by replacing one feature at a time with a typical legitimate value. This ignores interactions between features and is less rigorous than SHAP values.",
        "**Rule delay.** The card-testing rule needs three payments in 60 seconds, so the first two payments of a burst are not caught by the rule, and the model also misses them in the simulator (Chapter 7).",
        "**Static graph.** The device graph is built once from the training batch; new links are used for the current decision but are not stored.",
        "**Single-machine prototype.** Latency was measured on one machine, in one Python process, without network or database delays.",
    ])
    S["1.8 Organization of Report"] = D.table(["Chapter", "Content"], [
        ["1  Introduction", "Background, problem statement, existing scenario, proposed solution, objectives, scope and limitations."],
        ["2  Literature Survey", "Rule-based, machine-learning, anomaly, sequence, graph and commercial approaches; comparison and research gap."],
        ["3  Requirement Analysis", "Functional and non-functional requirements, hardware and software needs, feasibility and traceability."],
        ["4  System Design", "Architecture, data-flow, modules, use case, activity, flowchart, data design, ER, class and UI design."],
        ["5  Implementation", "Environment, module-wise implementation, algorithms, interfaces, data storage, code snippets, screenshots."],
        ["6  Testing and Validation", "Strategy, 28 test cases and results, bugs found and fixed, performance evaluation."],
        ["7  Results and Discussion", "Outputs, performance analysis, comparison with alternatives, challenges and lessons."],
        ["8  Conclusion", "Summary, objectives achieved and contributions."],
        ["9  Future Scope", "Enhancements, scalability and commercial applications."],
        ["Appendices, AI/ML Chapter", "User manual, installation, dataset and API details; detailed ML methodology, experiments and error analysis."],
    ], [1.1, 3.9], caption="Organisation of the report", size=19)

    # ---------------- Chapter 2 ----------------
    S["Chapter 2: Literature Survey"] = [body("This chapter reviews the main approaches to payment-fraud detection, compares them on the criteria that matter for a real-time decision system, and identifies the gap that FraudShield 2.0 addresses.")]
    S["2.1 Introduction"] = [
        body(f"Statistical fraud detection has a long history. Bolton and Hand’s classic review {c('bolton')} describes the field as the search for observations that depart from normal behaviour under severe class imbalance, strict time limits and costly mistakes. Later surveys {c('abd','phua')} classify techniques into rule-based, supervised, unsupervised and hybrid methods and stress three recurring difficulties: very few fraud examples, concept drift because fraudsters adapt, and the cost asymmetry between a missed fraud and a false alarm. These three difficulties shape every design decision in this project."),
    ]
    S["2.2 Existing Systems"] = [
        P("**Rule-based systems.** Hand-written conditions on amount, velocity, geography or device are the oldest and still the most common layer. Their strength is transparency and speed; their weakness is that thresholds are static, must be tuned by experts, and are easy to probe and evade.", after=140),
        P(f"**Supervised machine learning.** Random forests {c('rf')}, gradient-boosted trees {c('fried','xgb','lgbm')} and neural networks learn a decision boundary from labelled transactions. Dal Pozzolo et al. {c('dalp18')} study how to model realistic fraud streams, including delayed labels and the choice of evaluation metric, and show that plain accuracy is misleading when fraud is rare. Resampling methods such as SMOTE {c('smote')} and probability calibration after undersampling {c('dalp15')} are common ways to handle imbalance; class weighting, used in this project, is a simpler alternative that keeps all real data.", after=140),
        P(f"**Anomaly detection.** When labels are scarce, unsupervised methods such as Isolation Forest {c('iforest')} score how unusual a transaction is. Carcillo et al. {c('carc')} show that combining unsupervised scores with a supervised model can improve results. The weakness is that unusual does not always mean fraudulent, so false alarms are higher.", after=140),
        P(f"**Sequence models.** Jurgovsky et al. {c('jurg')} treat a card’s history as a sequence and apply recurrent networks, which capture behaviour over time but need per-card history stores and are harder to explain and to serve within a tight latency budget.", after=140),
        P(f"**Graph-based methods.** Fraud rings reuse devices, addresses and accounts, so relationship graphs are informative. Liu et al. {c('gem')} apply heterogeneous graph neural networks to malicious-account detection. Simple graph statistics, such as how many customers share a device, give much of the benefit at a fraction of the cost and are used in this project through NetworkX {c('nx')}.", after=140),
        P("**Commercial platforms.** Card networks and specialist vendors sell real-time scoring that mixes rules, models and consortium data and offers dashboards and case management. They are the benchmark for production quality but are closed, so their internal design cannot be studied or reproduced.", after=140),
        P(f"**Explainable AI.** Regulators and customers expect a reason when a payment is refused. Post-hoc explanation methods such as LIME {c('lime')} and SHAP {c('shap')} attribute a prediction to input features; Molnar’s book {c('molnar')} surveys the field. These methods can be expensive per request, which is why this project uses a light occlusion approach that fits inside the latency budget and degrades gracefully if it fails.", after=140),
    ]
    S["2.3 Comparative Analysis"] = D.table(["Approach", "Real-time", "Explainable", "Multi-class", "Needs labels", "Main weakness"], [
        ["Rule engine", "Yes", "High", "By rule", "No", "Static; easy to evade"],
        ["Supervised ML (trees)", "Yes", "Low–medium", "Possible", "Yes", "Labels, imbalance, drift"],
        ["Anomaly detection", "Yes", "Low", "No", "No", "High false alarms"],
        ["Sequence / deep models", "Harder", "Low", "Possible", "Yes", "History store; heavy"],
        ["Graph neural networks", "Harder", "Low", "Possible", "Yes", "Complex to build and serve"],
        ["Commercial platforms", "Yes", "Varies", "Yes", "Mixed", "Closed and costly"],
        ["**FraudShield 2.0**", "**Yes (≈10 ms)**", "**High (drivers + text)**", "**Yes (5 classes)**", "Yes (synthetic)", "Synthetic data; prototype"],
    ], [1.6, 0.9, 1.2, 1.0, 0.9, 1.6], caption="Comparison of fraud-detection approaches", size=17, hl_rows=(6,))
    S["2.3 Comparative Analysis"] += D.table(["Reference", "Year", "Technique", "Contribution", "Limitation for this use case"], [
        ["Bolton & Hand " + c("bolton"), "2002", "Statistical review", "Frames fraud detection problems", "Pre-dates modern ML"],
        ["Breiman " + c("rf"), "2001", "Random forest", "Robust tree ensemble", "Slower inference for large forests"],
        ["Chen & Guestrin " + c("xgb"), "2016", "XGBoost", "Scalable boosted trees", "Not benchmarked here (not installed)"],
        ["Dal Pozzolo et al. " + c("dalp18"), "2018", "Realistic fraud modelling", "Delayed labels, metrics", "Binary, card-only"],
        ["Liu et al. " + c("gem"), "2018", "Graph neural network", "Malicious-account detection", "Heavy for a real-time prototype"],
        ["Jurgovsky et al. " + c("jurg"), "2018", "LSTM sequences", "Uses transaction history", "Needs card history store"],
        ["Lundberg & Lee " + c("shap"), "2017", "SHAP values", "Unified feature attribution", "Costly per request"],
    ], [1.5, 0.5, 1.2, 1.5, 1.7], caption="Selected related work", size=17)
    S["2.4 Research Gap"] = [body("The survey shows strong methods in isolation but a gap at the level of a complete, open, explainable system. The gaps that this work fills are:")] + D.bullets([
        "**Binary labels.** Public datasets and most tutorials predict fraud / not fraud. Few show a model that names the attack type and matches a response to it.",
        "**Detection without decision.** Work stops at a probability. The step from score to a graded action (Allow, Challenge, Block) with configurable thresholds is rarely shown.",
        "**Explanation as an afterthought.** Explanations are usually a separate notebook step, not part of the request path with a fault-tolerant fallback.",
        "**Missing business view.** Detection quality is reported in F1-scores but not in chargeback fees, monitoring-programme fines or customer friction.",
        "**Latency not measured.** Few open projects report end-to-end decision time or break it down by component.",
        "**Hard-to-read systems.** Prototypes rarely include a guided interface that lets a non-expert understand what happened and why.",
    ])
    S["2.5 Summary"] = [body("Rules give speed and transparency, machine learning gives sensitivity, graphs expose coordinated behaviour, and explanations give trust. No single technique is enough, and the cited literature points towards hybrid systems. FraudShield 2.0 therefore combines all four inside one measured, explainable pipeline and wraps them in an interface that a non-specialist can follow.")]

    # ---------------- Chapter 3 ----------------
    S["Chapter 3: Requirement Analysis"] = [body("This chapter states what the system must do and how well it must do it. Requirements FR-1 to FR-5 and NFR-1 to NFR-2 come from the Software Requirements Specification (SRS); the remaining requirements were added during development when the dashboard and live-stream features were designed.")]
    S["3.1 Functional Requirements"] = D.table(["ID", "Requirement", "Source", "Priority"], [
        ["FR-1", "Evaluate each payment against deterministic rules before the ML model: Rule 1 (3+ payments ≤ ₹50 on one card in 60 s → Card Testing) and Rule 2 (new device within 10 min of a payee change → Account Takeover).", "SRS", "High"],
        ["FR-2", "Classify each payment with a multi-class model and output a probability for Legitimate, Credit Card Fraud, Account Takeover, APP Scam and Card Testing.", "SRS", "High"],
        ["FR-3", "Produce an explainable risk output for every calculation using feature-importance or local contribution scores.", "SRS", "High"],
        ["FR-4", "Provide a business ROI engine that turns monthly volume and average ticket size into capital saved (chargeback fees, fines, lost inventory).", "SRS", "Medium"],
        ["FR-5", "Route each payment to Allow, Challenge or Hard Block using thresholds configurable by sliders; return a mitigation blueprint per fraud class.", "SRS", "High"],
        ["FR-6", "Validate every payload against a strict schema and reject invalid data with readable messages.", "SRS (data)", "High"],
        ["FR-7", "Simulate a live payment stream mixing normal traffic and attacks, with alerts for blocked payments.", "Added", "Medium"],
        ["FR-8", "Show a device / card / customer connection graph and highlight shared devices.", "UI spec", "Medium"],
        ["FR-9", "Show a plain-English explanation and a step-by-step “how we got here” trace for each decision.", "Added", "High"],
        ["FR-10", "Keep an audit log of scored payments and allow it to be downloaded as CSV.", "SRS (admin)", "Medium"],
        ["FR-11", "Offer light and dark colour themes and an in-app guide and glossary for beginners.", "Added", "Medium"],
    ], [0.6, 4.6, 0.8, 0.7], caption="Functional requirements", size=18, align=["left", "left", "center", "center"])
    S["3.1 Functional Requirements"] += D.table(["Actor", "Permissions and goals"], [
        ["Risk / Compliance Officer", "Submits payments, adjusts thresholds, reads decisions, explanations and mitigation, inspects device graphs."],
        ["Fintech Product Manager", "Studies the trade-off between fraud prevented and customer friction; uses the ROI simulator and thresholds."],
        ["System Administrator (audit view)", "Views performance and audit logs and downloads the audit CSV."],
        ["Stream Simulator (system actor)", "Generates normal and attack payments for the live feed."],
    ], [1.6, 4.4], caption="System actors", size=18)
    S["3.2 Non-functional Requirements"] = D.table(["ID", "Requirement", "How it is verified"], [
        ["NFR-1", "Latency: the path from ingestion to routing decision completes in ≤ 100 ms (PRD goal: ≤ 80 ms).", "1,000-request benchmark (Section 6.5), test TC-27"],
        ["NFR-2", "Fault isolation: a failure in the explanation subsystem must not block routing.", "Fault-injection test TC-25"],
        ["NFR-3", "Usability: a first-time user can score a payment and understand the result without training.", "Guided Start page, plain-English summaries, tooltips"],
        ["NFR-4", "Accuracy: macro F1-score ≥ 90 % across all classes (PRD target).", "Hold-out test and 5-fold cross-validation"],
        ["NFR-5", "Maintainability: modular code with one responsibility per file and one configuration file.", "Module structure (Chapter 4)"],
        ["NFR-6", "Reproducibility: fixed random seeds; the data, model and results can be regenerated with three commands.", "Appendix B"],
        ["NFR-7", "Privacy: no real personal data is used or stored.", "Synthetic data only"],
        ["NFR-8", "Accessibility: high-contrast light and dark themes; colour is never the only signal (text labels accompany every colour).", "UI review"],
        ["NFR-9", "Portability: runs on a standard laptop (Windows, macOS or Linux) with open-source Python packages.", "Appendix B"],
    ], [0.6, 3.5, 2.0], caption="Non-functional requirements", size=18)
    S["3.3 Hardware Requirements"] = D.table(["Component", "Minimum", "Recommended"], [
        ["Processor", "Dual-core, 2 GHz", "Quad-core, 2.5 GHz or better"],
        ["Memory (RAM)", "4 GB", "8 GB or more"],
        ["Storage", "1 GB free (packages, data, model)", "2 GB free"],
        ["Display", "1366 × 768", "1920 × 1080 (the dashboard uses a wide layout)"],
        ["Network", "Not needed after installation (works offline)", "Broadband for installing packages"],
        ["Graphics card", "Not required", "Not required"],
    ], [1.3, 2.4, 2.4], caption="Hardware requirements", size=19)
    S["3.4 Software Requirements"] = D.table(["Software", "Version used / needed", "Purpose"], [
        ["Operating system", "Windows 10/11, macOS or Linux", "Development and demonstration"],
        ["Python", "3.12 (experiments); 3.10+ supported", "Programming language"],
        ["pandas / NumPy", "3.0 / 2.4 (experiments)", "Data handling and numerical work"],
        ["scikit-learn " + c("skl"), "1.8 (experiments)", "Gradient-boosted classifier, metrics, cross-validation"],
        ["XGBoost " + c("xgw") + " (optional)", "Any recent release", "Used automatically for training if installed"],
        ["NetworkX " + c("nx"), "3.6 (experiments)", "Device / card / user relationship graph"],
        ["Streamlit " + c("stw"), "1.39 or newer", "Web dashboard and live-refresh fragments"],
        ["Plotly " + c("plw"), "Recent 5.x / 6.x", "Gauge, bar, line and network charts"],
        ["Matplotlib, Graphviz " + c("gv"), "Recent", "Figures and diagrams in this report"],
        ["Web browser", "Chrome, Edge, Firefox (current)", "Viewing the dashboard"],
        ["VS Code or any editor", "Any", "Editing source code"],
    ], [1.7, 2.0, 2.4], caption="Software requirements", size=18)
    S["3.5 Feasibility Study"] = D.table(["Aspect", "Assessment", "Verdict"], [
        ["Technical", "All components (pandas, scikit-learn, NetworkX, Streamlit) are mature open-source packages. The measured decision time of about 10 ms is far below the 100 ms budget.", "Feasible"],
        ["Economic", "No licence cost. Development uses a student laptop. The ROI simulator shows that a real deployment could pay for itself quickly under stated assumptions.", "Feasible"],
        ["Operational", "A guided interface, plain-English explanations and a built-in simulator let non-experts operate the system.", "Feasible"],
        ["Schedule", "The five-day plan in the Development Roadmap covers data, training, engine, dashboard and validation; the live stream and UI polishing were added iteratively.", "Feasible"],
        ["Legal / ethical", "Only synthetic data is used, so no personal data is processed. A real deployment would need consent, data-protection compliance and fairness checks.", "Feasible with care"],
    ], [1.1, 4.1, 0.9], caption="Feasibility study", size=18)
    S["3.6 Requirement Specification"] = [body("The table below traces each requirement to the module that implements it and to the test cases that verify it. This traceability shows that every requirement has both an implementation and a check.")] + D.table(["Requirement", "Implemented in", "Verified by"], [
        ["FR-1 Rules", "core/rules_engine.py", "TC-02, TC-03, TC-17 to TC-22"],
        ["FR-2 Classifier", "train_pipeline.py, core/model_wrapper.py", "TC-01 to TC-05, hold-out and cross-validation"],
        ["FR-3 Explanation", "FraudShieldEngine._explain", "TC-25 and driver outputs in Section 7.1"],
        ["FR-4 ROI", "core/roi_calc.py", "Section 7.2 sensitivity analysis"],
        ["FR-5 Routing", "FraudShieldEngine.score, core/config.py", "TC-23, TC-24, threshold sweep"],
        ["FR-6 Validation", "core/validation.py", "TC-06 to TC-16"],
        ["FR-7 Live stream", "core/stream_sim.py, app.py", "Simulation in Section 7.2"],
        ["FR-8 Graph view", "core/graph_engine.py, app.py", "TC-26"],
        ["FR-9 Plain English", "core/narrative.py", "Outputs in Section 7.1"],
        ["NFR-1 Latency", "Whole pipeline", "TC-27, Section 6.5"],
        ["NFR-2 Fault isolation", "try / except in score()", "TC-25"],
    ], [1.5, 2.6, 2.0], caption="Requirement traceability matrix", size=18)
    return S
