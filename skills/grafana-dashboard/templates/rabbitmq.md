# RabbitMQ template

Version: 0.2.0. Load this template when the service type is **RabbitMQ**
(rabbitmq_exporter by kbudde, or RabbitMQ built-in Prometheus plugin).

## Sections

Overview, Queues, Messages, Connections, Channels, Memory, Erlang VM, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Messages ready | `sum by (queue) (rabbitmq_queue_messages_ready)` |
| Messages unacked | `sum by (queue) (rabbitmq_queue_messages_unacked)` |
| Total queue messages | `rabbitmq_queue_messages` (ready + unacked) |
| Queue consumers | `rabbitmq_queue_consumers` |
| Message publish rate | `sum(rate(rabbitmq_channel_messages_published_total[$__rate_interval]))` |
| Message deliver rate | `sum(rate(rabbitmq_channel_messages_delivered_total[$__rate_interval]))` |
| Message ack rate | `sum(rate(rabbitmq_channel_messages_acked_total[$__rate_interval]))` |
| Message redeliver rate | `sum(rate(rabbitmq_channel_messages_redelivered_total[$__rate_interval]))` |
| Unroutable messages | `sum(rate(rabbitmq_channel_messages_unroutable_total[$__rate_interval]))` |
| Connections per vhost | `rabbitmq_connections` by vhost |
| Channels | `rabbitmq_channels` |
| Memory used | `rabbitmq_memory_used_bytes` |
| Memory watermark % | `rabbitmq_memory_used_bytes / rabbitmq_memory_limit_bytes * 100` |
| Disk free | `rabbitmq_disk_space_available_bytes` |
| Erlang processes | `rabbitmq_processors_used` |
| Erlang Schedulers | `rabbitmq_schedulers_online` |
| Erlang run queue | `rabbitmq_schedulers_run_queue` |

Metric families: `rabbitmq_queue_*`, `rabbitmq_channel_messages_*`,
`rabbitmq_connections`, `rabbitmq_channels`, `rabbitmq_vhost_*`,
`rabbitmq_memory_*`, `rabbitmq_erlang_*`.

For the RabbitMQ built-in plugin (rabbitmq_prometheus), metric names
include `rabbitmq_detailed_*`, `rabbitmq_identity_info` — adapt prefixes
accordingly.

## Alerts

- Memory watermark > 90%
- Disk free below threshold (publishers get blocked)
- Queue growth too fast (rate exceeds consumption rate)
- Queue has > 0 consumers = 0 (starved consumer), or `consumers == 0`
- Unroutable message rate spike
- Erlang run queue saturation

## Variables

`$queue`, `$vhost`, `$instance`
