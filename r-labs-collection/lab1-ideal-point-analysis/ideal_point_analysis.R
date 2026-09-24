# Лабораторная №1 - анализ методом идеальной точки
# Данные: результаты маркетингового опроса (10 идеальных характеристик + 4 альтернативы по 10 признаков)

required_packages <- c("moments", "ggplot2", "reshape2", "dplyr")
missing_packages <- setdiff(required_packages, rownames(installed.packages()))
if (length(missing_packages) > 0) install.packages(missing_packages)
invisible(lapply(required_packages, library, character.only = TRUE))

# Загрузка данных
# Оригинальный файл варианта в репозиторий не входит. Если его нет,
# генерируем синтетическую таблицу той же структуры (data/generate_data.R)
if (!file.exists("data/ideal_point_survey.RData")) {
  local({ old <- setwd("data"); on.exit(setwd(old)); source("generate_data.R", encoding = "UTF-8") })
}
load("data/ideal_point_survey.RData")
dir.create("assets", showWarnings = FALSE)
str(Result)

# 1. Идеальные характеристики (первые 10 столбцов)
ideal <- Result[, 1:10]
colnames(ideal) <- c("Attr1", "Attr2", "Attr3", "Attr4", "Attr5",
                     "Attr6", "Attr7", "Attr8", "Attr9", "Attr10")

# 2. Альтернативы (по 10 признаков каждая из 4 блоков)
alternatives <- list(
  Wine1 = Result[, 11:20],
  Wine2 = Result[, 21:30],
  Wine3 = Result[, 31:40],
  Wine4 = Result[, 41:50]
)

for (i in names(alternatives)) {
  colnames(alternatives[[i]]) <- colnames(ideal)
}

# 3. Веса характеристик. В задании все характеристики равнозначны, поэтому веса единичные
weights <- matrix(1, nrow = nrow(ideal), ncol = ncol(ideal))

# 4. Расчёт отклонений от идеала
deviations <- list()
for (alt in names(alternatives)) {
  dev <- abs(alternatives[[alt]] - ideal) * weights
  deviations[[alt]] <- rowSums(dev)
}
dev_df <- as.data.frame(deviations)

# 5. Центральные тенденции
central_tendency <- data.frame(
  Mean = colMeans(dev_df),
  Median = apply(dev_df, 2, median),
  Mode = apply(dev_df, 2, function(x) {
    ux <- unique(x)
    ux[which.max(tabulate(match(x, ux)))]
  })
)
print("Центральные тенденции:")
print(central_tendency)

# 6. Вариация
variation <- data.frame(
  Variance = apply(dev_df, 2, var),
  StdDev = apply(dev_df, 2, sd),
  Range = apply(dev_df, 2, function(x) max(x) - min(x)),
  CoefVariation = apply(dev_df, 2, sd) / colMeans(dev_df) * 100
)
print("Показатели вариации:")
print(variation)

# 7. Характер распределений
distribution <- data.frame(
  Skewness = apply(dev_df, 2, skewness),
  Kurtosis = apply(dev_df, 2, kurtosis),
  Differentiation = apply(dev_df, 2, function(x) length(unique(x)) / length(x))
)
print("Показатели характера распределений:")
print(distribution)

# 8. Характеристики идеального исполнения
get_mode <- function(x) {
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}
ideal_stats <- data.frame(
  Mean = colMeans(ideal),
  Median = apply(ideal, 2, median),
  Mode = apply(ideal, 2, get_mode),
  Variance = apply(ideal, 2, var),
  StdDev = apply(ideal, 2, sd),
  Min = apply(ideal, 2, min),
  Max = apply(ideal, 2, max),
  Range = apply(ideal, 2, function(x) max(x) - min(x)),
  IQR = apply(ideal, 2, IQR),
  CI_Lower = colMeans(ideal) - qt(0.975, df = nrow(ideal) - 1) * apply(ideal, 2, sd) / sqrt(nrow(ideal)),
  CI_Upper = colMeans(ideal) + qt(0.975, df = nrow(ideal) - 1) * apply(ideal, 2, sd) / sqrt(nrow(ideal))
)
print("Характеристики идеального исполнения:")
print(ideal_stats)

# 9. Визуализация идеального исполнения

# Паутинчатая диаграмма (полярный график)
ideal_mean <- colMeans(ideal)
radar_data <- data.frame(
  Characteristic = names(ideal_mean),
  Value = ideal_mean
)
radar_data$Characteristic <- factor(radar_data$Characteristic, levels = colnames(ideal))
p_radar <- ggplot(radar_data, aes(x = Characteristic, y = Value, group = 1)) +
  geom_polygon(fill = "lightblue", alpha = 0.5, colour = "steelblue") +
  geom_point() +
  coord_polar() +
  labs(title = "Идеальный продукт (паутинчатая диаграмма)", x = NULL, y = NULL) +
  theme_minimal()
ggsave("assets/ideal_radar.png", p_radar, width = 6, height = 6, dpi = 110)

# Столбчатая диаграмма
p_bar <- ggplot(radar_data, aes(x = Characteristic, y = Value)) +
  geom_bar(stat = "identity", fill = "lightblue") +
  labs(title = "Средние значения по атрибутам идеального продукта", x = NULL, y = "Среднее") +
  theme_minimal()
ggsave("assets/ideal_bar.png", p_bar, width = 8, height = 5, dpi = 110)

# 10. График средних отклонений
dev_melt <- melt(dev_df, variable.name = "Alternative", value.name = "Deviation")
dev_summary <- dev_melt %>%
  group_by(Alternative) %>%
  summarise(Mean_Deviation = mean(Deviation)) %>%
  arrange(desc(Mean_Deviation))
p_mean <- ggplot(dev_summary, aes(x = reorder(Alternative, -Mean_Deviation), y = Mean_Deviation)) +
  geom_line(group = 1) +
  geom_point() +
  labs(title = "Средние отклонения от идеала", x = "Альтернатива", y = "Отклонение") +
  theme_minimal()
ggsave("assets/mean_deviation.png", p_mean, width = 7, height = 5, dpi = 110)

# 11. Диаграмма размаха по альтернативам
p_box <- ggplot(dev_melt, aes(x = Alternative, y = Deviation)) +
  geom_boxplot(fill = "lightgreen") +
  labs(title = "Распределение отклонений по альтернативам", x = "Альтернатива", y = "Отклонение") +
  theme_minimal()
ggsave("assets/deviation_boxplot.png", p_box, width = 7, height = 5, dpi = 110)

# 12. Гистограмма
p_hist <- ggplot(dev_melt, aes(x = Deviation, fill = Alternative)) +
  geom_histogram(position = "dodge", bins = 20) +
  labs(title = "Гистограмма отклонений по альтернативам", x = "Отклонение", y = "Число респондентов") +
  theme_minimal()
ggsave("assets/deviation_histogram.png", p_hist, width = 8, height = 5, dpi = 110)

# Итог: какая альтернатива ближе всего к идеалу
best <- rownames(central_tendency)[which.min(central_tendency$Mean)]
cat("\nБлиже всего к идеалу в среднем:", best, "\n")
