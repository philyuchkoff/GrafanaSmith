# Redis Cluster template

Version: 0.2.0. Load this template when the service type is **Redis Cluster**
(redis_exporter, cluster mode). Complements the base Redis template.

## Sections

Cluster State, Slots, Keyspace, Master/Replica per Node, Failover, Commands, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Cluster state | `redis_cluster_state` (1 = ok) — should be 1 for all cluster-aware nodes |
| Slots count per node | `redis_cluster_slots_number` |
| Slots assigned | `redis_cluster_slots_assigned` — sum across nodes should == 16384 |
| Slots moving | `redis_cluster_slots_migrating` — should be 0 under normal operation |
| Cluster failures | `redis_cluster_failures_count` per node |
| Cluster nodes known | `redis_cluster_known_nodes` (per node) — should be consistent across nodes |
| Cluster bus messages | `rate(redis_cluster_messages_received_total[$__rate_interval])` / `rate(redis_cluster_messages_sent_total[$__rate_interval])` |
| Cluster links | `redis_cluster_links` — should == known_nodes - 1 (connected to all peers) |
| Master count | `count(redis_node_info{role="master"})` — should be stable |
| Replica count | `count(redis_node_info{role="replica"})` — should be >= 1 per master in production |
| Master down | `count(redis_node_info{role="master"} == 0 by (node)` — any master with flag 0 |
| Slot failover state | `count(redis_node_info{master_link_status="up"} == 0)` |
| Slots migrating (per direction) | `rate(redis_cluster_slots_migrating[$__rate_interval])` |
| Cluster bus rx/tx | `rate(redis_cluster_messages_received_total[$__rate_interval])` by node |

Also carry over Redis base template metrics:
- Connected clients per node
- Memory used % per node
- Keyspace hits/misses per node
- Command rate (but cluster-wide aggregation makes more sense here)

## Alerts

- Cluster state != ok on any node
- Slots assigned total != 16384
- Slots migrating > 0 for more than 5 minutes
- Master down (any master node flag 0)
- Replica count per master < 1 (no failover partner)
- Cluster bus message flood (indicates network partition or reshard in progress)

## Variables

`$node`, `$master_id`, `$slot_range`
