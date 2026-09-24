# Лабораторная №2: очистные сооружения или штрафы за выбросы
# Данные: суточные концентрации вредных веществ, справочник ПДК и штрафов, роза ветров

required_packages <- c("openxlsx", "ggplot2", "dplyr", "outliers", "MASS")
missing_packages <- setdiff(required_packages, rownames(installed.packages()))
if (length(missing_packages) > 0) install.packages(missing_packages)
invisible(lapply(required_packages, library, character.only = TRUE))
select <- dplyr::select  # MASS тоже экспортирует select

# 1. Загрузка данных
# Оригинальный файл варианта в репозиторий не входит. Если его нет,
# генерируем синтетический файл той же структуры (data/generate_data.R)
data_path <- "data/emissions_data.xlsx"
if (!file.exists(data_path)) {
  local({ old <- setwd("data"); on.exit(setwd(old)); source("generate_data.R", encoding = "UTF-8") })
}
data <- read.xlsx(data_path, sheet = 1)
info <- read.xlsx(data_path, sheet = 2)
wind <- read.xlsx(data_path, sheet = 3)

colnames(info) <- c("Вещество", "Ед_измерения", "ПДК", "Штраф_тыс_руб",
                    "Стоимость_системы_тыс_руб", "Стоимость_обслуживания_тыс_руб")
substances <- names(data)[-1]
stopifnot(length(substances) == nrow(info))  # порядок веществ в листах 1 и 2 совпадает

# 2. Затраты на очистные сооружения за 5 лет
cost_analysis <- info %>%
  mutate(
    КапЗатраты = Стоимость_системы_тыс_руб,
    ГодОбслуживание = Стоимость_обслуживания_тыс_руб,
    СовокупныеЗатраты = КапЗатраты + 5 * ГодОбслуживание
  ) %>%
  select(Вещество, КапЗатраты, ГодОбслуживание, СовокупныеЗатраты)

# 3. Очистка от выбросов: тест Граббса, однократная замена самого выделяющегося значения
clean_data <- data
for (col in substances) {
  x <- data[[col]]
  if (length(unique(x)) > 1) {
    grubbs_test <- grubbs.test(x, type = 10)
    if (grubbs_test$p.value < 0.05) {
      clean_data[[col]] <- rm.outlier(x, fill = TRUE)
      cat(sprintf("%s: выброс найден и заменён (p = %.4f)\n", col, grubbs_test$p.value))
    }
  }
}

# 4. Подбор теоретического распределения по AIC
# MASS::fitdistr возвращает логарифм правдоподобия, поэтому AIC() считается напрямую.
# Если ни одно распределение не подошло (или AIC сильно хуже эмпирики), дальше
# работаем с эмпирической функцией распределения
analyze_distribution <- function(x) {
  x_pos <- x[x > 0]
  safe_fit <- function(expr) tryCatch(suppressWarnings(expr), error = function(e) NULL)
  scale_k <- 1 / mean(x_pos)  # масштабируем, чтобы оптимизатору было проще
  fits <- list(
    normal  = safe_fit(fitdistr(x, "normal")),
    gamma   = safe_fit(fitdistr(x_pos * scale_k, "gamma")),
    exp     = safe_fit(fitdistr(x_pos, "exponential")),
    weibull = safe_fit(fitdistr(x_pos * scale_k, "weibull"))
  )
  # Возвращаем параметры гаммы и Вейбулла к исходному масштабу, а AIC пересчитываем
  # с учётом якобиана замены y = k*x: logL(x) = logL(y) + n*log(k)
  aic <- sapply(names(fits), function(nm) {
    f <- fits[[nm]]
    if (is.null(f)) return(NA)
    a <- AIC(f)
    if (nm %in% c("gamma", "weibull")) a <- a - 2 * length(x_pos) * log(scale_k)
    round(a, 2)
  })
  if (!is.null(fits$gamma))   fits$gamma$estimate["rate"] <- fits$gamma$estimate["rate"] * scale_k
  if (!is.null(fits$weibull)) fits$weibull$estimate["scale"] <- fits$weibull$estimate["scale"] / scale_k

  best <- if (all(is.na(aic))) NA else names(which.min(aic))
  list(fits = fits, aic = aic, best = best)
}

dist_results <- lapply(substances, function(col) analyze_distribution(clean_data[[col]]))
names(dist_results) <- substances

cat("\nAIC по веществам:\n")
print(t(sapply(dist_results, `[[`, "aic")))

# 5. Графики: гистограмма, эмпирическая плотность и подобранные законы
plot_all_distributions <- function(x, name, fits, best) {
  p <- ggplot(data.frame(x = x), aes(x = x)) +
    geom_histogram(aes(y = after_stat(density)), bins = 30, fill = "lightblue", alpha = 0.7, colour = "grey30") +
    geom_density(colour = "black", linewidth = 1) +
    labs(title = paste("Распределение концентрации:", name),
         subtitle = paste("Лучшее по AIC:", best), x = "Концентрация", y = "Плотность") +
    theme_minimal()
  add <- function(p, fun, args, colour, lt) p + stat_function(fun = fun, args = args, colour = colour, linetype = lt, linewidth = 1)
  if (!is.null(fits$normal))  p <- add(p, dnorm, as.list(fits$normal$estimate), "blue", "dashed")
  if (!is.null(fits$gamma))   p <- add(p, dgamma, as.list(fits$gamma$estimate), "darkgreen", "dotdash")
  if (!is.null(fits$exp))     p <- add(p, dexp, as.list(fits$exp$estimate), "purple", "twodash")
  if (!is.null(fits$weibull)) p <- add(p, dweibull, as.list(fits$weibull$estimate), "orange", "longdash")
  p
}

plot_ecdf <- function(x, name) {
  ggplot(data.frame(x = x), aes(x = x)) +
    stat_ecdf(geom = "step", colour = "blue", linewidth = 1) +
    labs(title = paste("Эмпирическая функция распределения:", name), x = "Концентрация", y = "F(x)") +
    theme_minimal()
}

# Латинские имена файлов для графиков
translit <- function(x) {
  ru <- c("а","б","в","г","д","е","ё","ж","з","и","й","к","л","м","н","о","п","р","с","т","у","ф","х","ц","ч","ш","щ","ъ","ы","ь","э","ю","я")
  en <- c("a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","h","ts","ch","sh","sch","","y","","e","yu","ya")
  chars <- strsplit(tolower(x), "")[[1]]
  out <- vapply(chars, function(ch) { i <- match(ch, ru); if (is.na(i)) ch else en[i] }, "")
  gsub("[^a-z0-9]+", "_", paste(out, collapse = ""))
}

dir.create("assets", showWarnings = FALSE)
for (sub in substances) {
  x <- clean_data[[sub]]
  res <- dist_results[[sub]]
  file_name <- translit(sub)
  p <- if (is.na(res$best)) plot_ecdf(x, sub) else plot_all_distributions(x, sub, res$fits, res$best)
  ggsave(file.path("assets", paste0(file_name, ".png")), p, width = 8, height = 5, dpi = 100)
}
ggsave("assets/ecdf_example.png", plot_ecdf(clean_data[[substances[1]]], substances[1]), width = 8, height = 5, dpi = 100)

# 8-9. Вероятность суточного штрафа при самом неблагоприятном ветре
# Коэффициент показывает, какая доля выброса доходит до контрольной точки
# при ветре данного направления (задан в условии варианта)
wind$Эффективность <- c(0, 0.25, 0.5, 0.9, 0.75, 0.4, 0.1, 0)
max_eff <- max(wind$Эффективность)

exceed_prob <- function(x, pdk, eff) mean(x * eff > pdk, na.rm = TRUE)

penalty_analysis <- info %>%
  mutate(
    Вероятность = sapply(seq_along(substances), function(i) exceed_prob(clean_data[[substances[i]]], ПДК[i], max_eff)),
    ОжидаемыйШтраф = Штраф_тыс_руб * Вероятность * 365 * 5
  ) %>%
  bind_cols(cost_analysis %>% select(КапЗатраты, СовокупныеЗатраты))

# 10. Вещества, для которых даже худший случай дешевле очистки, дальше не рассматриваем
filtered_substances <- penalty_analysis %>% filter(ОжидаемыйШтраф >= СовокупныеЗатраты)
cat("\nОстаются после отсева:", paste(filtered_substances$Вещество, collapse = ", "), "\n")

# 11-12. Полная вероятность штрафа с учётом розы ветров
full_penalty <- penalty_analysis %>%
  mutate(
    ПолнаяВероятность = sapply(seq_along(substances), function(i) {
      sum(sapply(seq_len(nrow(wind)), function(j) {
        exceed_prob(clean_data[[substances[i]]], ПДК[i], wind$Эффективность[j]) * wind$Дней_в_году[j] / sum(wind$Дней_в_году)
      }))
    }),
    ПолныйШтраф = Штраф_тыс_руб * ПолнаяВероятность * 365 * 5
  )

# 13-14. Сопоставление затрат и штрафов
final_analysis <- full_penalty %>%
  mutate(Рекомендация = ifelse(ПолныйШтраф > СовокупныеЗатраты,
                               "Установить очистное оборудование", "Допустить штрафы")) %>%
  select(Вещество, СовокупныеЗатраты, ПолнаяВероятность, ПолныйШтраф, Рекомендация)

cat("\nСводка по затратам:\n"); print(cost_analysis)
cat("\nХудший случай по ветру:\n")
print(penalty_analysis %>% select(Вещество, ПДК, Штраф_тыс_руб, Вероятность, ОжидаемыйШтраф))
cat("\nИтоговые рекомендации:\n"); print(final_analysis)

write.xlsx(list(Затраты = cost_analysis, Штрафы = penalty_analysis, Рекомендации = final_analysis),
           "results.xlsx", overwrite = TRUE)
