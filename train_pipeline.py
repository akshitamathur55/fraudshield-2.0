
# import json, pickle, numpy as np, pandas as pd
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import f1_score, classification_report, confusion_matrix
# from sklearn.utils.class_weight import compute_sample_weight
# from core.config import *
# from core.features import FEATURES, build_features
# from core.graph_engine import GraphEngine

# def make_model():
#     try:                                   # preferred: XGBoost (if installed)
#         from xgboost import XGBClassifier
#         return "xgboost", XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
#                                         objective="multi:softprob", n_jobs=2, random_state=42)
#     except ImportError:                    # fallback: scikit-learn gradient boosting
#         from sklearn.ensemble import HistGradientBoostingClassifier
#         return "sklearn-hgb", HistGradientBoostingClassifier(max_iter=150, max_depth=5, learning_rate=0.1, random_state=42)

# def main():
#     df = pd.read_csv(DATA_PATH)
#     graph = GraphEngine().build(df)
#     X = np.array([build_features(r, *graph.stats(r["user_id"], r["card_id"], r["device_id"]))
#                   for r in df.to_dict("records")], dtype=float)
#     y = df["label"].values
#     Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
#     name, model = make_model()
#     w = compute_sample_weight("balanced", ytr)          # class weighting fights class imbalance
#     model.fit(Xtr, ytr, sample_weight=w)
#     pred = model.predict(Xte)
#     f1 = f1_score(yte, pred, average="macro")
#     print(f"Model: {name} | Macro F1 = {f1:.4f}")
#     print(classification_report(yte, pred, target_names=list(CLASSES.values()), digits=3))
#     print("Confusion matrix:\n", confusion_matrix(yte, pred))
#     baseline = np.median(X[y == 0], axis=0)             # a 'typical legit' row, used by the explainer
#     with open(MODEL_PATH, "wb") as f:
#         pickle.dump({"model": model, "features": FEATURES, "baseline": baseline, "graph": graph, "name": name}, f)
#     json.dump({"model": name, "macro_f1": f1, "rows": len(df)}, open(METRICS_PATH, "w"))
#     print(f"Saved {MODEL_PATH}  (target F1 >= 0.90: {'PASS' if f1 >= .9 else 'FAIL'})")

# if __name__ == "__main__":
#     main()
"""train_pipeline.py - trains the fraud model.

Training data = the simulated data (fraud_transactions.csv, all 5 classes)
              + the real IEEE-CIS Kaggle data, if its files are found (see core/ieee_loader.py).

Run locally:   python train_pipeline.py
Options:       python train_pipeline.py --ieee-legit 30000 --ieee-fraud 6000     (how many IEEE rows to use)
               python train_pipeline.py --no-ieee                                (simulated data only)
Then commit the new fraud_detector.pkl and training_metrics.json to GitHub so the Streamlit app uses them.
"""
import json, pickle, argparse, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, confusion_matrix, roc_auc_score, precision_score, recall_score
from sklearn.utils.class_weight import compute_sample_weight
from core.config import *
from core.features import FEATURES, build_features
from core.graph_engine import GraphEngine

def make_model():
    try:                                   # preferred: XGBoost (if installed)
        from xgboost import XGBClassifier
        return "xgboost", XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                                        objective="multi:softprob", n_jobs=2, random_state=42)
    except ImportError:                    # fallback: scikit-learn gradient boosting
        from sklearn.ensemble import HistGradientBoostingClassifier
        return "sklearn-hgb", HistGradientBoostingClassifier(max_iter=150, max_depth=5, learning_rate=0.1, random_state=42)

def load_training_data(use_ieee=True, n_legit=30000, n_fraud=6000):
    """Simulated data always; IEEE-CIS rows are added when the Kaggle files are present."""
    df = pd.read_csv(DATA_PATH); df["source"] = "simulated"
    parts, ieee_rows = [df], 0
    if use_ieee:
        from core.ieee_loader import find_ieee_files, load_ieee
        tx, ident = find_ieee_files()
        if tx:
            print(f"IEEE-CIS found: {tx}" + (f" + {ident}" if ident else "  (no identity file - device features will be neutral)"))
            ieee = load_ieee(tx, ident, n_legit=n_legit, n_fraud=n_fraud)
            parts.append(ieee); ieee_rows = len(ieee)
            print(f"Using {ieee_rows:,} IEEE-CIS rows ({int((ieee.label == 1).sum()):,} fraud) + {len(df):,} simulated rows")
        else:
            print("IEEE-CIS files NOT found (looked for train_transaction.csv in data/ieee, data, ieee, .). Training on simulated data only.")
    return pd.concat(parts, ignore_index=True), ieee_rows

def main(use_ieee=True, n_legit=30000, n_fraud=6000):
    df, ieee_rows = load_training_data(use_ieee, n_legit, n_fraud)
    graph = GraphEngine().build(df)
    X = np.array([build_features(r, *graph.stats(r["user_id"], r["card_id"], r["device_id"]))
                  for r in df.to_dict("records")], dtype=float)
    y, src = df["label"].values, df["source"].values
    idx = np.arange(len(df))
    tr, te = train_test_split(idx, test_size=0.2, stratify=df["label"].astype(str) + src, random_state=42)
    name, model = make_model()
    w = compute_sample_weight("balanced", y[tr])          # class weighting fights class imbalance
    model.fit(X[tr], y[tr], sample_weight=w)
    proba = model.predict_proba(X[te]); pred = proba.argmax(axis=1); yte, ste = y[te], src[te]

    f1_all = f1_score(yte, pred, average="macro")
    sim = ste == "simulated"
    f1_sim = f1_score(yte[sim], pred[sim], average="macro")
    print(f"Model: {name} | Macro F1 (all test rows) = {f1_all:.4f} | Macro F1 (simulated rows only) = {f1_sim:.4f}")
    print("\n--- Simulated data (5 classes) ---")
    print(classification_report(yte[sim], pred[sim], target_names=list(CLASSES.values()), digits=3))
    print("Confusion matrix:\n", confusion_matrix(yte[sim], pred[sim]))
    metrics = {"model": name, "macro_f1": f1_all, "simulated_macro_f1": f1_sim, "rows": len(df), "simulated_rows": int((src == "simulated").sum()),
               "ieee_rows": int(ieee_rows)}
    if ieee_rows:
        ie = ste == "ieee"; yb = (yte[ie] != 0).astype(int); pb = (pred[ie] != 0).astype(int)
        metrics.update(ieee_roc_auc=float(roc_auc_score(yb, 1 - proba[ie][:, 0])), ieee_fraud_precision=float(precision_score(yb, pb, zero_division=0)),
                       ieee_fraud_recall=float(recall_score(yb, pb, zero_division=0)))
        print(f"\n--- Real IEEE-CIS data (fraud vs legit, hold-out) ---\nROC-AUC {metrics['ieee_roc_auc']:.3f} | fraud precision {metrics['ieee_fraud_precision']:.3f} | fraud recall {metrics['ieee_fraud_recall']:.3f}")
    # 'typical legit' row for the explainer: taken from the simulated customers, which the demo payments resemble
    baseline = np.median(X[(y == 0) & (src == "simulated")], axis=0)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": model, "features": FEATURES, "baseline": baseline, "graph": graph, "name": name}, f)
    json.dump(metrics, open(METRICS_PATH, "w"))
    print(f"\nSaved {MODEL_PATH} and {METRICS_PATH}  (target macro-F1 >= 0.90 on simulated data: {'PASS' if f1_sim >= .9 else 'FAIL'})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ieee", action="store_true"); ap.add_argument("--ieee-legit", type=int, default=30000); ap.add_argument("--ieee-fraud", type=int, default=6000)
    a = ap.parse_args(); main(not a.no_ieee, a.ieee_legit, a.ieee_fraud)

