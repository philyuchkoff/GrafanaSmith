# PostgreSQL template

Load this template when the service type is **PostgreSQL** (postgres_exporter).

## Sections

Overview, Connections, Queries, Replication, Locks, Resources (Node), WAL/Backups

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Connections in use % | `sum(pg_stat_database_numbackends) / sum(pg_settings_max_connections) * 100` |
| Query latency | `pg_stat_database_xact_commit` / `rate()` based; see exporter-specific `pg_stat_statements` if exposed |
| Commits / Rollbacks | `sum(rate(pg_stat_database_xact_commit[$__rate_interval]))` / `sum(rate(pg_stat_database_xact_rollback[$__rate_interval]))` |
| Replication lag (bytes) | `pg_replication_lag` (or `pg_stat_replication_*` when exporter exposes it) |
| Deadlocks | `sum(rate(pg_stat_database_deadlocks[$__rate_interval]))` |
| Cache hit ratio | `sum(rate(pg_stat_database_blks_hit[$__rate_interval])) / (sum(rate(pg_stat_database_blks_hit[$__rate_interval])) + sum(rate(pg_stat_database_blks_read[$__rate_interval])))` |
| Longest query | `max(pg_stat_activity_duration (secs))` if exposed |

> Metric names differ across postgres_exporter versions. Base the panel on
> metrics confirmed present in `scrape_configs`/`up{job=...}`; default to
> the `pg_stat_database`, `pg_stat_replication`, `pg_stat_activity`,
> `pg_locks`, `pg_stat_user_tables` families.

## Alerts

- connection saturation (`pg_stat_database_numbackends / pg_settings_max_connections > 0.9`)
- replication lag (`pg_replication_lag > 1MB` or seconds-based threshold)
- cache hit ratio (< 0.95)
- transaction wraparound / long-running queries
- deadlocks rate above baseline

## Variables

`$role` (primary/replica), `$datname`, `$instance`