# Node Exporter template (generic host)

Load this template when the service type is any **Linux host** (node_exporter).

## Sections

CPU, Memory, Disk, Network, Filesystems, Kernel, Processes

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| CPU usage % | `100 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[$__rate_interval])) * 100` |
| CPU per mode | `sum by (mode) (rate(node_cpu_seconds_total[$__rate_interval]))` |
| Memory used % | `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` |
| Memory breakdown | `node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes` |
| Swap usage % | `node_memory_SwapFree_bytes / node_memory_SwapTotal_bytes * 100` |
| Disk usage % | `(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100` |
| Disk read/write | `rate(node_disk_read_bytes_total[$__rate_interval])` / `rate(node_disk_write_bytes_total[$__rate_interval])` |
| Disk I/O utilization | `rate(node_disk_io_time_seconds_total[$__rate_interval])` |
| Network in/out | `rate(node_network_receive_bytes_total[$__rate_interval])` / `rate(node_network_transmit_bytes_total[$__rate_interval])` |
| Load average vs cores | `node_load1 / count(node_cpu_seconds_total{mode="idle"})` |
| Processes blocked | `node_procs_blocked` / `node_procs_running` |

## Alerts

- CPU saturation, memory pressure
- disk space below threshold, disk I/O wait
- swap exhaustion, network error packet growth

## Variables

`$instance`, `$mountpoint`, `$device`, `$nic`