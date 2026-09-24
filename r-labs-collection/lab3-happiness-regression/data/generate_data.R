# Генерация синтетического happiness_survey.xlsx той же структуры, что и в задании
# Строка = сообщество, столбцы = 13 «признаков состояния», 10 «причинных» признаков
# и целевая переменная Ощущаемое_счастье

library(openxlsx)
set.seed(26)
n <- 400

income  <- rlnorm(n, log(600), 0.4)
alcohol <- rnorm(n, 8, 2.5)
family  <- rpois(n, 2) + 1
edu     <- rnorm(n, 13, 2)
food    <- rnorm(n, 30, 7)
gini    <- runif(n, 0.25, 0.5)
eco     <- rlnorm(n, log(40), 0.5)
wifi    <- runif(n, 40, 100)
deaths  <- rgamma(n, 2, 1)
volat   <- rgamma(n, 3, 2)

wellbeing <- 3 + 0.004 * income - 5 * gini + 0.1 * edu + rnorm(n, 0, 0.6)
support   <- 0.6 + 0.02 * family + rnorm(n, 0, 0.08)
health    <- 55 + 0.01 * income + rnorm(n, 0, 3)
freedom   <- rnorm(n, 0.75, 0.1)
generous  <- rnorm(n, 0, 0.15)
corrupt   <- rnorm(n, 0.7, 0.15)
unemp     <- 0.3 - 0.0002 * income + rnorm(n, 0, 0.05)
credit    <- rnorm(n, 0.5, 0.12)
conflict  <- rnorm(n, 0.4, 0.1)
fam_idx   <- rnorm(n, 0.6, 0.1)
food_sec  <- 0.9 - 0.008 * food + rnorm(n, 0, 0.05)
tech      <- 0.3 + 0.004 * wifi + rnorm(n, 0, 0.05)
inequal   <- 0.2 + gini + rnorm(n, 0, 0.05)

happy <- 1 + 0.55 * wellbeing + 0.0012 * income - 0.02 * food - 3 * unemp -
  2 * gini + 1.2 * support + 0.02 * health + rnorm(n, 0, 0.25)

data <- data.frame(
  `Оценка благополучия` = wellbeing,
  `Оценка социальной поддержки` = support,
  `Ожидаемая продолжительность здоровой жизни` = health,
  `Свобода граждан самостоятельно принимать жизненно важные решения` = freedom,
  `Индекс Щедрости` = generous,
  `Индекс отношения к коррупции` = corrupt,
  `Оценка риска безработицы` = unemp,
  `Индекс кредитного оптимизма` = credit,
  `Индекс страха социальных конфликтов` = conflict,
  `Индекс семьи` = fam_idx,
  `Индекс продовольственной безопасности` = food_sec,
  `Чувство технологического прогресса` = tech,
  `Чувство неравенства доходов в обществе` = inequal,
  `Среднегодовой доход (тыс.$)` = income,
  `Объем потребленного алкоголя в год (л)` = alcohol,
  `Количество членов семьи` = family,
  `Количество лет образования` = edu,
  `Доля от дохода семьи которая тратится на продовольствие, %` = food,
  `Коэффициент Джини сообщества` = gini,
  `Издержки сообщества на окружающую среду (млн.$)` = eco,
  `Охват беспроводной связи в сообществе, %` = wifi,
  `Количество смертей от вирусных и респираторных заболеваний в сообществе, тыс. человек` = deaths,
  `Волатильность потребительских цен в сообществе` = volat,
  Ощущаемое_счастье = happy,
  check.names = FALSE
)

write.xlsx(data, "happiness_survey.xlsx")
cat("Сохранено: data/happiness_survey.xlsx\n")
