"""stream_sim.py - fake 'live payment feed'. Each call to next() returns ONE transaction, like a gateway event.
Mostly normal payments, sometimes it starts an attack 'script' that emits several linked transactions."""
import random
from collections import deque
import pandas as pd
from core.config import DATA_PATH, MITIGATION

def _hex(r, n=16): return "".join(r.choice("0123456789abcdef") for _ in range(n))

class StreamSimulator:
    def __init__(self, csv=DATA_PATH, seed=None, attack_prob=0.15):
        df = pd.read_csv(csv)
        base = df[(df.label == 0) & (df.is_new_device == 0)].drop_duplicates("user_id")   # real-looking customers
        self.users = base.to_dict("records")
        self.r = random.Random(seed)
        self.queue = deque()          # pending transactions of the attack currently in progress
        self.n = 80_000_000           # transaction counter
        self.attack_prob = attack_prob

    def _payload(self, u, **kw):
        self.n += 1
        p = dict(transaction_id=f"TXN-{self.n:08d}", user_id=u["user_id"], card_id=u["card_id"], device_id=u["device_id"],
                 amount=0.0, ip_country="IN", velocity_1m=1, account_age_days=int(u["account_age_days"]),
                 payee_changed_hours=72 + self.r.expovariate(1 / 2500), is_new_device=False,
                 user_avg_amount=float(u["user_avg_amount"]), hour=self.r.randint(8, 22))
        p.update(kw); p["amount"] = round(p["amount"], 2); return p

    def _start_attack(self):
        r, u = self.r, self.r.choice(self.users)
        avg, kind = u["user_avg_amount"], r.choice(["Card Testing", "Account Takeover", "APP Scam", "Credit Card Fraud"])
        if kind == "Card Testing":      # burst of tiny payments on one card, velocity climbing 1,2,3...
            dev = _hex(r)
            for j in range(r.randint(4, 6)):
                self.queue.append((self._payload(u, amount=r.uniform(1, 50), device_id=dev, is_new_device=True,
                                                 velocity_1m=j + 1, ip_country=r.choice(["US", "RU", "IN"])), kind))
        elif kind == "Account Takeover":
            self.queue.append((self._payload(u, amount=avg * r.uniform(3, 9), device_id=_hex(r), is_new_device=True,
                                             payee_changed_hours=r.uniform(0.01, 8), hour=r.randint(0, 5),
                                             ip_country=r.choice(["NG", "RU", "US", "IN"])), kind))
        elif kind == "APP Scam":
            self.queue.append((self._payload(u, amount=avg * r.uniform(4, 15), payee_changed_hours=r.uniform(0.2, 48)), kind))
        else:
            self.queue.append((self._payload(u, amount=avg * r.uniform(3, 12), device_id=_hex(r), is_new_device=True,
                                             ip_country=r.choice(["US", "GB", "RU", "NG", "CN"]), hour=r.randint(0, 5)), kind))

    def next(self):
        """-> (payload, truth_label). truth is only for the demo scoreboard; the engine never sees it."""
        if not self.queue and self.r.random() < self.attack_prob: self._start_attack()
        if self.queue: return self.queue.popleft()
        u = self.r.choice(self.users)
        new_dev = self.r.random() < 0.03
        return self._payload(u, amount=max(5, u["user_avg_amount"] * self.r.lognormvariate(0, 0.5)),
                             device_id=_hex(self.r) if new_dev else u["device_id"], is_new_device=new_dev), "Legitimate"
