import numpy as np
from numpy.linalg import inv, pinv, LinAlgError

EA = np.array([1.0, 10.0])   #мат. ожидание кластера A
EB = np.array([5.0, 5.0])    #мат. ожидание кластера B
Q  = np.array([4.0, 2.0])    #точка, для которой ищем расстояния

#Матрицы
CA_raw = np.array([[3.0, 4.0],
                   [2.0, 3.0]])
CB_raw = np.array([[4.0, -1.0],
                   [-2.0, 2.0]])

#Симметризация ковариаций
def symmetrize(M):
    M_sym = M.copy().astype(float)
    off = 0.5 * (M_sym[0,1] + M_sym[1,0])
    M_sym[0,1] = off
    M_sym[1,0] = off
    return M_sym

CA = symmetrize(CA_raw)
CB = symmetrize(CB_raw)

print("Симметризированные ковариационные матрицы:")
print("CA =\n", CA)
print("CB =\n", CB)
print()

#Евклидовы расстояния
dA_euc = np.linalg.norm(Q - EA)
dB_euc = np.linalg.norm(Q - EB)
print("Евклидовы расстояния:")
print(f"d(Q, A) = {dA_euc:.4f}")
print(f"d(Q, B) = {dB_euc:.4f}")
print()

#Функция Махаланобисова расстояния
def mahalanobis_sq(x, mean, C, reg=0.0):
    """Вычисление квадрата расстояния Махаланобиса с регуляризацией"""
    C_reg = C + reg * np.eye(C.shape[0])
    try:
        invC = inv(C_reg)
    except LinAlgError:
        invC = pinv(C_reg)
    v = x - mean
    return float(v.T @ invC @ v)

#Расчёт
eps = 1e-6  #регуляризация
dA2 = mahalanobis_sq(Q, EA, CA, reg=eps)
dB2 = mahalanobis_sq(Q, EB, CB, reg=0.0)

print("Махаланобисовы расстояния:")
print(f"d_M(Q, A)^2 = {dA2:.4f},   d_M(Q, A) = {np.sqrt(dA2):.4f}")
print(f"d_M(Q, B)^2 = {dB2:.4f},   d_M(Q, B) = {np.sqrt(dB2):.4f}")
print()

#Вывод
if np.sqrt(dA2) < np.sqrt(dB2):
    print("Точка Q ближе к кластеру A (по Махаланобисову расстоянию).")
else:
    print("Точка Q ближе к кластеру B (по Махаланобисову расстоянию).")