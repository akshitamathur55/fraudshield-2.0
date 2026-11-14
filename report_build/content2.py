from lib_docx import *
from content1 import sub, body, eq, c, IMG
import os
def build(D, R, T):
    S = {}; ds = R["dataset"]; I = lambda n: IMG + n + ".png"
    # ---------------- Chapter 4 ----------------
    S["Chapter 4: System Design"] = [body("This chapter explains how FraudShield 2.0 is organised. It begins with the architecture and data flow, describes each module, and then presents the standard UML views (use case, activity, flowchart, ER and class diagrams), the data design and the user-interface design.")]
    S["4.1 Architecture"] = [
        body("FraudShield 2.0 uses a layered architecture (Figure below). The **presentation layer** is a Streamlit application with five tabs. It never contains detection logic; it only collects input, calls the engine and draws the result. The **decision engine** is a single Python class, `FraudShieldEngine`, whose `score()` method runs seven stages in a fixed order. The **data layer** holds the training CSV, the trained model file, and the audit log. A **stream simulator** feeds the Live feed tab through the same engine, so the live demonstration and the manual console use exactly the same code path."),
    ] + D.figure(I("architecture"), "Layered architecture of FraudShield 2.0", 5.2) + [
        body("The design follows three principles. First, **separation of concerns**: validation, rules, graph lookup, features, model, explanation and routing are separate modules with narrow interfaces. Second, **fail-safe behaviour**: the explanation stage is wrapped in an exception handler so the core decision is always returned (NFR-2). Third, **one source of truth**: all thresholds, class names and constants live in `core/config.py`, and the same feature function is used in training and in live scoring, which prevents training / serving mismatch."),
        sub("Data flow"),
        body("Figure below shows the context-level data-flow diagram. The system exchanges four kinds of data with the outside world: payment payloads from a payment source, scenario and threshold choices from the officer, business inputs from the product manager, and decisions and benefit figures going back. Three data stores are used: the transaction history (for the graph), the trained model, and the audit log."),
    ] + D.figure(I("dfd0"), "Context-level data-flow diagram (Level 0)", 5.0) + [
        body("The Level-1 diagram expands the single process into seven processes. Rule flags produced by process 2.0 travel to the router (7.0) so that a fired rule can override the model’s class and raise the score."),
    ] + D.figure(I("dfd1"), "Level-1 data-flow diagram", 5.6) + [
        sub("Sequence of a single decision"),
        body("The sequence diagram below follows one payment from the analyst’s click to the rendered result. Messages 3 to 12 happen inside one Python process, so there are no network hops in the prototype."),
    ] + D.figure(I("sequence"), "Sequence diagram of one scoring request", 5.9) + [
        sub("Deployment"),
        body("In the prototype the browser, the Streamlit server and the engine run on one machine. Streamlit calls the engine as an ordinary function, and the model, data and metrics are read from files at start-up. Chapter 9 describes how the same engine can be moved behind a service interface for production."),
    ] + D.figure(I("deployment"), "Deployment view of the prototype", 4.0)
    S["4.2 Module Description"] = D.table(["Module (file)", "Responsibility", "Key functions / classes"], [
        ["core/config.py", "All constants: class names, thresholds, rule parameters, mitigation text, paths, icon", "CLASSES, ALLOW_BELOW, BLOCK_ABOVE, MITIGATION"],
        ["core/validation.py", "Strict schema check of every payload; collects all errors at once", "validate_payload, ValidationError"],
        ["core/rules_engine.py", "Deterministic Card-Testing and Account-Takeover rules", "run_rules"],
        ["core/graph_engine.py", "NetworkX graph of customers, cards and devices; device-sharing counts", "GraphEngine.build / stats / ego_graph"],
        ["core/features.py", "Turns a payload plus graph counts into the 13-element feature vector (shared by training and serving)", "build_features, FEATURES, NICE"],
        ["core/model_wrapper.py", "The full pipeline, explanation and routing", "FraudShieldEngine.score, _explain"],
        ["core/data_gen.py", "Synthetic transaction generator with four fraud signatures", "generate"],
        ["train_pipeline.py", "Builds features, trains and evaluates the model, saves the artefact", "make_model, main"],
        ["core/stream_sim.py", "Live-stream simulator with attack scripts", "StreamSimulator.next"],
        ["core/narrative.py", "Plain-English summary and step-by-step trace", "summary, reasons, pipeline_steps"],
        ["core/roi_calc.py", "Converts detection quality into rupees saved", "compute_roi"],
        ["core/theme.py", "Colour palette, light / dark style sheet, chart layout", "css, plot_layout, THEMES"],
        ["core/scenarios.py", "Five ready-made demonstration payloads", "SCENARIOS"],
        ["app.py", "Streamlit dashboard (five tabs, theme switch, audit log)", "Tabs: Start / Check / Live / Map / ROI"],
        ["test_engine.py", "Local end-to-end smoke test with latency assertion", "script"],
    ], [1.5, 2.9, 1.7], caption="Module description", size=17)
    S["4.2 Module Description"] += D.figure(I("modules"), "Module dependency diagram", 4.6)
    S["4.3 Use Case Diagram"] = [body("Four actors interact with the system. The Risk or Compliance Officer is the main user. The Product Manager works with thresholds and the ROI tool. The System Administrator reads and exports the audit log. The Stream Simulator is a system actor that supplies events to the live feed. Scoring a payment always includes schema validation; reading the plain-English explanation extends the decision view.")] + D.figure(I("usecase"), "Use case diagram", 5.2) + D.table(["Use case", "Actor", "Main flow", "Outcome"], [
        ["UC-1 Score a payment", "Officer", "Choose scenario → edit fields → set thresholds → Execute", "Banner, score, class, explanation, mitigation"],
        ["UC-2 Tune strictness", "Officer, PM", "Move the Allow / Block slider and re-run", "Decision changes; trade-off is visible"],
        ["UC-3 Watch live feed", "Officer, PM", "Start the stream → watch rows, alerts, risk chart", "Real-time view of detection and false alarms"],
        ["UC-4 Inspect connections", "Officer", "Choose a device → read verdict and graph", "Shared devices highlighted in red"],
        ["UC-5 Estimate ROI", "PM", "Pick an example business → adjust sliders", "Monthly benefit and breakdown"],
        ["UC-6 Audit and export", "Administrator", "Open audit log → download CSV", "Record of scored payments"],
    ], [1.3, 0.9, 2.4, 1.6], caption="Use case descriptions", size=17)
    S["4.4 Activity Diagram"] = [body("The activity diagram traces the main workflow from the analyst’s action to the displayed result. It shows the first decision (is the payload valid?), the engine pipeline, the rule override branch and the final rendering and logging.")] + D.figure(I("activity"), "Activity diagram of the scoring workflow", 3.9, max_h=7.4) + [
        body("If validation fails, the dashboard shows the list of errors and no model is called. If it passes, rules, graph lookup and feature building run in order, the model returns probabilities, and a fired rule can raise the score and force the class. The explanation is generated inside an exception handler, so even if it fails the route is still produced.")]
    S["4.5 Flowchart"] = [body("The flowchart gives the exact decision logic. Rules are checked after the model so that they can override its class and enforce a minimum score (90 for Card Testing, 85 for Account Takeover). Thresholds are then applied to the final score.")] + D.figure(I("flowchart"), "Flowchart of the decision logic", 3.9, max_h=7.5) + [
        body("The routing bands on the 0–100 risk scale are shown below together with the score each of the five demonstration scenarios receives."),
    ] + D.figure(I("risk_bands"), "Routing bands and example scenario scores (default thresholds 30 / 70)", 6.0)
    S["4.6 Database Design"] = [
        body("The prototype does not use a database server. Data are kept in four simple stores that are easy to inspect, copy and reproduce. The logical design below is written so that it could be moved to a relational database and a graph store in a production version."),
        sub("(a) Transaction dataset (CSV file)"),
    ] + D.table(["Field", "Type", "Constraint / meaning"], [
        ["transaction_id", "string", "TXN- followed by 8 digits"],
        ["user_id", "string", "USR- followed by 6 digits"],
        ["card_id", "string", "CRD- followed by 12 digits"],
        ["device_id", "string", "Hexadecimal string"],
        ["amount", "float", "Greater than 0 (Rs)"],
        ["user_avg_amount", "float", "Customer’s typical payment; pre-computed baseline (PRD assumption)"],
        ["account_age_days", "integer", "0 or more"],
        ["is_new_device", "0 / 1", "Device not previously seen for this customer"],
        ["ip_country", "string", "ISO 2-letter code (home country is IN)"],
        ["hour", "integer", "0 to 23"],
        ["velocity_1m", "integer", "Payments on the same card in the last 60 s (including this one); 0 or more"],
        ["payee_changed_hours", "float", "Hours since the payee or beneficiary changed; 0 or more"],
        ["timestamp, label", "float, 0–4", "Event time in seconds; class label (0 Legitimate … 4 Card Testing)"],
    ], [1.5, 0.9, 3.7], caption="Schema of the transaction dataset and of an incoming payload", size=18) + [
        sub("(b) Other data stores"),
    ] + D.table(["Store", "Technology", "Contents"], [
        ["Trained model artefact", "Python pickle file (fraud_detector.pkl)", "Fitted classifier, feature names, baseline “typical legitimate” row, relationship graph"],
        ["Training metrics", "JSON file", "Model name, macro F1-score, number of rows"],
        ["Relationship graph", "NetworkX graph in memory", f"{ds['graph_nodes']:,} nodes (customers, cards, devices) and {ds['graph_edges']:,} edges"],
        ["Audit log", "Session memory, exportable to CSV", "Time, payment ID, amount, predicted class, risk score, route, latency"],
    ], [1.5, 2.0, 2.6], caption="Other data stores", size=18)
    S["4.7 ER Diagram"] = [body("The ER diagram shows the logical data model. A customer owns cards and makes transactions; a card and a device are each used in many transactions; every transaction produces exactly one decision, which may trigger several rule hits and is explained by several drivers (the top risk features). In the prototype the Customer, Card and Device entities are columns of the dataset, and the Decision, Rule-hit and Driver entities exist as the fields of a result and of the audit log.")] + D.figure(I("er"), "Entity-relationship diagram (logical model)", 3.7, max_h=7.5)
    S["4.8 Class Diagram"] = [body("The class diagram shows the main classes and modules. `FraudShieldEngine` is the central class: it owns a `GraphEngine` and a trained model and calls the validation, rules and feature modules. The Streamlit application depends on the engine, the stream simulator, the ROI calculator and the narrative module.")] + D.figure(I("classdiagram"), "Class diagram", 5.9, max_h=6.2) + D.table(["Class / module", "Responsibility"], [
        ["FraudShieldEngine", "Runs the pipeline: validate, rules, graph, features, predict, override, explain, route"],
        ["GraphEngine", "Builds the relationship graph and answers “how many customers and cards use this device?”"],
        ["StreamSimulator", "Creates a mix of normal payments and multi-payment attack scripts"],
        ["validation", "Checks the schema and raises a ValidationError listing all problems"],
        ["rules_engine + features", "Deterministic rules and the shared feature-building function"],
        ["roi_calc + narrative", "Money calculation and plain-English text generation"],
    ], [1.7, 4.4], caption="Class responsibilities", size=18)
    S["4.9 UI Design"] = [
        body("The interface was designed for two groups at once: experts who need numbers and traces, and beginners who need explanations. The principles are: (1) **guide first** – a Start page explains decisions, steps and vocabulary; (2) **plain language** – every result begins with a sentence a non-expert can read; (3) **progressive detail** – technical field names appear in tooltips and expanders, not in the main view; (4) **colour with meaning** – green, amber and red are used only for Allow, Challenge and Block, and every colour is paired with a text label; (5) **both themes** – a light and a dark theme share one palette and one style sheet."),
        sub("Navigation and screens"),
    ] + D.figure(I("navmap"), "Navigation map of the dashboard", 4.6) + D.table(["Tab", "Purpose", "Main elements"], [
        ["Start here", "Orientation for first-time users", "Decision cards, 5-step process, fraud types, 3-step guide, glossary"],
        ["Check a payment", "Score one payment and understand the result", "Scenario list, field form, strictness slider, banner, summary, riskometer, confidence chart, trace, drivers, action card"],
        ["Live feed", "Watch the engine on a simulated stream", "Start switch, speed and attack-share sliders, colour-coded table, alert banner, risk chart, alert cards"],
        ["Connections map", "See shared devices and possible fraud rings", "Device selector, verdict card, network graph with red hubs"],
        ["Money saved", "Show business value", "Example businesses, sliders, benefit headline, four metric cards, breakdown chart"],
    ], [1.2, 1.8, 3.1], caption="Dashboard screens", size=18) + [
        sub("Wireframes"),
    ] + D.figure(I("wire_check"), "Wireframe of the “Check a payment” screen", 5.6) + D.figure(I("wire_live"), "Wireframe of the “Live feed” screen", 5.6) + [
        sub("Colour palette and typography"),
        body("The palette is a dark-green family (Rich Black, Dark Green, Bangladesh Green, Mountain Meadow, Caribbean Green and Anti-Flash White). Dark mode uses the dark greens for backgrounds and Caribbean Green as the accent; light mode uses Anti-Flash White for the page and Bangladesh Green as the accent, which keeps text contrast high. Amber and red are added because a single-hue palette cannot express warning and danger. Text uses the Inter typeface with system sans-serif fall-backs, chosen for easy scanning of numbers."),
    ] + D.figure(I("palette"), "Colour palette used in the interface", 5.6)

    # ---------------- Chapter 5 ----------------
    sz = lambda f: os.path.getsize("/home/claude/FraudShield2.0/" + f)
    S["Chapter 5: Implementation"] = [body("This chapter describes how the design was implemented: the development environment, the logic of each module, the main algorithms, the interfaces, the way data are stored, and placeholders for the code listings and screenshots that the student adds from the working project.")]
    S["5.1 Development Environment"] = D.table(["Item", "Details"], [
        ["Language", "Python 3 (3.12 used for the experiments in this report)"],
        ["Editor", "Visual Studio Code or any text editor"],
        ["Environment", "Python virtual environment with packages from requirements.txt"],
        ["Run commands", "python -m core.data_gen → python train_pipeline.py → python test_engine.py → streamlit run app.py"],
        ["Version control", "Git (repository link in Appendix D)"],
        ["Report tools", "Matplotlib and Graphviz for figures; Word for the document"],
    ], [1.3, 4.8], caption="Development environment", size=18) + [sub("Project directory structure")] + D.code(
        "FraudShield2.0/\n├── core/\n│   ├── config.py          constants, thresholds, mitigation text\n│   ├── validation.py      strict schema validation\n│   ├── rules_engine.py    card-testing and ATO rules\n│   ├── graph_engine.py    NetworkX relationship graph\n│   ├── features.py        13-feature builder (shared)\n│   ├── model_wrapper.py   FraudShieldEngine.score()\n│   ├── data_gen.py        synthetic data generator\n│   ├── stream_sim.py      live-stream simulator\n│   ├── narrative.py       plain-English explanations\n│   ├── roi_calc.py        ROI formulas\n│   ├── theme.py           palette, light/dark CSS\n│   └── scenarios.py       demo payloads\n├── app.py                 Streamlit dashboard\n├── train_pipeline.py      training script\n├── test_engine.py         end-to-end test\n├── fraud_transactions.csv generated dataset\n├── fraud_detector.pkl     trained model artefact\n├── training_metrics.json  macro-F1 record\n└── requirements.txt")
    S["5.2 Module-wise Implementation"] = [
        P("**Configuration (config.py).** Holds the class dictionary (0 Legitimate to 4 Card Testing), the default thresholds (30 and 70), the rule constants (₹50, 3 payments, 60 s, 10 minutes), the score floors for rule overrides (90 and 85), the colours, the mitigation blueprint text for every class, the icon and the file paths. Changing behaviour means editing one file.", after=140),
        P("**Validation (validation.py).** Each field is matched against a regular expression or numeric rule from the SRS. The function does not stop at the first error; it collects every problem and raises one exception, so the user sees the whole list. Boolean values are rejected where numbers are expected, and NaN is rejected, because both pass naive numeric checks. Helper fields (`is_new_device`, `user_avg_amount`, `hour`) receive safe defaults.", after=140),
        P("**Rules (rules_engine.py).** Rule 1 fires when the amount is at most ₹50 and `velocity_1m` is at least 3. Rule 2 fires when the device is new and the payee changed within ten minutes (0.1667 h). Each hit returns a rule name, a class and a readable reason. The rules use only fields of the current payload, so they cost microseconds.", after=140),
        P(f"**Graph (graph_engine.py).** Every historical transaction adds three edges (customer–device, card–device, customer–card) to a NetworkX graph ({ds['graph_nodes']:,} nodes, {ds['graph_edges']:,} edges). For a new payment the engine counts the distinct customers and cards already linked to the device and adds the current ones, giving `device_user_count` and `device_card_count`. A neighbourhood of a device can be extracted for the graph view.", after=140),
        P("**Features (features.py).** Converts the payload and the two graph counts into 13 numbers (Table in Section “Feature Engineering”). Because training and live scoring call the same function, a feature can never be computed differently in the two places.", after=140),
        P("**Engine (model_wrapper.py).** `FraudShieldEngine.score()` runs: validate → rules → graph counts → features → model probabilities → rule override → explanation → routing, and measures its own elapsed time with a high-resolution clock. Invalid input returns a structured error result instead of raising. The explanation call is wrapped in `try / except`.", after=140),
        P("**Training (train_pipeline.py).** Loads the CSV, builds the graph and the feature matrix, makes a stratified 80/20 split, computes balanced sample weights, fits the classifier (XGBoost if installed, otherwise scikit-learn’s histogram gradient boosting), prints macro-F1 and the confusion matrix, and saves the artefact.", after=140),
        P("**Stream simulator (stream_sim.py).** Draws customers from the dataset. With a configurable probability it starts an attack script: a 4–6 payment card-testing burst with climbing velocity, an account takeover, an APP scam or card-not-present fraud. Each event is returned with a hidden “truth” label used only for the live scoreboard.", after=140),
        P("**Narrative (narrative.py).** Maps each feature to a sentence template (for example “the payee was changed only 0.1 hours ago”), builds the summary paragraph, and produces the five-step “how we got here” trace.", after=140),
        P("**Dashboard (app.py, theme.py).** Five tabs, a self-drawn pill switch for the theme, a keyed card layout, Plotly charts that follow the active theme, and a Streamlit fragment that refreshes the live feed at a set interval without reloading the page.", after=140),
    ]
    S["5.3 Algorithms"] = [
        sub("Algorithm 1: scoring a payment"),
    ] + D.code("INPUT : payload p, thresholds (a, b)\n1  p' <- validate(p); if errors: return errors\n2  hits <- run_rules(p')\n3  (du, dc) <- graph.stats(user, card, device)\n4  x <- build_features(p', du, dc)            # 13 numbers\n5  probs <- model.predict_proba(x)             # 5 classes\n6  score <- 100 * (1 - probs[Legitimate]); class <- argmax(probs)\n7  for each hit in hits: class <- hit.class; score <- max(score, floor[hit.class])\n8  try: drivers <- explain(x)  except: drivers <- []   # fault isolation\n9  route <- ALLOW if score < a; HARD BLOCK if score > b; else CHALLENGE\n10 return score, class, route, drivers, mitigation[class], latency") + [
        sub("Algorithm 2: gradient-boosted trees with class weights"),
        body(f"The classifier is an additive model of decision trees {c('fried')}. Starting from a constant, each new tree is fitted to the negative gradient of the multi-class log-loss of the current model, and added with a small learning rate. The prediction for class k is a softmax of the summed tree outputs:"),
        eq("P(y = k | x) = exp(F_k(x)) / Σ_j exp(F_j(x)),   F_k(x) = F_k⁰ + η · Σ_m h_{k,m}(x)"),
        body("Because fraud classes are rare, each training row receives a weight inversely proportional to the frequency of its class (the “balanced” heuristic), so that mistakes on the rare classes cost as much in total as mistakes on the common class:"),
        eq("w_c = N / (K · N_c)     (N rows, K = 5 classes, N_c rows of class c)"),
        sub("Algorithm 3: risk score and routing"),
        eq("risk = 100 × (1 − P(Legitimate));   rule override: risk ← max(risk, 90 or 85)"),
        sub("Algorithm 4: local explanation by occlusion in log-odds"),
        body("For a payment with feature vector x, the explainer builds one copy of x for each feature, replacing that feature with the median value of legitimate training rows. It scores all copies in one batch. The risk log-odds is L(x) = ln[(1 − P₀) / P₀], where P₀ is the probability of Legitimate. The contribution of feature j is the drop in risk log-odds when that feature is neutralised; positive contributions are normalised to a percentage share and the top three are shown:"),
        eq("c_j = L(x) − L(x with feature j replaced by its legitimate median)"),
        body("The log-odds scale is used because probabilities saturate near 0 and 1 for confident predictions, which would make every contribution look like zero on the probability scale (an issue found during development, see Section 6.4)."),
        sub("Algorithm 5: ROI estimate"),
        body("With monthly volume V and average ticket t, the number of transactions is n = V / t and the number of fraudulent ones is n·f. If the old system detects a share d₀ and FraudShield a share d₁, the extra fraud caught is n·f·(d₁ − d₀). The savings are the sum of: lost inventory avoided (extra fraud caught × t × cost-of-goods ratio), chargeback fees avoided (extra frauds caught × fee), a monitoring-programme fine avoided if the old chargeback ratio was at or above 0.9 % and the new one is below it, and friction saved (fewer genuine customers wrongly flagged × cost per false positive)."),
    ]
    S["5.4 API Integration"] = [
        body("**Third-party APIs.** The prototype does not call any external API. In particular it is **not** connected to GPay, UPI or any bank: personal payment-app data is not offered to third-party applications, and the project specification excludes live payment and OTP integrations. The “live” feed is produced by an internal simulator, which keeps the demonstration safe, offline and repeatable."),
        body("**Internal interface.** The stable interface of the system is the Python call `FraudShieldEngine.score(payload, allow_below, block_above)`, which accepts a dictionary and returns a dictionary. Appendix F documents the input and output fields in full. Because the interface is a plain function with JSON-compatible data, it can be placed behind a web service without changing the engine."),
        body("**Proposed service integration (not implemented).** In a production setting a payment gateway would call a scoring endpoint before capturing the payment, receive the decision, and apply it (allow, trigger OTP / 3-D Secure {0}, or decline). Gateway webhooks, which arrive after a payment event, suit alerting and case creation but cannot block a payment, so the synchronous call is the right place for the decision. Chapter 9 describes this design.".format(c("emv"))),
    ]
    S["5.5 Database Implementation"] = D.table(["Artefact", "Format", "Size on disk", "How it is created"], [
        ["fraud_transactions.csv", "CSV, 14 columns", f"{sz('fraud_transactions.csv')/1024/1024:.2f} MB ({ds['rows']:,} rows)", "python -m core.data_gen"],
        ["fraud_detector.pkl", "Pickle", f"{sz('fraud_detector.pkl')/1024/1024:.2f} MB", "python train_pipeline.py"],
        ["training_metrics.json", "JSON", f"{sz('training_metrics.json')} bytes", "python train_pipeline.py"],
        ["audit_log.csv", "CSV (download)", "Grows with use", "Download button in the dashboard"],
    ], [1.6, 1.2, 1.9, 1.4], caption="Stored artefacts", size=18) + [
        body("The relationship graph is rebuilt in memory from the CSV when the model is loaded (the graph is also stored inside the pickle file). Session state in Streamlit keeps the audit log and the live-feed rows while the browser tab is open. Because pickle files can execute code when loaded, the model file must only be loaded from a trusted source; a production system would use a safer model format and a managed model registry."),
    ]
    code_items = [("validate_payload()", "core/validation.py"), ("run_rules()", "core/rules_engine.py"), ("build_features()", "core/features.py"), ("FraudShieldEngine.score()", "core/model_wrapper.py"), ("FraudShieldEngine._explain()", "core/model_wrapper.py"), ("train_pipeline.main()", "train_pipeline.py")]
    cs = [body("Insert the following short code snippets from the project into the boxes below (use a monospaced font, 9–10 pt). Each snippet should be short enough to explain in a few lines.")]
    for k, (fn, fl) in enumerate(code_items, 1):
        cs += D.box(f"Code Snippet {k}: {fn}", [f"File: {fl}", "[ Paste the code here ]"], height=3300)
    S["5.6 Code Snippets"] = cs
    shots = [("Start here tab (dark mode)", "Shows the guide, the three decisions and the five steps."), ("Check a payment: normal purchase", "Scenario “Normal everyday purchase” → APPROVED."), ("Check a payment: card-testing attack", "Banner, summary, riskometer and “how we got here” trace."),
             ("Check a payment: account takeover", "Rule R2 triggered; drivers chart and action card."), ("Check a payment: invalid input", "Negative amount rejected by validation, with error list."), ("Live feed running", "Colour-coded table, alert banner, risk chart and alert cards."),
             ("Connections map", "Device verdict card and network graph with red hub devices."), ("Money saved (ROI)", "Headline saving, four metric cards and breakdown chart."), ("Light mode", "Any tab shown in light theme, with the theme switch visible."), ("Audit log", "Audit table and the download button.")]
    ss_ = [body("Insert a screenshot of the running application in each box below, then replace the placeholder text. Take screenshots at full browser width and keep them readable at the page width.")]
    for t, d in shots:
        ss_ += D.box("[ Screenshot ]", [d], height=3600, fill="FAFAFA") + [D.caption("Figure", f"Screenshot: {t}", keep=False)]
    S["5.7 Screenshots"] = ss_
    return S
