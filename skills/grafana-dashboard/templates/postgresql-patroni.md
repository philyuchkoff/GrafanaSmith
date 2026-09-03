# Patroni / PostgreSQL-HA template

Version: 0.2.0. Load this template when the service type is **PostgreSQL HA**
managed by **Patroni** (Kubernetes or bare-metal). Extends the base PostgreSQL
template with Patroni-specific metrics.

## Sections

Cluster Status, Leader Election, PostgreSQL (from postgres_exporter), Sync Replication, Resources

## Key metrics & PromQL

Patroni exposes its own metrics (optional, if a patroni_exporter or
service monitor is deployed). When not available, infer cluster health
from PostgreSQL metrics tagged by `role`.

| Panel | PromQL |
|-------|--------|
| Cluster healthy | `patroni_cluster_unlocked` (1 = unlocked, writes allowed) or derived from `pg_is_in_recovery` on the primary |
| Primary count | `count(pg_is_in_recovery == 0)` — should be exactly 1 |
| Replicas in sync | `count(pg_is_in_recovery == 1)` |
| Patroni version | `patroni_version` info metric |
| Replication lag (bytes) | `pg_stat_replication_replay_lag_bytes` or `pg_replication_lag` per replica |
| Replication lag (seconds) | `pg_stat_replication_replay_lag` when available |
| wal_position / replay bytes | `rate(pg_stat_replication_pg_wal_replay_bytes[$__rate_interval])` trending |
| DCS last update age | Seconds since last `patroni_dcs_last_update` — should be < TTL |
| Sync standby count | `count(pg_stat_replication_sync_state == "sync")` |
| Leader changes (rate) | `changes(patroni_cluster_unlocked[1m])` — any change > 0 indicates failover |
| Timeline divergence | `pg_control_checkpoint_timeline` mismatch across instances |

In the absence of Patroni-specific metrics:
- Infer cluster health from `pg_is_in_recovery` across instances
- Infer replication lag from `pg_stat_replication_*` on the primary

## Alerts

- Primary mismatch: `count(pg_is_in_recovery == 0) != 1`
- No sync standby when `synchronous_commit = on`
- Replication lag > threshold
- DCS TTL expired / no DCS heartbeat
- Frequent leader changes (flapping detection)

## Variables

`$role` (primary/replica), `$datname`, `$instance`

## Notes

- This template should be used alongside, not instead of, the PostgreSQL
  template — the PG template covers queries, locks, cache, WAL.
- In a composite dashboard, PostgreSQL and Patroni sections sit next to eachother.
