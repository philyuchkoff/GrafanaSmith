# NGINX template

Version: 0.2.0. Load this template when the service type is **NGINX** (nginx-prometheus-exporter / stub_status).

## Sections

Overview, Connections, Requests, Upstream, Cache, Resources

## Key metrics & PromQL

| Panel | PromQL |
|-------|--------|
| Requests per second | `sum(rate(nginx_http_requests_total[$__rate_interval]))` |
| Requests by status | `sum by (status) (rate(nginx_http_requests_total[$__rate_interval]))` |
| 5xx error rate | `sum(rate(nginx_http_requests_total{status=~"5.."}[$__rate_interval])) / sum(rate(nginx_http_requests_total[$__rate_interval]))` |
| Active connections | `nginx_connections_active` |
| Connection accepted / handled | `rate(nginx_connections_accepted_total[$__rate_interval])` / `rate(nginx_connections_handled_total[$__rate_interval])` |
| Upstream response time | `nginx_upstream_seconds (summary)` → `histogram_quantile` if exposed |

## Alerts

- 5xx rate above threshold
- upstream failures (`nginx_upstream_server_on_offline` / errors)
- active connections saturation
- request rate anomaly (spike/drop)

## Variables

`$upstream`, `$instance`