# Матрица совместимости версий экспортеров

В этом файле зафиксированы все известные переименования метрик между
версиями экспортеров, чтобы SKILL.md мог автоматически подставлять
правильные PromQL-выражения.

## PostgreSQL (postgres_exporter)

| Версия экспортера | Имена метрик | Примечания |
|:-:|---|--|
| 0.4.x | `pg_stat_database_tup_fetched`, `pg_stat_database_tup_returned` | Устаревшее именование с префиксом `tup_` |
| 0.12.x | `pg_stat_database_tuples_fetched`, `pg_stat_database_tuples_returned` | Переименовано `tup_` → `tuples_` |
| 0.14.x+ | `pg_stat_statements_*` доступны через `pgss` | Метрики уровня statement требуют флаг `--pg.stat_statements` |

**Правило выбора**: если в `scrape_configs` или `up{job=...}` встречается
`tup_` → использовать имена 0.4.x; если `tuples_` → имена 0.12+.

## Redis (redis_exporter)

| Версия экспортера | Имена метрик | Примечания |
|:-:|---|--|
| 1.x | `redis_commands_total`, `redis_connected_slaves`, `redis_db_keys` | Исходные метрики |
| 2.x (prometheus-redis-exporter) | `redis_commands_duration_seconds_*` (гистограмма) | Добавлена гистограмма продолжительности команд |

## Kafka

| Экспортер | Имена метрик |
|:-:|---|
| JMX Exporter | Зависят от конфигурации; обычно: `kafka_server_*`, `kafka_controller_*` |
| kafka_exporter (danielqsj) | `kafka_consumergroup_lag`, `kafka_topic_partition_*`, `kafka_broker_*` |
| Strimzi operator / Cruise Control | `kafka_server_*` через JMX mBean-шаблоны |

**Правило выбора**: смотреть `scrape_configs` → `metrics_path`. Если
указывает на kafka_exporter `/metrics` — использовать danielqsj-стиль
имен. Если JMX — попытаться определить mBean-шаблон из `relabel_configs`
или спросить пользователя.

## NGINX

| Экспортер | Имена метрик |
|:-:|---|
| nginx-prometheus-exporter (0.x–1.x) | `nginx_http_ickets_total`, `nginx_connections_*` |
| NGINX Ingress Controller (k8s) | `nginx_ingress_controller_*` — другой префикс |

## PowerDNS

| Экспортер | Имена метрик |
|:-:|---|
| powerdns_exporter (onebig .io) | `pdns_server_*` (authoritative) |
| pdns recursor exporter | `pdns_server_*` (recursor) — тот же префикс, другая семантика |

## Generic

Версионо-зависимых переименований пока не зафиксировано.

## OpenSearch / Elasticsearch

| Экспортер | Имена метрик |
|:-:|---|
| elasticsearch_exporter (prometheus-community) | `elasticsearch_*` |
| OpenSearch-exporter | `opensearch_*` |

## MongoDB

| Экспортер | Имена метрик |
|:-:|---|
| mongodb_exporter (percona) | `mongodb_*` |
| MongoDB Atlas | `mongodb_atlas_*` |

## RabbitMQ

| Экспортер | Имена метрик |
|:-:|---|
| rabbitmq_exporter (kbudde) | `rabbitmq_*` |
| RabbitMQ built-in | `rabbitmq_*` |

## Patroni / PostgreSQL-HA

У Patroni есть собственный REST-эндпоинт для проверки здоровья.
Метрики с префиксом `pg` идут от postgres_exporter, работающего
рядом с Patroni. Выделенного Patroni-exporter'а не существует —
здоровье определяется по:
- кастомным метрикам `patroni_*`, если развёрнут patroni_exporter;
- метрикам PostgreSQL с тегом `role`, получаемым через
  метрикс-эндпоинт Patroni.
