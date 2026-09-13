# Лабораторная №3 — регрессионная модель уровня субъективного счастья
# Данные: социально-экономические и поведенческие показатели по сообществам (индивидуальный вариант)

required_packages <- c("readxl", "dplyr", "ggplot2")
missing_packages <- setdiff(required_packages, rownames(installed.packages()))
if (length(missing_packages) > 0) install.packages(missing_packages)
invisible(lapply(required_packages, library, character.only = TRUE))

set.seed(123)

# Загрузка данных
# Файл с данными не входит в репозиторий (см. data/README.md) — положите его сюда перед запуском.
data <- read_excel("data/happiness_survey.xlsx")

# Очистка имён столбцов
colnames(data) <- make.names(colnames(data), unique = TRUE)

# Определение переменных
state_vars <- c("Оценка.благополучия", "Оценка.социальной.поддержки",
                "Ожидаемая.продолжительность.здоровой.жизни",
                "Свобода.граждан.самостоятельно.принимать.жизненно.важные.решения",
                "Индекс.Щедрости", "Индекс.отношения.к.коррупции",
                "Оценка.риска.безработицы", "Индекс.кредитного.оптимизма",
                "Индекс.страха.социальных.конфликтов", "Индекс.семьи",
                "Индекс.продовольственной.безопасности", "Чувство.технологического.прогресса",
                "Чувство.неравенства.доходов.в.обществе")

causal_vars <- c("Среднегодовой.доход..тыс...", "Объем.потребленного.алкоголя.в.год..л.",
                 "Количество.членов.семьи", "Количество.лет.образования",
                 "Доля.от.дохода.семьи.которая.тратится.на.продовольствие...",
                 "Коэффициент.Джини.сообщества",
                 "Издержки.сообщества.на.окружающую.среду..млн...",
                 "Охват.беспроводной.связи.в.сообществе...",
                 "Количество.смертей.от.вирусных.и.респираторных.заболеваний.в.сообществе..тыс..человек",
                 "Волатильность.потребительских.цен.в.сообществе")

response_var <- "Ощущаемое_счастье"

# Отбор данных без пропусков
data_complete <- data[!is.na(data[[response_var]]), ]
data_complete <- data_complete %>%
  mutate(across(all_of(c(state_vars, causal_vars, response_var)), as.numeric)) %>%
  filter(across(everything(), ~ !is.na(.) & !is.infinite(.)))

# Деление на обучение и валидацию
n <- nrow(data_complete)
train_index <- sample(1:n, size = floor(0.8 * n))
train_data <- data_complete[train_index, ]
valid_data <- data_complete[-train_index, ]

# Корреляция с целевой переменной
cor_values <- sapply(train_data[, state_vars], function(x) cor(x, train_data[[response_var]], use = "complete.obs"))
top_state_vars <- names(sort(abs(cor_values), decreasing = TRUE))[1:5]

# Построение модели
predictors <- c(top_state_vars, causal_vars)
formula <- as.formula(paste(response_var, "~", paste(predictors, collapse = "+")))
model <- lm(formula, data = train_data)

# Предсказания
valid_data$predicted <- predict(model, newdata = valid_data)

# R² вручную
SSE <- sum((valid_data[[response_var]] - valid_data$predicted)^2)
SST <- sum((valid_data[[response_var]] - mean(valid_data[[response_var]]))^2)
r2 <- 1 - SSE / SST
adj_r2 <- 1 - (1 - r2) * (nrow(valid_data) - 1) / (nrow(valid_data) - length(predictors) - 1)

cat("Скорректированный R² на валидации:", round(adj_r2, 4), "\n")

# Сохранение графика: фактическое vs предсказанное
plot_file <- "happiness_actual_vs_predicted.png"
png(filename = plot_file, width = 800, height = 600)
ggplot(valid_data, aes_string(x = response_var, y = "predicted")) +
  geom_point(color = "steelblue", size = 3) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "red") +
  labs(title = "Фактическое vs Прогнозируемое счастье",
       x = "Фактическое",
       y = "Прогнозируемое") +
  theme_minimal()
dev.off()
cat("График сохранён как", plot_file, "\n")

# Визуализация важности переменных
coefs <- coef(model)[-1]  # без intercept
importance <- data.frame(Variable = names(coefs), Coefficient = coefs)
importance <- importance[order(abs(importance$Coefficient), decreasing = TRUE), ]

bar_file <- "feature_importance.png"
png(filename = bar_file, width = 1000, height = 600)
ggplot(importance, aes(x = reorder(Variable, abs(Coefficient)), y = Coefficient)) +
  geom_col(fill = "skyblue") +
  coord_flip() +
  labs(title = "Важность признаков (коэффициенты модели)",
       x = "Признак",
       y = "Коэффициент") +
  theme_minimal()
dev.off()
cat("График важности признаков сохранён как", bar_file, "\n")
