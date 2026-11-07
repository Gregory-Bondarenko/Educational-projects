import pandas as pd

w0, lr = 2.0, 0.1
clients = pd.DataFrame({"client": ["A", "B", "C"], "n": [100, 60, 40], "a": [1, 1, 2], "m": [1, 3, 4]})
clients["share"] = clients["n"] / clients["n"].sum()
clients["grad"] = clients["a"] * (w0 - clients["m"])

global_grad = (clients["share"] * clients["grad"]).sum()
clients["deviation"] = clients["grad"] - global_grad
clients["weighted_sq"] = clients["share"] * clients["deviation"] ** 2
clients["w_local"] = w0 - lr * clients["grad"]

w1_global = w0 - lr * global_grad
w1_fedavg = (clients["share"] * clients["w_local"]).sum()
numerator = (clients["share"] * clients["a"] * clients["m"]).sum()
denominator = (clients["share"] * clients["a"]).sum()

print(clients.round(4).to_string(index=False))
print(f"F'(w0) = {global_grad:.4f}, zeta^2 = {clients['weighted_sq'].sum():.4f}")
print(f"w1 через глобальный градиент = {w1_global:.4f}, через усреднение моделей = {w1_fedavg:.4f}")
print(f"w* = {numerator:.2f} / {denominator:.2f} = {numerator / denominator:.4f}")
