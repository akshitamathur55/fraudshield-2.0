"""graph_engine.py - NetworkX 'who is linked to whom' checks (users, cards, devices).
A device shared by many users/cards is a classic sign of a coordinated attack."""
import networkx as nx

class GraphEngine:
    def __init__(self):
        self.G = nx.Graph()

    def build(self, df):
        """Build the relationship graph from a batch of historical transactions."""
        for u, c, d in zip(df["user_id"], df["card_id"], df["device_id"]):
            self.G.add_edge(("user", u), ("device", d))
            self.G.add_edge(("card", c), ("device", d))
            self.G.add_edge(("user", u), ("card", c))
        return self

    def _count(self, node, kind, extra):
        nb = {n[1] for n in self.G.neighbors(node) if n[0] == kind} if node in self.G else set()
        nb.add(extra)                      # include the current transaction's own link
        return len(nb)

    def stats(self, user_id, card_id, device_id):
        """(users on this device, cards on this device) - including the current txn."""
        node = ("device", device_id)
        return self._count(node, "user", user_id), self._count(node, "card", card_id)

    def ego_graph(self, device_id, radius=2):
        """Small sub-graph around a device, for the Graph Visualizer screen."""
        node = ("device", device_id)
        return nx.ego_graph(self.G, node, radius=radius) if node in self.G else nx.Graph()
