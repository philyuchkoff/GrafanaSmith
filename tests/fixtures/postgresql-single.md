# Test fixture: PostgreSQL single instance

## scrape_configs
```yaml
scrape_configs:
  - job_name: postgresql
    metrics_path: /metrics
    static_configs:
      - targets: ['pg-primary:9187']
```

## service_description
PostgreSQL 14, single instance, staging, postgres_exporter 0.12+

## context
staging, low load, no Alertmanager, Grafana 10

## expected_checks

### Mandatory root keys
- `annotations`, `description`, `editable`, `panels`, `refresh`, `schemaVersion`, `tags`, `templating`, `time`, `title`, `uid`, `version`, `grafanaSmith`

### grafanaSmith metadata
- `grafanaSmith.version` == "0.2.0"
- `grafanaSmith.template` == "postgresql"
- `grafanaSmith.template_version` == "0.2.0"
- `grafanaSmith.mode` == "create"
- `grafanaSmith.datasource_type` == "prometheus"
- `grafanaSmith.generated_at` is a valid ISO 8601 string

### schemaVersion
- `schemaVersion` == 39

### template variables
- Contains `$datasource` (type: datasource)
- Contains `$job` (type: query)
- Contains `$instance` (type: query)
- Contains `$interval` (type: interval)
- Contains `$role` (type: query)
- Contains `$datname` (type: query)

### No duplicate panel IDs
- All panel `id` values are unique

### gridPos validation
- Every panel: x >= 0, w >= 1, h >= 1, x + w <= 24
- No two panels overlap

### datasource references
- Every panel has `datasource: { "type": "prometheus", "uid": "${datasource}" }`

### Required sections present
- At least one panel containing "Overview" or "Status" in the title
- At least one panel for connections or QPS
