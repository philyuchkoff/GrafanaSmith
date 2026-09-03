# Redis template

Version: 0.2.0. Load this template when the service type is **Redis / Redis Cluster** (redis_exporter).

## Sections

Overview, Clients, Memory, Commands, Keyspace, Persistence, Replication, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Connected clients | `redis_connected_clients` |
| Blocked clients | `redis_blocked_clients` |
| Memory used % | `redis_memory_used_bytes / redis_config_maxmemory * 100` (fallback `redis_memory_used_bytes`) |
| Memory peak | `redis_memory_peak_bytes` |
| Command rate | `sum(rate(redis_commands_total[$__rate_interval])) by (cmd)` |
| Keyspace hits / misses | `rate(redis_keyspace_hits_total[$__rate_interval])` / `rate(redis_keyspace_misses_total[$__rate_interval])` |
| Hit ratio | `rate(redis_keyspace_hits_total[$__rate_interval]) / (rate(redis_keyspace_hits_total[$__rate_interval]) + rate(redis_keyspace_misses_total[$__rate_interval]))` |
| Connected replica count | `redis_connected_slaves` |

## Alerts

- memory saturation (`redis_memory_used_bytes / maxmemory > 0.9`)
- evictions rate (`rate(redis_evicted_keys_total[...])` above baseline)
- hit ratio drop
- replication backlog / blocked clients
- RDB/AOF failures

## Variables

`$role` (master/replica), `$instance`