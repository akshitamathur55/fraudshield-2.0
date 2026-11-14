"""config.py - ONE place for every setting/constant.
If you ever want to change a threshold or a name, you change it here only."""

# ---- The 5 classes the ML model predicts (number -> name) ----
CLASSES = {0: "Legitimate", 1: "Credit Card Fraud", 2: "Account Takeover",
           3: "APP Scam", 4: "Card Testing"}
CLASS_IDS = {v: k for k, v in CLASSES.items()}

# ---- Routing thresholds on the 0-100 risk score (sliders in the dashboard change these) ----
ALLOW_BELOW = 30      # score <  30        -> ALLOW
BLOCK_ABOVE = 70      # score >  70        -> HARD BLOCK
                      # in between         -> CHALLENGE (3DS / OTP)

# ---- Business-rule constants (SRS FR-1) ----
CARD_TEST_MAX_AMOUNT = 50.0      # rupees
CARD_TEST_MIN_COUNT = 3          # txns inside the window
CARD_TEST_WINDOW_SEC = 60
ATO_WINDOW_HOURS = 10 / 60       # 10 minutes expressed in hours
RULE_OVERRIDE_SCORE = {"Card Testing": 90.0, "Account Takeover": 85.0}

HOME_COUNTRY = "IN"
LATENCY_BUDGET_MS = 100          # NFR-1

# ---- UI colours (UI/UX spec) ----
COLOR_SAFE, COLOR_WARN, COLOR_CRIT = "#10B981", "#F59E0B", "#EF4444"

# ---- Mitigation blueprint per predicted class (SRS FR-5) ----
MITIGATION = {
    "Legitimate": "No action. Let the payment through with zero friction.",
    "Credit Card Fraud": "Block or step-up with 3DS. Verify shipping/billing match, request issuer re-auth, "
                         "add card to watchlist and notify the cardholder.",
    "Account Takeover": "Freeze new-beneficiary payouts, force password reset + device re-verification, "
                        "alert the real user on their trusted channel.",
    "APP Scam": "Show a scam-warning interstitial, add a cooling-off delay on first payments to new payees, "
                "and route to a human agent for a call-back.",
    "Card Testing": "Block the card + device immediately, enable CAPTCHA / rate limit on the checkout endpoint, "
                    "and report the BIN range to the acquirer.",
}

# ---- App icon (browser tab + page title). Change this ONE line to change it everywhere ----
APP_ICON = "🛡️"

# ---- Paths ----
DATA_PATH = "fraud_transactions.csv"
MODEL_PATH = "fraud_detector.pkl"
METRICS_PATH = "training_metrics.json"
