# Kubernetes Pods template (kube-state-metrics + cAdvisor)

Version: 0.2.0. Load this template when the service type is **Kubernetes pods / containers**
(kube-state-metrics + cAdvisor node exporter).

## Sections

Pod Overview, CPU/Memory, Restarts, Network, Volumes, Status

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Pod CPU usage | `sum by (pod) (rate(container_cpu_usage_seconds_total[$__rate_interval]))` |
| CPU throttling | `sum by (pod) (rate(container_cpu_cfs_throttled_seconds_total[$__rate_interval]))` |
| Memory usage | `sum by (pod) (container_memory_working_set_bytes)` |
| Memory limit % | `sum by (pod) (container_memory_working_set_bytes) / sum by (pod) (kube_pod_container_resource_limits{resource="memory"}) * 100` |
| Restarts | `max by (pod) (kube_pod_container_status_restarts_total)` |
| Network | `rate(container_network_receive_bytes_total[$__rate_interval])` / `rate(container_network_transmit_bytes_total[$__rate_interval])` |
| Phase | `kube_pod_status_phase` |

## Alerts

- CrashLoopBackOff (`kube_pod_container_status_waiting_reason == "CrashLoopBackOff"`)
- OOMKilled (`kube_pod_container_status_last_terminated_reason == "OOMKilled"`)
- CPU throttling, high restart count
- pending pods not scheduled

## Variables

`$namespace`, `$pod`, `$container`, `$node`