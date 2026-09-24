from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.linalg import sqrtm
from sklearn.decomposition import PCA

OUT_DIR = Path(__file__).resolve().parent

#Расстояние Вассерштейна между двумя гауссовскими распределениями
def wasserstein_distance_gaussian(mu1, sigma1, mu2, sigma2):
    diff_mean = np.linalg.norm(mu1 - mu2)
    #sqrtm может вернуть комплексную матрицу с нулевой мнимой частью из-за погрешностей
    sqrt_sigma1 = np.real(sqrtm(sigma1))
    sigma = np.real(sqrtm(sqrt_sigma1 @ sigma2 @ sqrt_sigma1))
    trace_term = np.trace(sigma1 + sigma2 - 2 * sigma)
    return float(np.sqrt(diff_mean**2 + max(trace_term, 0.0)))

#Матрица расстояний между кластерами
def compute_cluster_distances(clusters):
    n = len(clusters)
    means = []
    covs = []
    
    #Оцениваем параметры распределения для каждого кластера
    for cluster in clusters:
        cluster = np.array(cluster)
        mean = np.mean(cluster, axis=0)
        cov = np.cov(cluster, rowvar=False)
        means.append(mean)
        covs.append(cov)
    
    #Строим матрицу
    distance_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                distance_matrix[i, j] = 0
            else:
                distance_matrix[i, j] = wasserstein_distance_gaussian(
                    means[i], covs[i], means[j], covs[j]
                )
    return distance_matrix

#Визуализация
def plot_clusters_2d(clusters):
    plt.figure(figsize=(10, 6))
    colors = sns.color_palette("husl", len(clusters))
    
    for i, cluster in enumerate(clusters):
        cluster = np.array(cluster)
        if cluster.shape[1] > 2:
            pca = PCA(n_components=2)
            cluster_reduced = pca.fit_transform(cluster)
        else:
            cluster_reduced = cluster
        
        plt.scatter(
            cluster_reduced[:, 0], cluster_reduced[:, 1],
            color=colors[i], label=f"Кластер {i+1}", alpha=0.6
        )
    
    plt.title("Визуализация кластеров в 2D (PCA применён, если размерность > 2)")
    plt.xlabel("Компонента 1")
    plt.ylabel("Компонента 2")
    plt.legend()
    plt.grid(True)
    plt.savefig(OUT_DIR / 'clusters.png', dpi=120, bbox_inches='tight')
    plt.show()

def plot_distance_matrix(distance_matrix):
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        distance_matrix,
        annot=True, fmt=".2f", cmap="YlOrRd",
        xticklabels=[f"Кластер {i+1}" for i in range(distance_matrix.shape[0])],
        yticklabels=[f"Кластер {i+1}" for i in range(distance_matrix.shape[0])]
    )
    plt.title("Матрица расстояний между кластерами (расстояние Вассерштейна)")
    plt.savefig(OUT_DIR / 'result.png', dpi=120, bbox_inches='tight')
    plt.show()

#Пример использования
if __name__ == "__main__":
    #Генерируем тестовые кластеры (3 кластера в 3D для демонстрации PCA)
    np.random.seed(42)
    cluster1 = np.random.multivariate_normal([0, 0, 0], [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 100)
    cluster2 = np.random.multivariate_normal([3, 3, 2], [[1, 0.5, 0.3], [0.5, 1, 0.2], [0.3, 0.2, 1]], 100)
    cluster3 = np.random.multivariate_normal([-2, 2, -1], [[2, -0.7, 0.4], [-0.7, 1, -0.3], [0.4, -0.3, 1.5]], 100)
    
    clusters = [cluster1, cluster2, cluster3]
    plot_clusters_2d(clusters)
    
    distance_matrix = compute_cluster_distances(clusters)
    plot_distance_matrix(distance_matrix)
    
    print("Матрица расстояний между кластерами:")
    print(distance_matrix)