# Exporter Metric Compatibility Matrix

This file documents known metric renames across exporter versions so
that SKILL.md can switch PromQL expressions accordingly.

## PostgreSQL (postgres_exporter)

| Exporter version | Metric naming | Notable changes |
|:-:|---|--|
| 0.4.x | `pg_stat_database_tup_fetched`, `pg_stat_database_tup_returned` | Legacy naming with tup_ prefix |
| 0.12.x | `pg_stat_database_tuples_fetched`, `pg_stat_database_tuples_returned` | Renamed tup_ → tuples_ |
| 0.14.x+ | `pg_stat_statements_*` available via `pgss` queries | Statement-level metrics need `-pg.stat_statements` flag |

**Switch rule**: if `scrape_configs` or `up{job=...}` contains `tup_` → use
0.4.x names; if `tuples_` → use 0.12+ names.

## Redis (redis_exporter)

| Exporter version | Metric naming | Notable changes |
|:-:|---|--|
| 1.x | `redis_commands_total`, `redis_connected_slaves`, `redis_db_keys` | Original metrics |
| 2.x (prometheus-redis-exporter) | `redis_commands_duration_seconds_*` (histogram) | Added histogram support for command durations |

## Kafka

| Exporter | Metric naming |
|:-:|---|
| JMX Exporter | Configuration-dependent; typical: `kafka_server_*`, `kafka_controller_*` |
| kafka_exporter (danielqsj) | `kafka_consumergroup_lag`, `kafka_topic_partition_*`, `kafka_broker_*` |
| Strimzi operator / Cruise Control | `kafka_server_*` via JMX mBean patterns |

**Switch rule**: look at `scrape_configs` → `metrics_path`. If it points to
the Kafka exporter `/metrics`, use danielqsj-style names. If JMX, try to
infer the mBean pattern from `relabel_configs` or ask the user.

## NGINX

| Exporter | Metric naming |
|:-:|---|
| nginx-prometheus-exporter (0.x–1.x) | `nginx_http_requests_total`, `nginx_connections_*` |
| NGINX Ingress Controller (k8s) | `nginx_ingress_controller_*` — different prefix |

## PowerDNS

| Exporter | Metric naming |
|:-:|---|
| powerdns_exporter (onebig .io) | `pdns_server_*` (authoritative) |
| pdns recursor exporter | `pdns_server_*` (recursor) — same prefix but different semantics |

## Generic

No version-specific renames recorded yet.

## OpenSearch / Elasticsearch

| Exporter | Metric naming |
|:-:|---|
| elasticsearch_exporter (prometheus-community) | `elasticsearch_*` |
| OpenSearch-exporter | `opensearch_*` |

## MongoDB

| Exporter | Metric naming |
|:-:|---|
| mongodb_exporter (percona) | `mongodb_*` |
| MongoDB Atlas | `mongodb_atlas_*` |

## RabbitMQ

| Exporter | Metric naming |
|:-:|---|
| rabbitmq_exporter (kbudde) | `rabbitmq_*` |
| RabbitMQ built-in | `rabbitmq_*` |

## Patroni / PostgreSQL-HA

Patroni exposes its own REST endpoint for health. The `pg` prefix metrics
come from postgres_exporter running alongside Patroni. There is no
dedicated Patroni exporter — health is inferred from:
- `patroni_*` custom metrics if a patroni_exporter is deployed
- PostgreSQL metrics tagged with `role` labels via Patroni's metrics endpoint
