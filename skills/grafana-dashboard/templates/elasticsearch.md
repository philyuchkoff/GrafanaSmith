# Elasticsearch / OpenSearch template

Version: 0.2.0. Load this template when the service type is **Elasticsearch**
or **OpenSearch** (elasticsearch_exporter / opensearch-exporter).

## Sections

Cluster Overview, Nodes, Indices, Indexing/Search, JVM, Circuit Breaker, Thread Pools, GC, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Cluster status | `elasticsearch_cluster_health_status{color="green"}` → 1 if green, 0 otherwise |
| Active primary shards | `elasticsearch_cluster_health_active_primary_shards` |
| Unassigned shards | `elasticsearch_cluster_health_unassigned_shards` |
| Relocating shards | `elasticsearch_cluster_health_relocating_shards` |
| Data nodes count | `count(elasticsearch_nodes_stats_role_roles{role="data"} == 1)` |
| Search rate | `sum(rate(elasticsearch_indices_search_query_total[$__rate_interval]))` |
| Fetch rate | `sum(rate(elasticsearch_indices_search_fetch_total[$__rate_interval]))` |
| Indexing rate | `sum(rate(elasticsearch_indices_indexing_index_total[$__rate_interval]))` |
| Indexing latency | `rate(elasticsearch_indices_indexing_index_time_seconds_total[$__rate_interval]) / rate(elasticsearch_indices_indexing_index_total[$__rate_interval])` |
| Search latency | `rate(elasticsearch_indices_search_query_time_seconds_total[$__rate_interval]) / rate(elasticsearch_indices_search_query_total[$__rate_interval])` |
| JVM heap used % | `(elasticsearch_jvm_memory_used_bytes{area="heap"} / elasticsearch_jvm_memory_max_bytes{area="heap"}) * 100` |
| JVM non-heap used % | `(elasticsearch_jvm_memory_used_bytes{area="nonheap"} / elasticsearch_jvm_memory_max_bytes{area="nonheap"}) * 100` |
| GC time % (young) | `rate(elasticsearch_jvm_gc_collection_seconds_sum{gc="young"}[$__rate_interval]) / rate(elasticsearch_jvm_gc_collection_seconds_count{gc="young"}[$__rate_interval])` |
| GC time % (old) | `rate(elasticsearch_jvm_gc_collection_seconds_sum{gc="old"}[$__rate_interval]) / rate(elasticsearch_jvm_gc_collection_seconds_count{gc="old"}[$__rate_interval])` |
| Old GC count | `rate(elasticsearch_jvm_gc_collection_seconds_count{gc="old"}[$__rate_interval])` |
| Circuit breaker tripped | `elasticsearch_breakers_tripped` per breaker |
| Thread pool active | `elasticsearch_thread_pool_active` |
| Thread pool rejected | `elasticsearch_thread_pool_rejected` |
| Translog ops | `elasticsearch_indices_translog_operations` |
| Fielddata evictions | `increase(elasticsearch_indices_fielddata_evictions[$__rate_interval])` |

Metric families: `elasticsearch_cluster_health_*`, `elasticsearch_nodes_stats_*`,
`elasticsearch_indices_*`, `elasticsearch_jvm_*`, `elasticsearch_breakers_*`,
`elasticsearch_thread_pool_*`.

For OpenSearch, substitute `elasticsearch_` → `opensearch_` prefix in all
above expressions.

## Alerts

- Cluster red (`elasticsearch_cluster_health_status{color="red"} == 1`)
- Cluster yellow longer than 10 min
- Unassigned shards > 0 for `5m`
- Circuit breaker tripped
- Thread pool rejected rate spike
- Old GC rate above threshold (no stop-the-world on G1, but still costly)

## Variables

`$node`, `$index`, `$thread_pool`
