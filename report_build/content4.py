from lib_docx import *
from content1 import sub, body, eq, c, IMG
import sys, os, json
ROOT = "/home/claude/FraudShield2.0"; sys.path.insert(0, ROOT)
def f3(x): return f"{x:.3f}"
def refp(n, t): return P(f"[{n}]  {t}", jc="left", left=560, hanging=560, after=100, size=21)

def build(D, R, T):
    S = {}; I = lambda n: IMG + n + ".png"; ds, fin, cv, comp = R["dataset"], R["final"], R["cv"], R["comparison"]
    # ---------------- References ----------------
    S["References"] = [body("Citations in the text use the numbers in square brackets below. Web pages were last accessed in November 2026.")]
    S["Books"] = [refp(1, "C. M. Bishop, ~~Pattern Recognition and Machine Learning~~. New York, NY, USA: Springer, 2006."),
        refp(2, "T. Hastie, R. Tibshirani and J. Friedman, ~~The Elements of Statistical Learning: Data Mining, Inference, and Prediction~~, 2nd ed. New York, NY, USA: Springer, 2009."),
        refp(3, "A. Géron, ~~Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow~~, 3rd ed. Sebastopol, CA, USA: O’Reilly Media, 2022."),
        refp(4, "C. Molnar, ~~Interpretable Machine Learning: A Guide for Making Black Box Models Explainable~~, 2nd ed., 2022. [Online]. Available: https://christophm.github.io/interpretable-ml-book/"),
        refp(5, "I. Sommerville, ~~Software Engineering~~, 10th ed. Harlow, U.K.: Pearson, 2015."),
        refp(6, "J. Han, M. Kamber and J. Pei, ~~Data Mining: Concepts and Techniques~~, 3rd ed. Waltham, MA, USA: Morgan Kaufmann, 2011.")]
    S["Research Papers"] = [
        refp(7, "R. J. Bolton and D. J. Hand, “Statistical fraud detection: A review,” ~~Statistical Science~~, vol. 17, no. 3, pp. 235–255, 2002."),
        refp(8, "A. Dal Pozzolo, G. Boracchi, O. Caelen, C. Alippi and G. Bontempi, “Credit card fraud detection: A realistic modeling and a novel learning strategy,” ~~IEEE Trans. Neural Networks and Learning Systems~~, vol. 29, no. 8, pp. 3784–3797, 2018."),
        refp(9, "A. Dal Pozzolo, O. Caelen, R. A. Johnson and G. Bontempi, “Calibrating probability with undersampling for unbalanced classification,” in ~~Proc. IEEE Symposium Series on Computational Intelligence (SSCI)~~, 2015, pp. 159–166."),
        refp(10, "T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in ~~Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining~~, 2016, pp. 785–794."),
        refp(11, "G. Ke et al., “LightGBM: A highly efficient gradient boosting decision tree,” in ~~Advances in Neural Information Processing Systems 30~~, 2017, pp. 3146–3154."),
        refp(12, "L. Breiman, “Random forests,” ~~Machine Learning~~, vol. 45, no. 1, pp. 5–32, 2001."),
        refp(13, "J. H. Friedman, “Greedy function approximation: A gradient boosting machine,” ~~Annals of Statistics~~, vol. 29, no. 5, pp. 1189–1232, 2001."),
        refp(14, "S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in ~~Advances in Neural Information Processing Systems 30~~, 2017, pp. 4765–4774."),
        refp(15, "M. T. Ribeiro, S. Singh and C. Guestrin, “‘Why should I trust you?’ Explaining the predictions of any classifier,” in ~~Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining~~, 2016, pp. 1135–1144."),
        refp(16, "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” ~~J. Machine Learning Research~~, vol. 12, pp. 2825–2830, 2011."),
        refp(17, "A. A. Hagberg, D. A. Schult and P. J. Swart, “Exploring network structure, dynamics, and function using NetworkX,” in ~~Proc. 7th Python in Science Conf. (SciPy 2008)~~, 2008, pp. 11–15."),
        refp(18, "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, “SMOTE: Synthetic minority over-sampling technique,” ~~J. Artificial Intelligence Research~~, vol. 16, pp. 321–357, 2002."),
        refp(19, "A. Abdallah, M. A. Maarof and A. Zainal, “Fraud detection system: A survey,” ~~J. Network and Computer Applications~~, vol. 68, pp. 90–113, 2016."),
        refp(20, "C. Phua, V. Lee, K. Smith and R. Gayler, “A comprehensive survey of data mining-based fraud detection research,” arXiv:1009.6119, 2010."),
        refp(21, "J. Jurgovsky et al., “Sequence classification for credit-card fraud detection,” ~~Expert Systems with Applications~~, vol. 100, pp. 234–245, 2018."),
        refp(22, "F. T. Liu, K. M. Ting and Z.-H. Zhou, “Isolation forest,” in ~~Proc. 8th IEEE Int. Conf. Data Mining (ICDM)~~, 2008, pp. 413–422."),
        refp(23, "F. Carcillo, Y.-A. Le Borgne, O. Caelen, Y. Kessaci, F. Oblé and G. Bontempi, “Combining unsupervised and supervised learning in credit card fraud detection,” ~~Information Sciences~~, vol. 557, pp. 317–331, 2021."),
        refp(24, "Z. Liu, C. Chen, X. Yang, J. Zhou, X. Li and L. Song, “Heterogeneous graph neural networks for malicious account detection,” in ~~Proc. 27th ACM Int. Conf. Information and Knowledge Management (CIKM)~~, 2018, pp. 2077–2085.")]
    S["Websites"] = [
        refp(25, "scikit-learn developers, “scikit-learn: Machine learning in Python – documentation.” https://scikit-learn.org/stable/"),
        refp(26, "Streamlit Inc., “Streamlit documentation.” https://docs.streamlit.io/"),
        refp(27, "NetworkX developers, “NetworkX documentation.” https://networkx.org/documentation/stable/"),
        refp(28, "Plotly Technologies Inc., “Plotly Python graphing library.” https://plotly.com/python/"),
        refp(29, "XGBoost developers, “XGBoost documentation.” https://xgboost.readthedocs.io/"),
        refp(30, "EMVCo, “EMV 3-D Secure.” https://www.emvco.com/emv-technologies/3-d-secure/"),
        refp(31, "National Payments Corporation of India (NPCI), “Unified Payments Interface (UPI).” https://www.npci.org.in/"),
        refp(32, "Reserve Bank of India, “Reserve Bank of India.” https://www.rbi.org.in/"),
        refp(33, "Business Standard, “UPI transactions scale all-time high of Rs 29.52 trillion in March,” 1 Apr. 2026. https://www.business-standard.com/industry/news/upi-transactions-hit-record-rs-29-52-trillion-in-march-126040101247_1.html"),
        refp(34, "StartupTalky, “UPI daily transactions cross 800 million for the first time: 24.07 billion transactions in September 2026,” 2026. https://startuptalky.com/india-upi-transactions-september-2026/"),
        refp(35, "Graphviz, “Graphviz – graph visualization software.” https://graphviz.org/"),
        refp(36, "PCI Security Standards Council, “Payment Card Industry Data Security Standard (PCI DSS).” https://www.pcisecuritystandards.org/")]

    # ---------------- Appendices ----------------
    S["Appendices"] = [body("The appendices contain the user manual, installation steps, placeholders for source code and repository details, the dataset specification, the interface documentation and (if applicable) internship details.")]
    S["Appendix A: User Manual"] = [body("**Starting the application.** Open a terminal in the project folder and run `streamlit run app.py` (the file name must include `.py`). The dashboard opens in the browser, normally at http://localhost:8501. The first launch trains the model automatically if it does not exist yet.")] + D.table(["Task", "Steps"], [
        ["Switch theme", "Click the pill switch at the top right to change between dark and light mode."],
        ["Learn the basics", "Open **Start here**. Read the three decisions, the five checking steps and the glossary."],
        ["Score a payment", "Open **Check a payment** → choose a ready-made scenario (or “Custom transaction”) → edit any value → move the strictness slider if you wish → press **Execute Scoring Evaluation**."],
        ["Read the result", "Read the banner and the summary first. Then look at the riskometer, the confidence chart, the “How we got here” steps, the risk drivers and the recommended action."],
        ["Test validation", "Enter a negative amount or an invalid card ID and press Execute; a list of errors is shown and nothing is scored."],
        ["Watch the live feed", "Open **Live feed** → press the **Live stream** switch → adjust speed and share of attacks. Rows are coloured by decision; blocked payments raise a pop-up and a blinking banner."],
        ["Inspect connections", "Open **Connections map** → choose a device. Read the verdict card; red devices are shared by three or more customers or cards."],
        ["Estimate money saved", "Open **Money saved** → choose an example business → adjust sliders and fraud levels. The headline shows the monthly saving."],
        ["Export the audit log", "Open the **Audit log** section at the bottom → press **Download audit CSV**."],
    ], [1.3, 4.8], caption="How to use the dashboard", size=18) + D.table(["Problem", "Likely cause and fix"], [
        ["“Streamlit requires raw Python (.py) files”", "The command was typed without the extension. Use `streamlit run app.py`."],
        ["“'streamlit' is not recognized”", "Use `python -m streamlit run app.py`, or activate the virtual environment first."],
        ["Switch or panels look like plain buttons", "Streamlit is too old. Run `pip install -U streamlit` (version 1.39 or newer)."],
        ["Old colours or icon after an edit", "Stop the app (Ctrl+C), start it again and hard-refresh the browser (Ctrl+Shift+R)."],
        ["Model file missing", "Run `python -m core.data_gen` and then `python train_pipeline.py`, or simply start the app."],
        ["Live feed does not move", "Check that the Live stream switch shows ON and that the browser tab is open and active."],
    ], [2.2, 3.9], caption="Troubleshooting", size=18)
    S["Appendix B: Installation Guide"] = [body("The commands below are for Windows (PowerShell or Command Prompt); on macOS or Linux, activate the environment with `source venv/bin/activate`.")] + D.code(
        "cd FraudShield2.0\npython -m venv venv\nvenv\\Scripts\\activate\npip install -r requirements.txt\n\npython -m core.data_gen        # creates fraud_transactions.csv\npython train_pipeline.py       # trains and saves fraud_detector.pkl\npython test_engine.py          # end-to-end smoke test\nstreamlit run app.py           # starts the dashboard") + [
        body("**requirements.txt** lists pandas, numpy, scikit-learn, networkx, streamlit (1.37 or newer; 1.39 or newer recommended for the styled panels and switches), plotly and, optionally, xgboost. If XGBoost is installed it is used for training; otherwise scikit-learn’s histogram gradient boosting is used. Run all scripts from the project folder so that relative paths resolve.")]
    S["Appendix C: Important Source Code"] = [body("Paste the complete listings of the important source files here (monospaced font, 8–9 pt). Suggested files, in order:")] + D.table(["No.", "File", "What it contains"], [
        ["1", "core/config.py", "Constants and configuration"], ["2", "core/validation.py", "Schema validation"], ["3", "core/rules_engine.py", "Business rules"], ["4", "core/graph_engine.py", "Relationship graph"],
        ["5", "core/features.py", "Feature builder"], ["6", "core/model_wrapper.py", "Scoring pipeline and explanation"], ["7", "train_pipeline.py", "Training script"], ["8", "core/data_gen.py", "Synthetic data generator"],
        ["9", "core/stream_sim.py", "Live-stream simulator"], ["10", "core/roi_calc.py", "ROI formulas"], ["11", "app.py", "Streamlit dashboard"],
    ], [0.5, 2.2, 3.4], caption="Source files to include", size=18, align=["center", "left", "left"]) + D.box("Source code listings", ["[ Paste the code listings here ]", "Space reserved: several pages"], height=9000)
    S["Appendix D: GitHub Repository"] = D.table(["Item", "Details (to be filled by the student)"], [["Repository URL", "[ https://github.com/<user>/<repository> ]"], ["Branch / release tag", "[ main / v1.0 ]"], ["Commit used for this report", "[ commit hash ]"], ["README", "[ link to README.md ]"], ["Licence", "[ e.g. MIT ]"]], [1.8, 4.3], caption="Repository details", size=19) + D.box("Repository screenshot or QR code", ["[ Insert a screenshot of the repository page or a QR code here ]"], height=4500)
    S["Appendix E: Dataset Details"] = [body(f"The dataset is generated by `core/data_gen.py` with a fixed random seed (42). It contains {ds['rows']:,} transactions from {ds['users']:,} customers, {ds['cards']:,} cards and {ds['devices']:,} devices. The table lists how each class is generated.")] + D.table(["Class", "Rows", "How the rows are generated"], [
        ["Legitimate", "10,000", "Amount around the customer’s usual spend (log-normal); 3 % large purchases (3–6× usual); 5 % micro payments (₹5–50); 4 % from a new device; 4 % from a foreign IP; 6 % with a recently changed payee; daytime-centred hours"],
        ["Card Testing", "579", "130 bursts of 3–6 payments of ₹1–50 on one card, 3–8 seconds apart; bots reuse devices from a pool of 40; 80 % from a new device; mixed IP countries"],
        ["Account Takeover", "500", "New device (95 %), amount 3–9× usual, payee changed within 10 hours (25 % within 10 minutes), attacker devices re-used (75 %), foreign IP in half"],
        ["APP Scam", "500", "Trusted device and home IP, amount 4–15× usual, payee added 0.2–48 hours earlier, daytime"],
        ["Credit Card Fraud", "600", "Amount 3–12× usual, new device (85 %), foreign IP (80 %), night-time in 60 % of cases"],
    ], [1.3, 0.6, 4.2], caption="Generation rules per class", size=17) + D.table(["Class", "Median amount (₹)", "Mean velocity", "New device", "Foreign IP", "Median payee age (h)"], [
        [k, f"{v['amount_median']:,.0f}", f"{v['vel_mean']:.2f}", f"{v['new_dev'] * 100:.0f} %", f"{v['foreign_ip'] * 100:.0f} %", f"{v['payee_med']:,.1f}"] for k, v in R["desc"].items()
    ], [1.5, 1.1, 0.9, 0.9, 0.9, 1.2], caption="Descriptive statistics by class", size=18, align=["left"] + ["center"] * 5) + [
        body("The `velocity_1m` column is computed after generation as the number of payments on the same card in the preceding 60 seconds (including the current one). The first column of each row in the CSV is a unique transaction ID in the format TXN-00000000.")]
    inp = [["transaction_id", "string", "Yes", "TXN-[0-9]{8}", "TXN-90000002"], ["user_id", "string", "Yes", "USR-[0-9]{6}", "USR-000020"], ["card_id", "string", "Yes", "CRD-[0-9]{12}", "CRD-000000000020"], ["amount", "number", "Yes", "> 0", "12.0"], ["device_id", "string", "Yes", "hex characters", "deadbeefdeadbeef"],
           ["ip_country", "string", "Yes", "two capital letters", "US"], ["velocity_1m", "integer", "Yes", "≥ 0", "5"], ["account_age_days", "integer", "Yes", "≥ 0", "400"], ["payee_changed_hours", "number", "Yes", "≥ 0", "3000.0"], ["is_new_device", "boolean", "No (false)", "true / false", "true"], ["user_avg_amount", "number", "No (= amount)", "> 0", "1500.0"], ["hour", "integer", "No (12)", "0 to 23", "3"]]
    cur = os.getcwd(); os.chdir(ROOT)
    from core.model_wrapper import FraudShieldEngine
    from core.scenarios import SCENARIOS
    eng = FraudShieldEngine(); p = SCENARIOS["Launch Card Testing Automated Script Attack"]; ok = eng.score(p); bad = eng.score(dict(p, amount=-5, card_id="XYZ")); os.chdir(cur)
    okj = {k: ok[k] for k in ("valid", "risk_score", "predicted_class", "route", "probabilities", "rules_triggered", "drivers", "explain_ok", "mitigation", "graph", "latency_ms")}
    okj["drivers"] = [{k: d[k] for k in ("feature", "label", "impact")} for d in ok["drivers"]]
    S["Appendix F: API Documentation"] = [body("The prototype exposes one stable internal interface, the Python call `FraudShieldEngine.score(payload, allow_below=30, block_above=70)`. Its input and output are JSON-compatible dictionaries, so the same contract can be exposed through a web service later.")] + D.table(["Field", "Type", "Required", "Constraint", "Example"], inp, [1.5, 0.8, 0.9, 1.4, 1.5], caption="Input fields", size=16) + [sub("Example request (card-testing burst)")] + D.code(json.dumps(p, indent=1)) + [sub("Output fields")] + D.table(["Field", "Meaning"], [
        ["valid", "False when validation failed; then only `errors` (list of messages) is returned"], ["risk_score", "0–100; 100 × (1 − P(Legitimate)), raised by rule overrides"], ["predicted_class", "One of the five classes"], ["route", "ALLOW, CHALLENGE or HARD BLOCK"],
        ["probabilities", "Probability of each class"], ["rules_triggered", "List of fired rules with name, class and reason"], ["drivers", "Top-3 risk drivers: feature, readable label, percentage impact"], ["explain_ok", "False if the explanation stage failed (decision still valid)"],
        ["mitigation", "Recommended action for the predicted class"], ["graph", "device_user_count and device_card_count"], ["latency_ms", "Time taken by the whole call"],
    ], [1.4, 4.7], caption="Output fields", size=17) + [sub("Example response")] + D.code(json.dumps(okj, indent=1)[:2600].rsplit("\n", 1)[0] + "\n ...") + [sub("Example error response")] + D.code(json.dumps({"valid": False, "errors": bad["errors"]}, indent=1)) + [
        sub("Proposed REST endpoint (design only, not implemented)"),
        body("A service wrapper would expose `POST /v1/score` that accepts the request body above plus optional `allow_below` and `block_above`, returns the response body above with HTTP 200, returns HTTP 422 with the error list when validation fails, and requires an API key. Synchronous scoring before payment capture is the correct place for the decision; gateway webhooks, which arrive after the event, would be used for alerts and case creation."),
    ]
    S["Appendix G: Internship Details (if applicable)"] = D.box("INTERNSHIP DETAILS (if applicable)", ["[ Organisation, duration, mentor, role and summary of work — or write “Not applicable” ]"], height=5200)

    # ---------------- AI/ML Chapter ----------------
    cnt, tc = ds["counts"], ds["test_counts"]
    S["Additional Chapter for AI/ML Projects"] = [body("This chapter documents the machine-learning part of the project in detail: the data, preprocessing, features, model, training set-up, tuning, metrics, experiments, comparison and error analysis.")]
    S["Dataset Description"] = [body(f"The dataset has {ds['rows']:,} rows and 14 columns (Appendix E). After an 80/20 stratified split, {ds['train']:,} rows are used for training and {ds['test']:,} for testing, and every class keeps the same proportion in both parts.")] + D.table(["Class", "Label", "Rows", "Share", "Test rows"], [[k, str(i), f"{cnt[k]:,}", f"{cnt[k] / ds['rows'] * 100:.1f} %", f"{tc[k]}"] for i, k in enumerate(cnt)] + [["Total", "-", f"{ds['rows']:,}", "100 %", f"{ds['test']:,}"]], [1.8, 0.7, 1, 1, 1.1], caption="Class distribution", size=18, align=["left"] + ["center"] * 4, hl_rows=(5,)) + D.figure(I("class_distribution"), "Class distribution of the dataset", 5.6) + [
        body("Legitimate payments are the majority (82 %), and each fraud class is between 4 % and 5 % of the data, so the problem is imbalanced and accuracy alone would be misleading: a model that always answered “legitimate” would score 82 % accuracy and catch no fraud. The classes differ strongly in a few behaviours, shown below."),
    ] + D.figure(I("feature_behaviour"), "Behaviour of each class on four basic measures", 5.6)
    S["Data Collection"] = [body("Real fraud data are confidential and are not shared outside financial institutions, and the public credit-card benchmark has anonymised numeric features that do not contain device, payee or customer-level information. The data were therefore **generated synthetically** with a Python script, using stated rules for each class (Appendix E). The generator was designed with three goals: (1) include the attack signatures described in the specifications; (2) make genuine behaviour overlap with fraud so that the task is not trivial (large genuine purchases, tiny genuine payments, genuine new devices and foreign IPs); and (3) be fully reproducible through a fixed seed. Because the rules are written by the developer, the model can learn them quickly; this is the main reason why the scores are higher than would be expected on real data.")]
    S["Data Preprocessing"] = D.bullets([
        "**Validation.** Incoming payloads pass the strict schema in `validation.py`; the training CSV is produced by the generator and is already consistent.",
        "**Missing values.** None: every field is generated for every row (a real system would need an imputation policy).",
        "**Encoding.** Booleans become 0/1. The country code is converted to an “IP mismatch” flag (1 if not the home country), which avoids a high-cardinality category.",
        "**Scaling.** Not needed for tree-based models. The logistic-regression baseline uses standardisation inside a pipeline.",
        "**Class imbalance.** Handled by balanced sample weights rather than by resampling, so no synthetic rows are added and no real rows are discarded; SMOTE-style oversampling " + c("smote") + " was considered but not needed.",
        "**Splitting.** Stratified 80/20 split with a fixed seed; five-fold stratified cross-validation as a second check.",
        "**Leakage check.** Features use only fields available at decision time. One caveat: device-sharing counts are computed from the whole dataset, including test rows, which mirrors a live system that already holds the same history, but a stricter experiment would build the graph from training rows only. This is listed as a validity threat below.",
    ])
    S["Feature Engineering"] = [body("Thirteen features are built from the raw fields and the graph. The same function builds them in training and in live scoring.")] + D.figure(I("features"), "Feature groups and the 13-element feature vector", 5.0) + D.table(["Feature", "Definition", "Why it matters"], [
        ["amount_log", "ln(1 + amount)", "Scale-free size of the payment"], ["amount_ratio", "amount ÷ customer’s usual amount", "Outsized transfers (APP scam, ATO, card fraud)"], ["velocity_1m", "Payments on the card in 60 s", "Bot bursts (card testing)"], ["account_age_days", "Age of account", "Newer accounts are riskier"],
        ["payee_changed_hours", "Hours since payee change", "ATO and APP scam follow a payee change"], ["recent_payee_change", "1 if ≤ 48 h", "Threshold version of the above"], ["is_new_device", "1 if unrecognised device", "ATO, card fraud"], ["ip_mismatch", "1 if IP country ≠ IN", "Foreign access"],
        ["hour, is_night", "Hour of day; 1 if ≤ 5 a.m.", "Night-time activity"], ["is_micro", "1 if amount ≤ ₹50", "Card-testing signature"], ["device_user_count", "Customers seen on this device", "Bots and fraud rings share devices"], ["device_card_count", "Cards seen on this device", "Same idea at card level"],
    ], [1.5, 2.1, 2.5], caption="The 13 features", size=17)
    S["Model Architecture"] = [body(f"The final classifier is scikit-learn’s histogram-based gradient boosting classifier {c('skl')}, an additive model of shallow decision trees trained one after another {c('fried')}, with a softmax output over the five classes. The trees are grown on binned feature values, which makes training and prediction fast. The code uses XGBoost {c('xgb')} instead if it is installed. The probability of the first class is converted to the risk score, and two business rules can override the class and raise the score. The explanation stage re-uses the same model to score modified copies of the input."),
        body("Why this model: gradient-boosted trees handle mixed numeric and binary features and non-linear interactions (for example “large amount **and** recent payee change”) without scaling, give calibrated-looking probabilities that can be turned into a score, and predict in a few milliseconds. The random forest reached almost the same F1-score but was about {rf_ratio:.0f} times slower per prediction in the comparison below, which matters because the explanation needs many predictions per request.".format(rf_ratio=comp['Random Forest (200 trees)']['lat_ms'] / comp['Gradient Boosting (HGB, final)']['lat_ms']))]
    S["Training Configuration"] = D.table(["Setting", "Value"], [
        ["Algorithm", "HistGradientBoostingClassifier (scikit-learn)"], ["Number of boosting iterations", "150"], ["Maximum tree depth", "5"], ["Learning rate", "0.1"], ["Class handling", "Balanced sample weights (w = N / (K · N_c))"],
        ["Random seed", "42 (data generator, split, model)"], ["Train / test split", f"80 / 20 stratified ({ds['train']:,} / {ds['test']:,})"], ["Cross-validation", "5-fold stratified"], ["Training time", f"{comp['Gradient Boosting (HGB, final)']['fit_s']:.1f} s on one laptop-class CPU"],
        ["Features", "13"], ["Output", "Probabilities for 5 classes; risk score = 100 × (1 − P(Legitimate))"],
    ], [2.2, 3.9], caption="Training configuration", size=18)
    g = sorted(R["grid"], key=lambda x: -x["f1"]); chosen = next(x for x in R["grid"] if x["depth"] == 5 and x["lr"] == 0.1 and x["iters"] == 150)
    S["Hyperparameter Tuning"] = [body(f"A grid of 27 settings (depth 3, 5, 8; learning rate 0.05, 0.1, 0.2; 100, 150 or 300 iterations) was evaluated with three-fold cross-validation on the training data only. The best mean macro-F1 was {g[0]['f1']:.4f} (depth {g[0]['depth']}, learning rate {g[0]['lr']}, {g[0]['iters']} iterations). The configuration used in the system (depth 5, learning rate 0.1, 150 iterations) was fixed before tuning and scored {chosen['f1']:.4f}, a difference of {g[0]['f1'] - chosen['f1']:.4f}, which is negligible, so it was kept.")] + D.figure(I("hyperparameter_grid"), "Cross-validated macro-F1 for the hyper-parameter grid", 5.9) + D.table(["Rank", "Depth", "Learning rate", "Iterations", "Macro F1 (3-fold CV)"], [[str(i + 1), str(x["depth"]), str(x["lr"]), str(x["iters"]), f"{x['f1']:.4f}"] for i, x in enumerate(g[:5])] + [["...", "", "", "", ""]] + [[str(len(g) - 1 + j), str(x["depth"]), str(x["lr"]), str(x["iters"]), f"{x['f1']:.4f}"] for j, x in enumerate(g[-2:])], [0.7, 0.8, 1.2, 1.0, 1.7], caption="Best and worst grid settings", size=18, align=["center"] * 5) + [
        body(f"The grid also shows a weakness: the setting with depth 3 and a learning rate of 0.2 fell to {g[-1]['f1']:.3f}, so very shallow trees with an aggressive learning rate can fail to converge on this weighted problem. A learning rate of 0.1 was stable at every depth.")]
    S["Evaluation Metrics"] = [body("Let TP, FP and FN be the true positives, false positives and false negatives of a class. The metrics are:")] + D.bullets([
        "**Precision** = TP / (TP + FP): of the payments labelled with this class, how many truly belong to it.",
        "**Recall** = TP / (TP + FN): of the payments that truly belong to the class, how many were found.",
        "**F1-score** = 2 · precision · recall / (precision + recall): the harmonic mean of the two.",
        "**Macro F1** = the unweighted mean of the five class F1-scores. Every class counts equally, so rare fraud classes are not hidden by the large legitimate class. This is the headline metric of the specification.",
        "**Accuracy** = correct predictions / all predictions; reported for completeness only.",
        "**Confusion matrix:** a table of actual versus predicted classes that shows which classes are confused.",
        "**Permutation importance:** the drop in macro-F1 when one feature’s values are shuffled; a large drop means the model relies on that feature " + c("molnar") + ".",
    ]) + [body("Textbook definitions can be found in " + c("bishop", "esl", "geron") + ".")]
    S["Experimental Results"] = [body(f"The headline results (macro F1 of {fin['metrics']['f1']:.4f} on the hold-out set and {cv['mean']:.4f} ± {cv['std']:.4f} in cross-validation) and the confusion matrix are given in Section 7.2. Two further experiments explain **why** the model works.")] + [sub("Which features does the model rely on?")] + D.figure(I("feature_importance"), "Permutation feature importance", 5.0) + [
        body("Four features carry almost all the importance: the amount relative to the customer’s usual spend, the hours since the payee changed, the number of customers sharing the device, and the micro-amount flag. These correspond to APP scams and account takeovers, to bot devices, and to card testing. The velocity feature shows zero importance. This is a finding, not a bug: in the training data, card testing is already identified by tiny amounts plus shared bot devices, so the model never needed the velocity count. It is also the root of the card-testing weakness seen in the stream simulation, where each burst used a fresh device."),
        sub("What happens when a feature group is removed?"),
    ] + D.figure(I("ablation"), "Rules vs model vs hybrid, and feature-group ablations (macro F1)", 5.5) + D.table(["Feature group removed", "Macro F1", "Change"], [[k, f"{v['f1']:.4f}", f"{v['f1'] - fin['metrics']['f1']:+.4f}"] for k, v in R["feature_ablation"].items()], [3.6, 1.2, 1.2], caption="Feature-group ablation (test set)", size=18, align=["left", "center", "center"]) + [
        body("Removing the payee-change features causes the largest loss (macro F1 falls to 0.872), then removing the amount features (0.904). Removing the graph features costs 0.009, which confirms that device sharing adds real signal beyond the payload fields (objective O4). Each group matters, and no single feature is a shortcut, since removing any group still leaves a useful model.")]
    S["Model Comparison"] = [body("Four models were trained on the same split. Logistic regression and the decision tree are simple baselines; the random forest and gradient boosting are the two strong candidates. Inference time is the average of 200 single-row predictions.")] + D.table(["Model", "Accuracy", "Macro precision", "Macro recall", "Macro F1", "Training (s)", "Predict 1 row (ms)"], [[k, f"{v['acc']:.4f}", f"{v['prec']:.4f}", f"{v['rec']:.4f}", f"{v['f1']:.4f}", f"{v['fit_s']:.2f}", f"{v['lat_ms']:.2f}"] for k, v in comp.items()], [1.7, 0.8, 0.9, 0.9, 0.8, 0.8, 0.9], caption="Comparison of four classifiers (test set)", size=16, align=["left"] + ["center"] * 6, hl_rows=(3,)) + D.figure(I("model_comparison"), "Macro F1 and inference time of the four models", 5.7) + [
        body(f"All four models exceed the 0.90 target, which again shows how separable the synthetic data are. The random forest and gradient boosting are essentially tied (difference {abs(comp['Random Forest (200 trees)']['f1'] - comp['Gradient Boosting (HGB, final)']['f1']):.4f}, within the noise of a single split). Gradient boosting was chosen because its prediction is several times faster, which leaves room in the 100 ms budget for the explanation stage. Logistic regression and the single tree are the fastest and lose about one to two points of macro F1. XGBoost and LightGBM were not benchmarked here because they were not installed in the experiment environment; they are listed as future work.")]
    ex = R["errors"]["examples"]
    S["Error Analysis"] = [body(f"Only {R['errors']['n']} of {ds['test']:,} test payments were wrong. The table lists the kinds of error.")] + D.table(["Actual → predicted", "Count"], [[k, str(v)] for k, v in R["errors"]["pairs"].items()], [4, 1.2], caption="Misclassifications on the test set", size=18, align=["left", "center"]) + [
        body("The errors share one pattern: the payment sits where genuine behaviour and fraud overlap. For example, a genuine customer made a purchase about five times their usual spend from a foreign IP (a plausible holiday purchase), and the model called it Credit Card Fraud with a high probability. Conversely, two real card-not-present frauds were missed because they came from the customer’s own known device with an amount of only about five to six times the usual spend (one of them from the home country as well), which looks like a normal large purchase. Real attackers behave in the same way, which is why a Challenge route (an OTP) is better than a hard block for medium scores."),
        sub("Weaknesses revealed by the stream simulation"),
        body("The largest weakness is not in the test-set errors but in the stream: the first two payments of every card-testing burst were let through, and only the third and later payments were caught (Section 7.2). Two causes combine. The rule needs three payments in 60 seconds. The model does not use velocity, because in the training data bots re-used devices, whereas in the simulator each burst arrives from a fresh device. The mismatch between training and serving behaviour is a classic risk. Practical remedies are to add card-level and BIN-level tiny-payment counts over a wider window, to lower the rule threshold to two payments with a moderate score instead of a hard override, and to retrain on data that include fresh-device bursts."),
        sub("Threats to validity"),
    ] + D.bullets([
        "**Synthetic data:** class separation is stronger than in reality; scores are an upper bound.",
        "**Graph features built from all rows:** a stricter protocol would build the graph from training rows only.",
        "**Single split and fixed seed:** cross-validation reduces this risk but all data come from one generator.",
        "**Simple explanations:** one-feature-at-a-time occlusion misses interactions; SHAP would be more rigorous.",
        "**Latency measured on one machine:** network, database and concurrency effects are not included.",
        "**No fairness analysis:** a real deployment must check that decisions do not disadvantage groups of customers.",
    ])
    return S
