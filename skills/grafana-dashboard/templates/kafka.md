# Kafka template

Load this template when the service type is **Kafka** (JMX / kafka_exporter).

## Sections

Cluster, Brokers, Topics, Partitions, Producers, Consumers, Lag, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Broker status | `up` / `kafka_broker_up` |
| Controller count | `kafka_controller_kafkacontroller_activecontrollercount` |
| Under-replicated partitions | `kafka_server_replicamanager_underreplicatedpartitions` |
| In-sync replicas (ISR) shrink | `kafka_server_replicamanager_insyncreplicas_total` trend |
| Consumer lag | `sum by (topic, consumer_group) (kafka_consumergroup_lag)` |
| Partition offset | `rate(kafka_broker_topic_partition_..._offset[$__rate_interval])` |

Metric families to rely on: `kafka_server_*`, `kafka_topic_partition_*`,
`kafka_consumergroup_lag`, `kafka_log_log_size`. Names vary by exporter
(JMX vs kafka_exporter) — confirm against `up{job=...}` labels first.

## Alerts

- consumer lag above threshold (per consumer group)
- under-replicated partitions > 0
- ISR shrink / controller count drift
- broker down (`up == 0`)

## Variables

`$topic`, `$consumergroup`, `$instance`