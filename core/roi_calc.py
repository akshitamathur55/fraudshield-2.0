"""roi_calc.py - converts fraud-detection performance into rupees (FR-4)."""
def compute_roi(monthly_volume, avg_ticket, fraud_rate=0.006, legacy_detect=0.60, new_detect=0.92,
                legacy_fpr=0.020, new_fpr=0.0012, chargeback_fee=1250.0, monitor_ratio=0.009,
                monitor_fine=500000.0, cogs_ratio=0.70, friction_cost_per_fp=150.0):
    """All money in rupees. Returns a dict of the numbers the dashboard shows."""
    n = monthly_volume / avg_ticket                       # transactions per month
    fraud_n, legit_n = n * fraud_rate, n * (1 - fraud_rate)
    caught_old, caught_new = fraud_n * legacy_detect, fraud_n * new_detect
    extra_caught = caught_new - caught_old
    missed_old, missed_new = fraud_n - caught_old, fraud_n - caught_new   # each missed one -> chargeback
    # 1) stopped fraud: goods we don't lose (cost of goods) + refund of money is saved through blocking
    fraud_loss_saved = extra_caught * avg_ticket * cogs_ratio + 0  # lost inventory avoided
    # 2) chargeback fees avoided
    fees_saved = (missed_old - missed_new) * chargeback_fee
    # 3) monitoring-programme fine avoided (Visa/MC 0.9% chargeback-to-transaction ratio)
    ratio_old, ratio_new = missed_old / n, missed_new / n
    fine_saved = monitor_fine if (ratio_old >= monitor_ratio and ratio_new < monitor_ratio) else 0.0
    gross = fraud_loss_saved + fees_saved + fine_saved
    # 4) friction: fewer good customers wrongly challenged/blocked
    fp_old, fp_new = legit_n * legacy_fpr, legit_n * new_fpr
    friction_saved = (fp_old - fp_new) * friction_cost_per_fp
    return {"transactions": n, "fraud_txns": fraud_n, "extra_fraud_caught": extra_caught,
            "inventory_loss_avoided": fraud_loss_saved, "chargeback_fees_avoided": fees_saved,
            "monitoring_fine_avoided": fine_saved, "gross_fraud_savings": gross,
            "false_positives_old": fp_old, "false_positives_new": fp_new,
            "friction_savings": friction_saved, "total_monthly_benefit": gross + friction_saved,
            "chargeback_ratio_old_pct": ratio_old * 100, "chargeback_ratio_new_pct": ratio_new * 100}
