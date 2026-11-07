import pandas as pd

w0, mu = 2.0, 0.2
clients = pd.DataFrame({"client": ["A", "B", "C"], "n": [100, 50, 50], "delta": [0.5, -0.3, 0.1]})
clients["share"] = clients["n"] / clients["n"].sum()
clients["delta_eff"] = (1 - mu) * clients["delta"]
clients["contribution"] = clients["share"] * clients["delta_eff"]
clients["w_eff"] = w0 + clients["delta_eff"]

shift_prox = clients["contribution"].sum()
shift_avg = (clients["share"] * clients["delta"]).sum()

print(clients.round(4).to_string(index=False))
print(f"N = {clients['n'].sum()}, сумма весов = {clients['share'].sum():.2f}")
print(f"FedProx: w1 = {w0 + shift_prox:.4f} (смещение {shift_prox:+.4f})")
print(f"FedAvg:  w1 = {w0 + shift_avg:.4f} (смещение {shift_avg:+.4f})")
print(f"сокращение смещения: {1 - shift_prox / shift_avg:.0%}")
