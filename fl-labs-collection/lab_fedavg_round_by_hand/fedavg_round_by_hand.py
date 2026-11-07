import pandas as pd

w0 = 1.0
clients = pd.DataFrame({"client": ["A", "B", "C"], "n": [100, 60, 40], "delta": [0.4, -0.2, 0.6]})
clients["w_k"] = w0 + clients["delta"]
clients["share"] = clients["n"] / clients["n"].sum()
clients["contribution"] = clients["share"] * clients["w_k"]

w1_models = clients["contribution"].sum()
w1_updates = w0 + (clients["share"] * clients["delta"]).sum()

print(clients.round(4).to_string(index=False))
print(f"сумма долей = {clients['share'].sum():.2f}")
print(f"w1 через модели = {w1_models:.4f}, через обновления = {w1_updates:.4f}")
