# Test fixture: Node Exporter — generic Linux host

## scrape_configs
```yaml
scrape_configs:
  - job_name: node
    metrics_path: /metrics
    static_configs:
      - targets: ['web-server-01:9100', 'web-server-02:9100']
```

## service_description
2 Linux hosts running a stateless web app, monitored with node_exporter

## context
production, Grafana 11

## expected_checks

### Mandatory root keys
- `annotations`, `description`, `editable`, `panels`, `refresh`, `schemaVersion`, `tags`, `templating`, `time`, `title`, `uid`, `version`, `grafanaSmith`

### grafanaSmith metadata
- `grafanaSmith.version` == "0.2.0"
- `grafanaSmith.template` == "node-exporter"
- `grafanaSmith.template_version` == "0.2.0"

### template variables
- Contains `$datasource`, `$job`, `$instance`, `$interval`
- Contains `$mountpoint`, `$device`, `$nic`

### schemaVersion
- `schemaVersion` == 40

### No duplicate panel IDs

### gridPos validation
- Every panel: x >= 0, w >= 1, h >= 1, x + w <= 24
- No two panels overlap

### Required sections
- CPU panels present (cpu usage %, per-mode breakdown)
- Memory panels present
- Disk panels present
- Network panels present
