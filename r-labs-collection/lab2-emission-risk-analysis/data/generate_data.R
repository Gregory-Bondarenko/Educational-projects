# Генерация синтетического файла emissions_data.xlsx той же структуры, что и в задании
# Лист 1: суточные концентрации веществ, лист 2: справочник ПДК, штрафов и стоимости
# очистки, лист 3: роза ветров (сколько дней в году дует ветер каждого направления)

library(openxlsx)
set.seed(26)
n_days <- 365

conc <- data.frame(
  День = seq_len(n_days),
  Фосген = rgamma(n_days, shape = 4, rate = 80),
  Диоксин = rexp(n_days, rate = 2e4),
  `Диоксид серы` = rnorm(n_days, 0.35, 0.08),
  Бромметан = rweibull(n_days, shape = 1.8, scale = 0.6),
  Аммиак = rlnorm(n_days, log(0.12), 0.35),
  check.names = FALSE
)
# Несколько явных выбросов, чтобы тесту Граббса было что находить
conc$Фосген[c(40, 200)] <- c(0.45, 0.5)
conc$Аммиак[120] <- 1.4
conc$`Диоксид серы` <- pmax(conc$`Диоксид серы`, 0.01)

info <- data.frame(
  Вещество = c("Фосген", "Диоксин", "Диоксид серы", "Бромметан", "Аммиак"),
  Ед = rep("мг/м3", 5),
  ПДК = c(0.05, 0.00005, 0.5, 1.0, 0.2),
  Штраф = c(120, 300, 40, 60, 25),
  Система = c(9000, 25000, 6000, 12000, 3500),
  Обслуживание = c(600, 1500, 300, 900, 200)
)

wind <- data.frame(
  Направление = c("С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"),
  Дней_в_году = c(40, 35, 38, 52, 60, 58, 45, 37)
)

wb <- createWorkbook()
addWorksheet(wb, "Концентрации"); writeData(wb, 1, conc)
addWorksheet(wb, "Справочник");   writeData(wb, 2, info)
addWorksheet(wb, "Роза ветров");  writeData(wb, 3, wind)
saveWorkbook(wb, "emissions_data.xlsx", overwrite = TRUE)
cat("Сохранено: data/emissions_data.xlsx\n")
