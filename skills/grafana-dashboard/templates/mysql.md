# MySQL / MariaDB template

Version: 0.2.0. Load this template when the service type is **MySQL / MariaDB** (mysqld_exporter).

## Sections

Overview, Connections, Queries, InnoDB, Replication, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Connections | `mysql_global_status_threads_connected` / `mysql_global_variables_max_connections` |
| Connection errors | `rate(mysql_global_status_aborted_connects[$__rate_interval])` |
| Queries per second | `rate(mysql_global_status_queries[$__rate_interval])` |
| Threads running | `mysql_global_status_threads_running` |
| InnoDB buffer pool hit | `rate(mysql_global_status_innodb_buffer_pool_read_requests[$__rate_interval]) / (rate(mysql_global_status_innodb_buffer_pool_read_requests[$__rate_interval]) + rate(mysql_global_status_innodb_buffer_pool_reads[$__rate_interval]))` |
| Replica lag (seconds) | `mysql_slave_status_seconds_behind_master` |
| InnoDB history list length | `mysql_global_status_history_list_length` |

Base panels on the `mysql_global_status_*`, `mysql_global_variables_*`,
`mysql_innodb_*`, `mysql_slave_status_*` families present in the scrape.

## Alerts

- connections near `max_connections`
- `threads_running` saturation
- replica lag above threshold
- InnoDB history list length growth

## Variables

`$role`, `$instance`