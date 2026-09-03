# Generic / unknown service template

Version: 0.2.0. Load this template when the service type does not match a known exporter, or
the type is ambiguous and cannot be determined from `scrape_configs`.

## Sections

Overview (Golden Signals), Saturation, Resources (Node), Errors

## Approach

1. Derive the metric namespace from the `job_name` prefix and the metrics
   listed in the scrape config.
2. Reuse the Golden Signals stat panels from the skill's Overview row:
   - Throughput: `sum(rate(<metric>_total[$__rate_interval]))` where
     `<metric>` is the service's primary counter.
   - Latency p99: `histogram_quantile(0.99, sum by (le) (rate(<name>_seconds_bucket[$__rate_interval])))`.
   - Error rate: ratio over the sub-`status=~"5..|error"` series.
   - Saturation: whatever gauge best reflects capacity (connections, queue,
     lag, disk).
3. Fall back to the Node Exporter resource row if the service runs on
   hosts that also scrape node_exporter under the same `$instance`.

## Alerts

- error rate, saturation, latency above thresholds
- `up == 0` for the job

## Variables

`$instance` (+ `$job` derived from label_values)