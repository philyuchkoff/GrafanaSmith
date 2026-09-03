# MongoDB template

Version: 0.2.0. Load this template when the service type is **MongoDB**
(mongodb_exporter, Percona variant).

## Sections

Overview, Operations, Latency, Replication, WiredTiger Cache, Connections, Locks, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Opcounter (insert/query/update/delete/getmore/command) | `sum by (type) (rate(mongodb_op_counters_total[$__rate_interval]))` |
| Opcounter in primary | `sum by (type) (rate(mongodb_op_counters_total{state="primary"}[$__rate_interval]))` |
| Document ops | `sum by (op) (rate(mongodb_documents_total[$__rate_interval]))` |
| Latency p99 (reads) | `histogram_quantile(0.99, sum by (le) (rate(mongodb_op_latencies_reads_latency_bucket[$__rate_interval])))` |
| Latency p99 (writes) | `histogram_quantile(0.99, sum by (le) (rate(mongodb_op_latencies_writes_latency_bucket[$__rate_interval])))` |
| Replica lag (sec) | `mongodb_rs_members_optimeDate - mongodb_rs_members_lastAppliedDate` (or `mongodb_mongod_replset_member_replication_lag` in newer versions) |
| Oplog window | `mongodb_rs_members_oplogWindow` |
| Replica member health | `mongodb_rs_members_health` (1 = healthy, 0 = down) |
| WiredTiger cache used % | `mongodb_wiredtiger_cache_bytes / mongodb_wiredtiger_cache_max_bytes * 100` |
| WiredTiger cache dirty | `mongodb_wiredtiger_cache_dirty_bytes` |
| Connections | `mongodb_connections{state="current"}` |
| Available connections | `mongodb_connections{state="available"}` |
| Connections utilization | `mongodb_connections{state="current"} / (mongodb_connections{state="current"} + mongodb_connections{state="available"}) * 100` |
| Locks wait time (global) | `rate(mongodb_locks_time_acquiring_global_seconds[$__rate_interval])` |
| Network in/out | `rate(mongodb_network_bytes_in_total[$__rate_interval])` / `rate(mongodb_network_bytes_out_total[$__rate_interval])` |

Metric families: `mongodb_op_counters_*`, `mongodb_op_latencies_*`,
`mongodb_rs_members_*`, `mongodb_wiredtiger_*`, `mongodb_connections`,
`mongodb_locks_*`, `mongodb_network_*`.

## Alerts

- Replica lag > 30s
- Primary missing (`count(mongodb_rs_members_health{member_state="PRIMARY"} == 1) == 0`)
- Oplog window < 1h (for deployments where this matters)
- WiredTiger cache utilization > 90%
- Connection utilization > 80%

## Variables

`$instance`, `$state` (primary/secondary), `$rs_state` (PRIMARY/SECONDARY/ARBITER)
