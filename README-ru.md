# GrafanaSmith

> Набор инструментов для SRE, которые создают дашборды Grafana для production-сервисов.

GrafanaSmith — это скилл для превращения Prometheus `scrape_configs` и краткого описания сервиса
в production-ready дашборды Grafana.

Центральный элемент — скилл
[`grafana-dashboard`](skills/grafana-dashboard/SKILL.md): opinionated-генератор, который знает
метрики, панели и переменные, важные для самых распространённых инфраструктурных компонентов.
Скилл написан в стандартном формате `SKILL.md` и **не привязан к конкретному движку**: он
работает в [opencode](https://opencode.ai), Claude Code, Cursor и в любом другом агенте,
умеющем загружать скиллы из файла `SKILL.md`.

## Зачем GrafanaSmith

Большинство дашбордов Grafana в дикой природе страдают от одних и тех же
проблем:

- панели без внятного нарратива (нет Golden Signals);
- `rate(node_cpu_seconds_total[5m])` копипастится везде, даже когда
  сервис не упирается в CPU;
- имена инстансов захардкожены вместо объявления шаблонных переменных;
- пороги выбраны случайно, без привязки к SLO.

GrafanaSmith превращает SRE best practices (RED, USE, Golden Signals) в
повторяемый workflow, чтобы каждый выкатываемый дашборд имел одинаковый формат и одинаковую планку качества.

## Скилл `grafana-dashboard`

Скилл принимает на вход некоторые данные и выдаёт Grafana-совместимый JSON дашборд:

| Вход | Обязательно | Описание |
|------|--------------|----------|
| `scrape_configs` | да | Определения Prometheus job (job_name, static_configs, relabel_configs, metrics_path) |
| `service_description` | да | Что за сервис и как развёрнут (single, cluster, primary-replica, sharded...) |
| `context` | нет | Окружение, ожидаемая нагрузка, SLO, наличие Alertmanager |

Скилл работает в двух режимах:

- **create** — сгенерировать новый дашборд с нуля.
- **iterate** — доработать существующий дашборд, не переписывая его.

### Встроенные шаблоны сервисов

Скилл поставляется с девятью шаблонами в
[`skills/grafana-dashboard/templates/`](skills/grafana-dashboard/templates/):

- PostgreSQL
- MySQL / MariaDB
- Redis
- Kafka
- NGINX
- PowerDNS Authoritative
- Node Exporter
- Kubernetes Pods (kube-state-metrics + cAdvisor)
- Generic / неизвестный сервис (fallback на Golden Signals)

Каждый шаблон задаёт секции панелей, **готовые PromQL-выражения**, пороги
алертов и шаблонные переменные, осмысленные для данного сервиса. Новый
сервис добавляется одним файлом `templates/<service>.md` по образцу —
менять сам скилл не нужно.

### Что генерирует скилл

Каждый дашборд, сгенерированный скиллом, содержит:

- **Overview row** с Golden Signals (QPS, latency p99, error rate, saturation) в виде `stat`-панелей.
- **Traffic / Queries row** с time-series разбивкой по лейблам.
- **Saturation / Resources row** (CPU, memory, disk, network при наличии node_exporter).
- **Errors & latency distribution row** с heatmap'ами и p50/p95/p99.
- **Topology row** (если у сервиса нетривиальная топология).
- **Переменные шаблонов**: `$datasource`, `$job`, `$instance`, `$interval` плюс профильные (`$role`, `$datname`, `$topic`, `$consumergroup`, `$namespace`, ...).
- **Опционально**: thresholds на критичных панелях, отдельные правила Prometheus для Alertmanager, аннотации деплоев.

Генерируемый JSON следует современным конвенциям Grafana:

- `schemaVersion` 39 (Grafana 10), 40 (Grafana 11), 41 (Grafana 12), 42 (Grafana 13+ — финальная схема v1);
- `gridPos` валидируется по реальным правилам сетки (`x + w <= 24`, без пересечений);
- `$__rate_interval` во всех окнах `rate()` (фиксированные `[5m]` — только в alert-правилах);
- `unit` задан на каждой панели (`reqps`, `s`, `percentunit`, `bytes`, ...);
- `legendFormat` на каждой серии;
- стабильная конвенция `uid` (`<environment>-<service>-<purpose>`).

В скилл встроены эталонные панели (stat, timeseries, table), чтобы каждая
сгенерированная панель следовала одному и тому же контракту полей, а
после выдачи JSON скилл просит импортировать дашборд и сообщить об
ошибках — для второй итерации.

## Установка

Скилл — это файл `SKILL.md` плюс директория `templates/`. Любой агент,
умеющий загружать скиллы (opencode, Claude Code, Cursor, ...),
подхватит его из соответствующей директории.

### opencode

```bash
git clone https://github.com/philyuchkoff/GrafanaSmith.git
ln -s "$(pwd)/GrafanaSmith/skills/grafana-dashboard" \
      ~/.config/opencode/skills/grafana-dashboard
```

Перезапустите opencode, чтобы новый скилл загрузился.

### Claude Code / Cursor

```bash
git clone https://github.com/philyuchkoff/GrafanaSmith.git
mkdir -p ~/.claude/skills
cp -R GrafanaSmith/skills/grafana-dashboard ~/.claude/skills/
```

(Claude Code загружает `~/.claude/skills/<name>/SKILL.md`; Cursor читает
`.cursor/skills/` в проекте или в пользовательской директории.)

### Установка только для проекта

Чтобы использовать скилл только внутри одного репозитория, скопируйте
его в проектную директорию скиллов (например, `.opencode/skills/` для
opencode):

```bash
mkdir -p .opencode/skills
cp -R skills/grafana-dashboard .opencode/skills/
```

## Использование

Запустите скилл, описав сервис и вставив scrape config:

> «Сделай дашборд Grafana для нашего PostgreSQL 14 — кластер 1 primary,
> 2 replica, production, ~5000 QPS. Вот scrape config: ...»

Скилл сделает следующее:

1. Распарсит scrape config и определит доступные метрики, структуру
   лейблов и роли инстансов.
2. Загрузит подходящий шаблон из `templates/` и сопоставит его с
   описанием сервиса.
3. Задаст не более 3-4 уточняющих вопросов (топология, SLI, алертинг,
   временная агрегация), если что-то неоднозначно.
4. Выдаст полный JSON дашборда плюс краткое описание структуры панелей,
   после чего попросит импортировать его и сообщить об ошибках.

Для доработки существующего дашборда:

> «Добавь секцию Replication и сделай порог error rate строже: 80/95»

Скилл сохранит существующие панели нетронутыми и применит только
запрошенное изменение, показав diff в конце.

## Структура репозитория

```
GrafanaSmith/
├── README.md                          # en
├── README-ru.md                       # ru
└── skills/
    └── grafana-dashboard/
        ├── SKILL.md                   # собственно скилл
        └── templates/                 # шаблоны сервисов (PromQL, алерты, переменные)
            ├── postgresql.md
            ├── mysql.md
            ├── redis.md
            ├── kafka.md
            ├── nginx.md
            ├── powerdns.md
            ├── node-exporter.md
            ├── kubernetes-pods.md
            └── generic.md
```

## Конвенции

Когда добавляете новый шаблон сервиса, соблюдайте правила:

1. **Берите метрики, которые реально эмитит экспортер.** Сверяйтесь с
   документацией экспортера, не выдумывайте имена метрик.
2. **Используйте `$__rate_interval` в окнах `rate()`** — дашборд будет
   корректно работать при любом уровне зума. Фиксированные окна (`[5m]`)
   допустимы только в Prometheus alert-правилах, где `$__rate_interval`
   не существует.
3. **Всегда задавайте `legendFormat`** с интерполяцией хотя бы одного лейбла.
4. **Пороги должны быть привязаны к SLO или к сигналу из реальных
   инцидентов.** Случайные пороги — это шум.
5. **Группируйте панели в rows** с `collapsed: false`, чтобы дашборд
   оставался навигируемым.
6. **Переменные — snake_case и регистрозависимые.** `$replica_type`, а не
   `$ReplicaType`.
7. **Задавайте `unit` на каждой панели** и следуйте конвенции `uid`
   `<environment>-<service>-<purpose>`.

## Участие в проекте

Pull request'ы приветствуются. Самые полезные дополнения:

- Новые шаблоны сервисов (Cassandra, MongoDB, RabbitMQ, Elasticsearch,
  ClickHouse, Envoy, HAProxy, ...) — файлом `templates/<service>.md`.
- Лучшие дефолты для порогов на основе реальных SLO.
- Дополнительные паттерны PromQL для трудноизвлекаемых сигналов.
- Переводы документации.

Открывайте PR с новым шаблоном в
`skills/grafana-dashboard/templates/<service>.md`.

## Дорожная карта

- [ ] Шаблонные drill-down дашборды (cluster → node → query).
- [ ] Автогенерация файлов Prometheus alert-правил вместе с дашбордом.
- [ ] Манифесты provisioning (Grafana provisioning, Terraform).
- [ ] Линтер, валидирующий JSON дашборда по конвенциям.

## Лицензия

MIT. См. файл [`LICENSE`](LICENSE).
