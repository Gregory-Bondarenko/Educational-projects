# Генерация синтетической мастер-таблицы опроса той же структуры, что и в задании
# Оригинальные данные привязаны к варианту курса и в репозиторий не входят
#
# 50 столбцов: 10 оценок идеального вина + 4 альтернативы по 10 характеристик
# Оценки целые, по шкале от 1 до 10

set.seed(26)
n_resp <- 120
n_attr <- 10

ideal_profile <- c(8, 6, 7, 5, 9, 4, 7, 6, 8, 5)
clip <- function(x) pmin(pmax(round(x), 1), 10)

ideal <- sapply(ideal_profile, function(m) clip(rnorm(n_resp, m, 1.2)))

# Каждая альтернатива отличается от идеала своим набором смещений
shifts <- list(
  c( 0, -1,  1, 0, -1,  1, 0, -1,  0,  1),
  c(-2,  1, -2, 2, -3,  2, -1, 1, -2,  0),
  c( 1,  0,  0, -1, 0,  0,  1, 0,  1, -1),
  c(-3, -2, 2,  3, -2, 3, -3, 2,  -1, 2)
)
alts <- lapply(shifts, function(s) {
  sapply(seq_len(n_attr), function(j) clip(ideal[, j] + s[j] + rnorm(n_resp, 0, 1.5)))
})

Result <- as.data.frame(cbind(ideal, do.call(cbind, alts)))
colnames(Result) <- c(paste0("Ideal_", 1:10),
                      paste0(rep(paste0("Wine", 1:4, "_"), each = 10), 1:10))

save(Result, file = "ideal_point_survey.RData")
cat("Сохранено: data/ideal_point_survey.RData,", nrow(Result), "респондентов\n")
