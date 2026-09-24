import numpy as np

EA = np.array([1.0, 10.0])   #мат. ожидание кластера A
EB = np.array([5.0, 5.0])    #мат. ожидание кластера B
Q  = np.array([4.0, 2.0])    #точка, для которой ищем расстояния

#Матрицы из условия. Они несимметричны, а ковариационная матрица обязана быть симметричной
CA_raw = np.array([[3.0, 4.0],
                   [2.0, 3.0]])
CB_raw = np.array([[4.0, -1.0],
                   [-2.0, 2.0]])

#Симметризация: берём симметричную часть матрицы (M + M^T) / 2
def symmetrize(M):
    return 0.5 * (M + M.T)

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


def mahalanobis(x, mean, C, tol=1e-10):
    """Расстояние Махаланобиса с учётом возможной вырожденности C

    Если C невырождена, считаем обычную формулу sqrt(v^T C^-1 v).
    Если вырождена, распределение сосредоточено на прямой (подпространстве)
    через mean. Точка вне этого подпространства для такого распределения
    невозможна, и расстояние до неё бесконечно. Если точка лежит в
    подпространстве, берём псевдообратную матрицу
    """
    v = x - mean
    eigvals, eigvecs = np.linalg.eigh(C)
    print(f"  собственные значения C: {np.round(eigvals, 4)}")
    if np.all(eigvals > tol):
        return float(np.sqrt(v @ np.linalg.inv(C) @ v))

    null_dirs = eigvecs[:, eigvals <= tol]
    off_support = np.linalg.norm(null_dirs.T @ v)
    print(f"  матрица вырождена, компонента вектора вне носителя: {off_support:.4f}")
    if off_support > 1e-8:
        return np.inf
    return float(np.sqrt(v @ np.linalg.pinv(C) @ v))


print("Кластер A:")
dA = mahalanobis(Q, EA, CA)
print("Кластер B:")
dB = mahalanobis(Q, EB, CB)
print()

print("Расстояния Махаланобиса:")
print(f"d_M(Q, A) = {dA:.4f}")
print(f"d_M(Q, B) = {dB:.4f}")
print()

if np.isinf(dA):
    print("После симметризации CA вырождена (det = 0): кластер A лежит на прямой y - 10 = x - 1,")
    print("а точка Q на эту прямую не попадает. Значит, Q не может принадлежать A,")
    print("и расстояние до A бесконечно. Регуляризация (C + eps*I) дала бы здесь огромное,")
    print("но конечное число, которое зависит только от выбранного eps")
    print()

print("Точка Q ближе к кластеру", "A" if dA < dB else "B", "(по расстоянию Махаланобиса)")
