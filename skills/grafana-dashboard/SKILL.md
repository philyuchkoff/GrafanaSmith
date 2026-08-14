---
name: grafana-dashboard
label: "Grafana Dashboard Generator"
description: "Senior SRE for designing and generating production-ready Grafana dashboards from scrape_configs and a service description. Use when creating, refining, or extending a Grafana dashboard for PostgreSQL, MySQL, Redis, Kafka, NGINX, PowerDNS, Node Exporter, and other typical services. Triggers: grafana dashboard, create dashboard, generate dashboard, refine dashboard, extend dashboard, dashboard for <service>."

trigger: |
  Activated by:
  - Direct requests: "make a grafana dashboard", "write a dashboard", "grafana dashboard", "generate a dashboard"
  - Providing scrape_configs (or job_name/metrics_path) and a service description
  - Iteration requests: "refine", "extend", "fix", "simplify", "add section", "remove section"
  - Mentioning specific services together with "dashboard" or "monitoring"

parameters:
  scrape_configs:
    type: string
    description: Prometheus configuration (job_name, static_configs, relabel_configs, metrics_path). May be YAML, JSON, or a simple list of jobs.
    required: true
  service_description:
    type: string
    description: "Service description: type (PostgreSQL, Redis, Kafka...), architecture (single/cluster/replication), criticality"
    required: true
  context:
    type: string
    description: "Additional context: environment (prod/staging), expected load, SLO, presence of Alertmanager"
    required: false
    default: ""
  dashboard_action:
    type: choice
    description: Action to perform on the dashboard
    default: create
    choices: [create, iterate, fix, add_section, remove_section]
  existing_dashboard:
    type: string
    description: Existing dashboard JSON (for iterate/fix mode)
    required: false
    default: ""
  datasource:
    type: choice
    description: Datasource type
    default: prometheus
    choices: [prometheus, victoria_metrics, mimir, thanos]

validated_memory:
  service_type:
    description: Identified service type (postgresql, redis, kafka, nginx, powerdns, generic)
    validation: Matches one of the SERVICE_TEMPLATES keys
  topology:
    description: Service topology (single/primary-replica/cluster/sharded)
    validation: "Determined through relabel_configs and description"
  instance_roles:
    description: Instance roles inferred from labels (primary/replica/worker/leader)
    validation: Non-empty list when a cluster is present
  key_sli:
    description: Key SLIs for the service (latency, error_rate, throughput, saturation)
    validation: "2-4 metrics from Golden Signals / RED / USE"
  previous_version:
    description: Previous dashboard version (for iterations)
    validation: Full JSON with preserved panels/templating structure
---

## Roles and modes

The skill operates in **two primary modes**, determined by the
`dashboard_action` parameter or the dialog context:

### Mode 1: Create (`dashboard_action: create`)

Full cycle from `scrape_configs` to a ready-to-import dashboard JSON.

### Mode 2: Iterate (`dashboard_action: iterate|fix|add_section|remove_section`)

Modifies an existing dashboard while preserving the previous version's
context. **Do not regenerate the dashboard from scratch** — apply only the
requested changes.

---

## Input

### Required

- `scrape_configs` — Prometheus configuration for the service (job_name,
  static_configs, relabel_configs, metrics_path).
- `service_description` — what the service is and how it is architected.

### Optional

- `context` — environment, load, SLO, presence of Alertmanager, datasource.
- `existing_dashboard` — current JSON, if a dashboard already exists.
- `datasource` — datasource type (default `prometheus`).

### Input example

```yaml
scrape_configs:
  - job_name: postgresql
    metrics_path: /metrics
    static_configs:
      - targets: ['pg-primary:9187', 'pg-replica-1:9187', 'pg-replica-2:9187']
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_role]
        target_label: role

service_description: "PostgreSQL 14, cluster with 1 primary + 2 replicas, Highload"
context: "production, ~5000 QPS, SLO 99.95%, Alertmanager in place"
```

---

## Analysis phase

### Step 1: Parse scrape_configs

Extract from the configuration:

1. **Available metrics** — determined by `metrics_path` and known exporters:
   - `postgres_exporter` → `pg_*`
   - `redis_exporter` → `redis_*`
   - `kafka_exporter` → `kafka_*`
   - `node_exporter` → `node_*`
   - `nginx-prometheus-exporter` → `nginx_*`
   - `mysqld_exporter` → `mysql_*`
   - `powerdns-exporter` → `pdns_*`
2. **Label structure** — `instance`, `job`, and custom ones via
   `relabel_configs` (`role`, `env`, `cluster`, `shard`, `datname`, etc.).
3. **Instance patterns** — primary/replica/worker/leader — extracted from
   labels produced via relabel.
4. **Multi-tenancy** — presence of `namespace`, `tenant`, `cluster` labels.

### Step 2: Identify the service type

Based on `service_description`, pick a template from `SERVICE_TEMPLATES`
(see below). If the type is ambiguous, ask **one clarifying question**.

### Step 3: Determine topology

Possible values:

- `single` — standalone instance
- `primary-replica` — master-slave replication
- `cluster` — peer nodes (Cassandra, MongoDB replica set)
- `sharded` — sharding (MongoDB sharded cluster, Vitess)
- `stateless` — pool of identical instances behind a load balancer

---

## Service templates

Templates live as separate files under `templates/` (relative to this
skill's directory). **Before generating for a service, read the matching
template file** so the panels, PromQL, and thresholds match the exporter
actually in use.

| Service | Template file |
|---------|---------------|
| PostgreSQL | `templates/postgresql.md` |
| MySQL / MariaDB | `templates/mysql.md` |
| Redis | `templates/redis.md` |
| Kafka | `templates/kafka.md` |
| NGINX | `templates/nginx.md` |
| PowerDNS Authoritative | `templates/powerdns.md` |
| Node Exporter (linux host) | `templates/node-exporter.md` |
| Kubernetes Pods | `templates/kubernetes-pods.md` |
| Generic / unknown | `templates/generic.md` |

Each template defines: panel **Sections**, **Key metrics & PromQL**
(ready-to-use expressions), **Alerts** (Prometheus rules), and
**Variables**. Always verify metric names against the exporter version
and the actual `scrape_configs` before emitting JSON — exporter metric
families vary (e.g. postgres_exporter, JMX vs kafka_exporter). To add a
template for a new service, create `templates/<service>.md` following the
same layout.

---

## Dialog strategy

### Principles

- **Use the `question` tool** to ask — do not ask in plain chat text. Offer
  the user concrete choices (`topology`, `primary/replica`, `SLI`, ...) so
  answers are fast.
- **No more than 3-4 questions** in a single round.
- **Questions by priority**: first things that change the dashboard
  structure (topology), then content (SLI), then details (aggregations,
  annotations).
- **If data is sufficient — don't ask**: for example, if `relabel_configs`
  clearly exposes `role: primary/replica`, do not ask about replication.
- **One question at a time**: do not compose a questionnaire.

### Question flow (if needed)

1. **Service discovery**
   - "Is this a cluster or a standalone?" (only if not obvious from
     `scrape_configs`)
   - "If a cluster — how are instance roles identified? (is there a
     `role` / `instance_type` label?)"

2. **Business metrics**
   - "Which SLIs are critical for the business? (latency / error rate /
     throughput / saturation)"
   - "Which operations are critical? (read / write / admin / replication)"

3. **Alerting & UX**
   - "Do you need built-in thresholds and alerts on the dashboard?"
   - "Which time aggregations should be the default? (1m / 5m / 1h / 24h)"

4. **Advanced** (on demand)
   - "Do you need time drill-down (from a daily chart to a 5-minute one)?"
   - "Add deployment annotations from GitLab / GitHub?"

---

## Dashboard generation

### JSON structure

The root object is an exported Grafana dashboard:

```json
{
  "annotations": { "list": [] },
  "description": "<short dashboard description>",
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 1,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [...],
  "refresh": "30s",
  "schemaVersion": 39,
  "tags": ["sre", "service", "<service_type>"],
  "templating": { "list": [...] },
  "time": { "from": "now-6h", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "<Service> - <Environment> Overview",
  "uid": "<auto-generated-or-given>",
  "version": 1,
  "weekStart": ""
}
```

### Reference panels

Use these as **structural templates** — every generated panel must follow
the same field naming (`id`, `type`, `title`, `gridPos`, `targets`,
`fieldConfig`). Three canonical examples:

**Stat panel (Overview row):**

```json
{
  "id": 1,
  "type": "stat",
  "title": "QPS",
  "gridPos": { "h": 4, "w": 4, "x": 0, "y": 0 },
  "datasource": { "type": "prometheus", "uid": "${datasource}" },
  "fieldConfig": {
    "defaults": {
      "unit": "reqps",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          { "color": "green", "value": null },
          { "color": "yellow", "value": 70 },
          { "color": "red", "value": 90 }
        ]
      },
      "color": { "mode": "thresholds" }
    },
    "overrides": []
  },
  "options": { "reduceOptions": { "calcs": ["lastNotNull"], "values": false } },
  "targets": [
    {
      "expr": "sum(rate(<metric>_total[$__rate_interval]))",
      "legendFormat": "QPS",
      "refId": "A"
    }
  ]
}
```

**Timeseries panel (Traffic row):**

```json
{
  "id": 2,
  "type": "timeseries",
  "title": "Requests by status",
  "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
  "datasource": { "type": "prometheus", "uid": "${datasource}" },
  "fieldConfig": {
    "defaults": {
      "unit": "reqps",
      "custom": { "lineWidth": 2, "fillOpacity": 20, "drawStyle": "line", "showPoints": "never" }
    },
    "overrides": []
  },
  "options": { "legend": { "displayMode": "list", "placement": "bottom", "showLegend": true } },
  "targets": [
    {
      "expr": "sum by (status) (rate(<metric>_total[$__rate_interval]))",
      "legendFormat": "{{status}}",
      "refId": "A"
    }
  ]
}
```

**Table panel (Topology row):**

```json
{
  "id": 3,
  "type": "table",
  "title": "Instances",
  "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
  "datasource": { "type": "prometheus", "uid": "${datasource}" },
  "fieldConfig": {
    "defaults": { "unit": "short", "color": { "mode": "thresholds" } },
    "overrides": [
      { "matcher": { "id": "byName", "options": "Value" }, "properties": [{ "id": "custom.cellOptions", "value": { "type": "color-background" } }] }
    ]
  },
  "options": { "showHeader": true },
  "targets": [
    {
      "expr": "up",
      "format": "table",
      "instant": true,
      "refId": "A"
    }
  ]
}
```

Every panel must carry `datasource: {type: "prometheus", uid: "${datasource}"}`
referencing the `$datasource` template variable, a unique `id`, and a
`legendFormat` on each target.

### Units (`fieldConfig.defaults.unit`)

Always set a unit so numbers are human-readable instead of raw values:

| Metric | `unit` |
|--------|--------|
| Request throughput | `reqps` |
| Latency (seconds) | `s` |
| Error rate / ratio | `percentunit` (0–1) or `percent` (0–100) |
| Memory / disk / network bytes | `bytes` |
| Data rate | `Bps`, `BdiskIops`, `bps` |
| Counts / gauges | `short` or `none` |
| CPU usage | `percent` |
| Temperature | `celsius` |
| Time durations | `s`, `ms`, `ns` |

For ratio metrics driven by the same underlying counter (e.g. error rate
= errors / total), prefer `unit: percentunit` and keep the query returning
values in the 0–1 range; use `percent` when the query already multiples by
100.

### Mandatory panel sections

Use the **RED + USE** methodology:

#### 1. Overview (top row)

Stat panels with Golden Signals:

- **QPS / Throughput** — `sum(rate(<metric>_total[$__rate_interval]))`
- **Latency p99** — `histogram_quantile(0.99, sum by (le) (rate(<metric>_seconds_bucket[$__rate_interval])))`
- **Error Rate** — `sum(rate(<metric>_total{status=~"5..|error"}[$__rate_interval])) / sum(rate(<metric>_total[$__rate_interval]))`
- **Saturation** — profile-specific to the service (connections, lag, queue depth, disk usage)

#### 2. Traffic / Queries (timeseries)

Time-series charts broken down by labels:

- Rate per label (status, method, op_type, command, query_type)
- Top N (via `topk(10, ...)`)

#### 3. Saturation / Resources

- CPU, Memory, Disk, Network (if node_exporter is present)
- Service-specific metrics (replication lag, cache size, queue depth)

#### 4. Errors & latency distribution

- Error rate breakdown
- Latency heatmap (`histogram_quantile` + heatmap panel)
- Long tail: p50/p95/p99 on a single chart

#### 5. Topology (if applicable)

- Table with instance statuses
- Stats per role (primary/replica/worker)

#### 6. Logs / Traces (optional)

Links to Loki Explore / Tempo with pre-filled labels.

### Template variables (`templating.list`)

Minimal set:

| Name | Type | Query | Purpose |
|------|------|-------|---------|
| `$datasource` | datasource | `prometheus` | datasource selection |
| `$job` | query | `label_values(<metric>, job)` | filter by job |
| `$instance` | query | `label_values(<metric>{job=~"$job"}, instance)` | instance selection |
| `$interval` | interval | `1m,5m,15m,1h,6h,1d` | aggregation for rate() |

Extensions by service type:

- PostgreSQL: `$datname`, `$role`
- Kafka: `$topic`, `$consumergroup`
- K8s: `$namespace`, `$pod`, `$container`, `$node`
- Node: `$mountpoint`, `$device`, `$nic`

Every variable must have:

- `current: { text: "All", value: "$__all" }` (if multi-value)
- `includeAll: true`
- `multi: true` (except `$datasource`, `$interval`)
- `refresh: 2` (refresh on dashboard load)

### Alerts on the dashboard

**Optional.** If the user confirms, add to each critical panel:

```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    { "color": "green", "value": null },
    { "color": "yellow", "value": 70 },
    { "color": "red", "value": 90 }
  ]
}
```

For Alertmanager integration, generate Prometheus rules in a **separate
file**. Note: `$__rate_interval` is a Grafana template variable and does
**not** work inside Prometheus rules — use a fixed window (e.g. `[5m]`)
there:

```yaml
groups:
  - name: <service>-alerts
    rules:
      - alert: <Service>HighErrorRate
        expr: sum(rate(...[5m])) > 0.05
        for: 5m
        labels: { severity: warning, service: <service> }
        annotations:
          summary: "..."
          description: "..."
```

---

## Best practices (PromQL)

- **Use `rate()` for counters**, not `irate()` — for dashboards with a long
  time range.
- **`$__rate_interval`** instead of a fixed `[5m]` — Grafana substitutes an
  interval based on the chosen range.
- **`sum by (...)` for aggregation** over the labels you actually need, not
  all of them.
- **`topk(10, ...)`** for top-N tables.
- **`histogram_quantile(0.99, sum by (le) (rate(..._bucket[$__rate_interval])))`** — the
  standard pattern for p99.
- **`legendFormat`** — required for every metric, format:
  `{{label1}} - {{label2}}`.
- **`thresholds`** — set reasonable thresholds in the metric's units.
- **Group panels by section into `collapsed: true` rows** — improves
  navigation.

---

## Validation (before emitting JSON)

1. **JSON syntax** — verify via `jq . dashboard.json` (or
   `python3 -m json.tool dashboard.json` if `jq` is not installed).
2. **All metrics exist** — if Prometheus is reachable, run
   `curl http://prometheus/api/v1/label/__name__/values | jq` and cross-check.
   If not reachable — say so honestly and ask the user to verify via
   `up{job="..."}`.
3. **Variables substitute correctly** — for each variable, show the user
   an example of the substituted query.
4. **`gridPos` is valid and panels do not overlap** — each
   `panel.gridPos: {x, y, w, h}` must satisfy `0 <= x`, `x + w <= 24`,
   `w >= 1`, `h >= 1`. The horizontal axis is limited to 24 columns;
   `y` is any non-negative integer. Two panels must never share the same
   area. Collapsed rows use `gridPos: {h: 1, w: 24}` and push the
   following panels below them.
5. **`schemaVersion` matches the Grafana version** — see the dashboard
   generation section.

After emitting the JSON, **close the loop**: ask the user to import the
dashboard into Grafana and paste any import errors or "metric not found"
warnings. Iterate on that feedback (fix queries, adjust units or
thresholds) rather than taking the first JSON as final.

---

## Iteration (mode `dashboard_action != create`)

### Principles

1. **Preserve context** — do not regenerate the dashboard from scratch;
   work only with the requested part.
2. **Preserve all unchanged sections as is** (including panel IDs if set).
3. **When adding a section** — compute `gridPos` so it slots in at the end
   (or where the user asked).
4. **When removing a section** — shift lower panels up to avoid empty space
   (unless the user wants to keep the gap).
5. **Show a diff** — what changed, which panels/variables are new, which
   were removed.

### Iteration commands

- "add a Replication section" → add a row + panels at the end
- "remove the Cache section" → delete the row + panels, shift the rest
- "rename QPS to Throughput" → change only the title
- "tighten p99" → change the thresholds
- "add a `$topic` variable" → add to `templating.list`
- "simplify the dashboard" → drop redundant panels, keep only Golden Signals

---

## Error handling

| Situation | Action |
|-----------|--------|
| Metric not found | Propose an alternative from the same exporter. If none — mark the panel as "needs verification" |
| `scrape_configs` structure unclear | Ask for a real Prometheus query example: `curl /api/v1/query?query=<metric>` |
| Config too complex | Suggest splitting into multiple dashboards (e.g., overview + detailed) |
| Unknown service type | Use the generic template with Golden Signals, ask about specifics |
| Multiple datasources | Ask which one to use by default, expose the rest via `$datasource` |
| User gave minimum data | Ask at most 3 key questions, default the rest |

---

## Output format

### When creating

First, a short text description of the structure, then JSON in a code
block:

```markdown
## Dashboard structure

- **Variables:** datasource, job, instance, interval, role
- **Row 1 — Overview:** QPS, Latency p99, Error Rate, Active Connections
- **Row 2 — Traffic:** HTTP Requests by Status, Top Endpoints
- **Row 3 — Replication:** Replica Lag, WAL Position
- **Row 4 — Resources:** CPU, Memory, Disk (Node Exporter)

## JSON

```json
{ ... }
```
```

### When iterating

```markdown
## Changes

- ➕ Added **Replication** section (3 panels)
- 🔧 Changed Error Rate threshold: 70/90 → 80/95
- ➖ Removed "Top Queries" panel

## JSON diff

```diff
+ "panels": [...3 new panels...]
- "panels": [...removed panel...]
```

(Full JSON in the code block below.)
```

---

## Example

### Input

> Here is the scrape config for PostgreSQL, cluster: 1 primary + 2 replicas,
> production, ~5000 QPS.

### Skill response

```
Identified: PostgreSQL 14, primary-replica topology.

Dashboard structure:
- Variables: $datasource, $job, $instance, $role, $datname, $interval
- Row 1 — Cluster Overview: Cluster status, Replication lag (max), Active connections, TPS
- Row 2 — Primary Focus: Write QPS, Commits/Rollbacks, Lock wait time, Longest transaction
- Row 3 — Replica Health: Replica lag per replica, Read QPS, Hot standby feedback
- Row 4 — Resources: CPU, Memory, Disk I/O, Network (Node Exporter)
- Row 5 — Database Stats: Top tables by seq/index scan, Cache hit ratio, Dead tuples

Question: add alerts to the dashboard (thresholds + Alertmanager rules)?
```

After the user's answer — generate the full JSON.

---

## Limitations

- The skill **does not connect to Prometheus** — all metric checks are done
  by the user manually or at their request via bash.
- The skill **does not validate JSON inside Grafana** — emits JSON, the
  user imports into Grafana and verifies.
- The skill **does not version dashboards** — the user decides where to
  store versions (Git, Grafana provisioning, Terraform).
- The skill **works only with the Prometheus-family** of datasources
  (Prometheus, VictoriaMetrics, Mimir, Thanos).
