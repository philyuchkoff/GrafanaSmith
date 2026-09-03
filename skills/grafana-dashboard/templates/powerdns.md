# PowerDNS Authoritative template

Version: 0.2.0. Load this template when the service type is **PowerDNS Authoritative** (powerdns-exporter).

## Sections

Overview, Queries, Cache, Backend, Latency, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Query rate | `sum(rate(pdns_server_queries_total[$__rate_interval])) by (opcode, rcode)` |
| Uptime | `pdns_server_uptime` |
| Cache size | `pdns_server_cache_size` |
| Cache hit / miss | `rate(pdns_server_cache_hits_total[$__rate_interval])` / `rate(pdns_server_cache_misses_total[$__rate_interval])` |
| Backend errors | `rate(pdns_server_backend_query_errors_total[$__rate_interval])` |
| Latency | `pdns_server_latency_seconds` gauge / `histogram_quantile` if buckets exposed |

Metric families: `pdns_server_*`, `pdns_recursor_*`, `pdns_cache_*`,
`pdns_backend_*`.

## Alerts

- query rate anomaly
- cache miss ratio growth
- backend errors above baseline
- latency p99 above threshold

## Variables

`$instance`