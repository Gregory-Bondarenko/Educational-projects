# Лабораторная №2 — оценка риска штрафов за выбросы против затрат на очистные сооружения
# Данные: концентрации вредных веществ, справочник ПДК/штрафов, роза ветров

required_packages <- c("openxlsx", "EnvStats", "ggplot2", "dplyr", "outliers")
missing_packages <- setdiff(required_packages, rownames(installed.packages()))
if (length(missing_packages) > 0) install.packages(missing_packages)
invisible(lapply(required_packages, library, character.only = TRUE))

# 1. Загрузка данных
# Файл с данными не входит в репозиторий (см. data/README.md) — положите его сюда перед запуском.
data_path <- "data/emissions_data.xlsx"
data <- read.xlsx(data_path, sheet = 1)
info <- read.xlsx(data_path, sheet = 2)
wind <- read.xlsx(data_path, sheet = 3)

# Проверка и переименование столбцов
colnames(info) <- c("Вещество", "Ед_измерения", "ПДК", "Штраф_тыс_руб",
                    "Стоимость_системы_тыс_руб", "Стоимость_обслуживания_тыс_руб")

# 2. Оценка затрат на очистные сооружения
cost_analysis <- info %>%
  mutate(
    КапЗатраты = Стоимость_системы_тыс_руб,
    ГодОбслуживание = Стоимость_обслуживания_тыс_руб,
    СовокупныеЗатраты = КапЗатраты + 5 * ГодОбслуживание
  ) %>%
  select(Вещество, КапЗатраты, ГодОбслуживание, СовокупныеЗатраты)

# 3. Очистка данных от выбросов (тест Граббса, однократное удаление наиболее выделяющегося значения)
clean_data <- data
for (col in names(data)[-1]) {
  x <- data[[col]]
  if (length(unique(x)) > 1) {
    grubbs_test <- grubbs.test(x, type = 10)
    if (grubbs_test$p.value < 0.05) {
      clean_data[[col]] <- rm.outlier(x, fill = TRUE)
    }
  }
}

# 4. Оценка распределений
analyze_distribution <- function(x) {
  fits <- list(
    normal = tryCatch(enorm(x), error = function(e) NULL),
    gamma = tryCatch(egamma(x), error = function(e) NULL),
    exp = tryCatch(eexp(x), error = function(e) NULL),
    weibull = tryCatch(eweibull(x), error = function(e) NULL)
  )

  aic <- sapply(fits, function(f) {
    if (!is.null(f)) round(-2 * f$loglik + 2 * length(f$parameters), 2) else NA
  })

  best <- if (all(is.na(aic))) NA else names(which.min(aic))

  list(fits = fits, aic = aic, best = best)
}

dist_results <- lapply(names(clean_data)[-1], function(col) {
  analyze_distribution(clean_data[[col]])
})
names(dist_results) <- names(clean_data)[-1]

# 5. Функция построения графика всех распределений сразу
plot_all_distributions <- function(x, name, fits) {
  df <- data.frame(x = x)

  p <- ggplot(df, aes(x = x)) +
    geom_histogram(aes(y = ..density..), bins = 30, fill = "lightblue", alpha = 0.7, color = "black") +
    geom_density(color = "black", size = 1.2, linetype = "solid") +
    ggtitle(paste("Сравнение распределений для", name)) +
    xlab("Концентрация") + ylab("Плотность") +
    theme_minimal()

  if (!is.null(fits$normal)) {
    p <- p + stat_function(fun = dnorm,
                           args = list(mean = fits$normal$parameters[1],
                                       sd = fits$normal$parameters[2]),
                           color = "blue", linetype = "dashed", size = 1)
  }
  if (!is.null(fits$gamma)) {
    p <- p + stat_function(fun = dgamma,
                           args = list(shape = fits$gamma$parameters[1],
                                       rate = fits$gamma$parameters[2]),
                           color = "green", linetype = "dotdash", size = 1)
  }
  if (!is.null(fits$exp)) {
    p <- p + stat_function(fun = dexp,
                           args = list(rate = fits$exp$parameters[1]),
                           color = "purple", linetype = "twodash", size = 1)
  }
  if (!is.null(fits$weibull)) {
    p <- p + stat_function(fun = dweibull,
                           args = list(shape = fits$weibull$parameters[1],
                                       scale = fits$weibull$parameters[2]),
                           color = "orange", linetype = "longdash", size = 1)
  }

  return(p)
}

# Функция построения ЭФР
plot_ecdf <- function(x, name) {
  p <- ggplot(data.frame(x = x), aes(x = x)) +
    stat_ecdf(geom = "step", color = "blue", size = 1.2) +
    ggtitle(paste("Эмпирическая функция распределения для", name)) +
    xlab("Концентрация") + ylab("F(x)") +
    theme_minimal()

  return(p)
}

# Создание папки для графиков
plots_dir <- "plots"
if (!dir.exists(plots_dir)) dir.create(plots_dir)

# 7. Построение графиков
for (sub in names(dist_results)) {
  x <- clean_data[[sub]]
  fits <- dist_results[[sub]]$fits
  best_fit <- dist_results[[sub]]$best

  if (is.na(best_fit) || is.null(best_fit)) {
    p_ecdf <- plot_ecdf(x, sub)
    print(p_ecdf)
    ggsave(filename = paste0(plots_dir, "/", sub, "_ecdf.png"), plot = p_ecdf, width = 8, height = 6)
  } else {
    p_all <- plot_all_distributions(x, sub, fits)
    print(p_all)
    ggsave(filename = paste0(plots_dir, "/", sub, "_distributions.png"), plot = p_all, width = 8, height = 6)
  }
}

# 8-9. Вероятность штрафа при неблагоприятном ветре
wind$Эффективность <- c(0, 0.25, 0.5, 0.9, 0.75, 0.4, 0.1, 0)
max_eff <- max(wind$Эффективность)

penalty_analysis <- info %>%
  mutate(
    Вероятность = sapply(1:nrow(info), function(i) {
      mean(clean_data[[i + 1]] > (ПДК[i] / max_eff), na.rm = TRUE)
    }),
    ОжидаемыйШтраф = Штраф_тыс_руб * Вероятность * 365 * 5
  ) %>%
  bind_cols(cost_analysis %>% select(КапЗатраты, СовокупныеЗатраты))

# 10. Отсеивание веществ
filtered_substances <- penalty_analysis %>%
  filter(ОжидаемыйШтраф >= СовокупныеЗатраты)

# 11-12. Полная вероятность штрафа с учётом ветров
full_penalty <- penalty_analysis %>%
  mutate(
    ПолнаяВероятность = sapply(1:nrow(.), function(i) {
      sum(sapply(1:nrow(wind), function(j) {
        if (wind$Эффективность[j] > 0) {
          mean(clean_data[[i + 1]] > (ПДК[i] / wind$Эффективность[j]), na.rm = TRUE) * wind$Дней_в_году[j] / 365
        } else {
          0
        }
      }))
    }),
    ПолныйШтраф = Штраф_тыс_руб * ПолнаяВероятность * 365 * 5
  )

# 13-14. Сопоставление затрат и штрафов
final_analysis <- full_penalty %>%
  mutate(
    Рекомендация = ifelse(ПолныйШтраф > СовокупныеЗатраты,
                          "Установить очистное оборудование",
                          "Допустить штрафы")
  ) %>%
  select(Вещество, КапЗатраты, СовокупныеЗатраты, ПолныйШтраф, Рекомендация)

# Вывод результатов
print("Сводка по затратам:")
print(cost_analysis)

print("Анализ штрафов:")
print(penalty_analysis %>% select(Вещество, ПДК, Штраф_тыс_руб, Вероятность, ОжидаемыйШтраф))

print("Итоговые рекомендации:")
print(final_analysis)

# Сохранение результатов
write.xlsx(list(
  Затраты = cost_analysis,
  Штрафы = penalty_analysis,
  Рекомендации = final_analysis
), "results.xlsx")
