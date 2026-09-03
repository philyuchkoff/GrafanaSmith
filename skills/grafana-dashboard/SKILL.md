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
  auto_inferred:
    description: Decisions made automatically from scrape_configs (topology, roles, multi-tenancy) so next iteration knows not to re-ask
    validation: List of (decision, confidence) tuples
  key_sli:
    description: Key SLIs for the service (latency, error_rate, throughput, saturation)
    validation: "2-4 metrics from Golden Signals / RED / USE"
  previous_version:
    description: Previous dashboard version (for iterations)
    validation: Full JSON with preserved panels/templating structure
---

## Roles and modes

The skill operates in **three modes**, determined by the
`dashboard_action` parameter or the dialog context:

### Mode 1: Create (`dashboard_action: create`)

Full cycle from `scrape_configs` to a ready-to-import dashboard JSON.

### Mode 2: Iterate (`dashboard_action: iterate|fix|add_section|remove_section`)

Modifies an existing dashboard while preserving the previous version's
context. **Do not regenerate the dashboard from scratch** — apply only the
requested changes.

### Mode 3: Composite (`dashboard_action: create`, multiple scrape_configs)

Creates a single dashboard containing sections for **multiple services**
that belong to the same application stack — e.g. PostgreSQL + Redis +
Kafka behind an NGINX API.

**When to use:**
- The user explicitly asks for a "composite dashboard" or "a single
  dashboard covering everything in the stack."
- The user provides multiple `scrape_configs` entries under the same app
  name and says they're all part of one product.

**When NOT to use:**
- The services are independent and monitored by different teams.
- The user is asking for a dashboard per service (default behavior).

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
    - **Consult `compatibility-matrix.md`** for known metric renames per exporter
      version (e.g. `tup_` → `tuples_` for postgres_exporter).
    - **Detect version** — if the user provides `up{job=...}` output or
      `curl /api/v1/label/__name__/values`, match metric naming against the
      compatibility matrix. If unable to detect, default to the latest known
      naming and warn the user.
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

### Step 4: Auto-infer from scrape_configs (before asking)

Before asking the user about topology, instance roles, or additional labels,
**apply inference rules**. The goal: extract as much as possible from config,
ask only when truly ambiguous.

**Inference rules:**

| From config | Infer | Confidence |
|---|---|---|
| `relabel_configs` sets `role: primary\|replica\|master\|slave` | Topology is `primary-replica` with roles detected | High |
| `relabel_configs` sets `role: leader\|follower\|candidate` (etcd/consul) | Topology is `cluster` with leader election | High |
| `relabel_configs` exposes `shard`, `shard_id`, `partition` | Topology includes sharding dimension | High |
| `static_configs` has exactly 1 target, no `role`-like labels | Likely `single` — confirm with user only if service type supports replication | Medium |
| `static_configs` has multiple targets with a `_meta_kubernetes_pod_label_*` that includes `statefulset` or `sts` | Cluster with pod identity — ask only the sharding/single distinction | Medium |
| `job_name` contains `primary`, `master`, `leader`, `replica`, `slave`, `follower`, `standby` | Role-based deployment — infer topology accordingly | Medium |
| `job_name` contains `cluster`, `node`, `peer` | Peer cluster — infer `cluster` topology | Medium |
| No role/sharing labels at all, multiple targets | Likely `stateless` or `single` — ask the user | Low |
| `namespace`, `cluster`, `datacenter` in labels | Multi-tenancy present — add corresponding template variable | High |
| `__meta_kubernetes_pod_label_app` or `app_kubernetes_io_name` | Extract `$app` variable | High |
| `metrics_path` contains `/probe` | Blackbox-exporter probing — ask the user if it's an HTTP/TCP/ICMP probe | — |
| `metrics_path` is JMX-style (`/`, `/metrics`, jmx_config) for Kafka | Check `compatibility-matrix.md` for metric naming (JMX vs kafka_exporter) | — |

**Action:**
- If confidence is **High** for a decision — use it, do not ask.
- If confidence is **Medium** — use it as default, mention it in the
  description, offer the user a chance to correct.
- If confidence is **Low** — ask the user (max 1 question).

### After inference

Construct the `instance_roles` list from the labels found. The validated
memory section of the skill carries a `instance_roles` field that should
be populated from inference output, not from user input alone.

---

## Service templates

Templates live as separate files under `templates/` (relative to this
skill's directory). **Before generating for a service, read the matching
template file** so the panels, PromQL, and thresholds match the exporter
actually in use.

| Service | Template file |
|---------|---------------|
| PostgreSQL | `templates/postgresql.md` |
| PostgreSQL HA (Patroni) | `templates/postgresql-patroni.md` |
| MySQL / MariaDB | `templates/mysql.md` |
| Redis | `templates/redis.md` |
| Redis Cluster | `templates/redis-cluster.md` |
| Kafka | `templates/kafka.md` |
| NGINX | `templates/nginx.md` |
| Elasticsearch / OpenSearch | `templates/elasticsearch.md` |
| MongoDB | `templates/mongodb.md` |
| RabbitMQ | `templates/rabbitmq.md` |
| PowerDNS Authoritative | `templates/powerdns.md` |
| Node Exporter (linux host) | `templates/node-exporter.md` |
| Kubernetes Pods | `templates/kubernetes-pods.md` |
| Generic / unknown | `templates/generic.md` |

Each template defines: panel **Sections**, **Key metrics & PromQL**
(ready-to-use expressions), **Alerts** (Prometheus rules), and
**Variables**. Always verify metric names against the exporter version
and the actual `scrape_configs` before emitting JSON — exporter metric
families vary (e.g. postgres_exporter, JMX vs kafka_exporter). **Also
consult `compatibility-matrix.md`** for known metric renames across
exporter versions — for example, `tup_` → `tuples_` between
postgres_exporter 0.4 and 0.12. To add a template for a new service,
create `templates/<service>.md` following the same layout.

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

3. **Alerting & runbook**
    - "Do you need dashboard thresholds + Prometheus alert rules?"
    - "If yes — what severity levels? (default: warning + critical)"
    - "If yes — do you have a Confluence runbook page I can link in
      `annotations.runbook_url`?"
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
  "schemaVersion": 42,
  "tags": ["sre", "service", "<service_type>"],
  "templating": { "list": [...] },
  "time": { "from": "now-6h", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "<Service> - <Environment> Overview",
  "uid": "<auto-generated-or-given>",
  "version": 1,
  "weekStart": "",
  "grafanaSmith": {
    "version": "0.2.0",
    "template": "<service_type>",
    "template_version": "0.2.0",
    "mode": "create",
    "datasource_type": "prometheus",
    "generated_at": "<ISO 8601 timestamp>"
  }
}
```

`schemaVersion` depends on the Grafana version the dashboard targets; if
the target is unknown, ask in the clarifying round:
`39` for Grafana 10, `40` for Grafana 11, `41` for Grafana 12, `42` for
Grafana 13+. Version 42 is the **final schema of the v1 dashboard API** —
Grafana does not raise it further, so `42` is the safe default for new
dashboards. Lower version numbers import fine into newer Grafana; a
too-high number fails on older instances. Do not set `"version"` above
`1` — Grafana bumps it on the first save.

**`grafanaSmith` metadata** — every generated dashboard MUST include a
`grafanaSmith` object at the top level with versioning metadata. This
enables iteration: when you re-read an existing dashboard, you immediately
know which template version produced it and which exporter assumptions
were baked in. The `grafanaSmith.version` matches the skill release;
`grafanaSmith.template_version` matches the template file version (see
template file header). When iterating (`mode: "iterate"`), preserve the
original `grafanaSmith` block and only update `grafanaSmith.generated_at`.

**`uid` convention** — generate a stable, descriptive uid from the
service and environment so provisioning and links are predictable:
`<environment>-<service>-<purpose>`, e.g. `prod-postgresql-overview`,
`staging-nginx-edge`. If the user already has a dashboard uid, reuse it
(when iterating) or derive a new one without conflicts.

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

### Annotations (deployments)

If the user asked for deployment annotations, populate `annotations.list`
with a Prometheus-range annotation that fires on deploy events. Detect
deploys via a metric that changes on restart (exporter `_build_info`,
`node_boot_time_seconds`, or a dedicated deploy counter); if the team
pushes GitLab/GitHub events into Loki, reference the Loki datasource
instead:

```json
"annotations": {
  "list": [
    {
      "name": "Deployments",
      "type": "tags",
      "datasource": { "type": "prometheus", "uid": "${datasource}" },
      "expr": "changes(<service>_build_info[1m]) > 0",
      "step": "60",
      "iconColor": "blue"
    }
  ]
}
```

Only add annotations when confirmed — they add noise on dashboards that do
not need deploy correlation.

### Alerts on the dashboard

**Optional.** If the user confirms, add threshold visual markers to each
critical panel. These are **dashboard-level thresholds** only (color
changes on the graph/stat) — they do not trigger actual alert
notifications.

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

### Prometheus alert rules (separate output)

**If the user mentions Alertmanager or asks for alert rules**, generate
them in a **separate file** (not inside the dashboard JSON), formatted
as a standard PrometheusRule CR or `prometheus_rules.yml` file.

**Dialog flow for alerts:**
1. If the user mentions Alertmanager: "I'll generate PrometheusRules as a
   separate YAML file alongside the dashboard. Two questions:"
   - "What severity levels should I use? (default: warning + critical)"
   - "Do you have a Confluence runbook page I can link in
     `annotations.runbook_url`?"

2. If the user provides a **Confluence runbook URL**, inject it into every
   alert's `annotations.runbook_url`:
   ```yaml
   annotations:
     runbook_url: "https://confluence.example.com/display/.../<page-id>"
   ```

3. If the user says **only Alertmanager but no runbook yet**, ask if they
   want a Confluence page created and a link added later.

4. If the user says **no alerts at all**, skip this section.

**Output format for alert rules:**

The skill emits a second code block containing the PrometheusRule YAML.
All template-specific alerts come from the template's `## Alerts` section.

```yaml
# prometheus-rules.yaml — <Service> alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: <service>-alerts
  namespace: monitoring
  labels:
    app: grafana-smith
    tier: alerting
spec:
  groups:
    - name: <service>
      rules:
        - alert: <Service>HighErrorRate
          expr: sum(rate(<metric>_total{status=~"5..|error"}[5m])) / sum(rate(<metric>_total[5m])) > 0.05
          for: 5m
          labels:
            severity: warning
            service: "<service>"
          annotations:
            summary: "<Service> error rate above 5%"
            description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes."
            runbook_url: "<provided-by-user>"
```

`$__rate_interval` is a Grafana template variable and does **not** work
inside Prometheus rules — use a fixed window (e.g. `[5m]`).

**Conventions for alert rules:**
- `alert` name: `<Service><Description>` PascalCase (e.g. `PostgreSQLConnectionSaturation`)
- `severity`: `critical` (needs immediate paging) or `warning` (needs attention within hours)
- `for`: `1m` for critical, `5m` for warning, `15m` for trends
- `annotations.summary`: one-line summary with the service and metric
- `annotations.description`: includes `{{ $value }}` for context
- `annotations.runbook_url`: set once per service (same for all rules in that group)

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

## Composite dashboards (multiple services)

When the user wants one dashboard for their entire stack (e.g. "my app
uses PG + Redis + Kafka — give me one dashboard"), generate in composite
mode.

### Layout

```
Row 1 — Resources (shared)
  ├─ Stat: Total CPU, Total Memory, Total Disk
  ├─ Timeseries: CPU per instance, Memory per instance
  └─ Table: All instances with service type column

Row 2 — Service A (e.g. PostgreSQL)
  ├─ Stat overview: QPS, Latency, Error Rate (A-specific)
  ├─ Timeseries: A-specific panels
  └─ Relevant topology/health panels

Row 3 — Service B (e.g. Redis)
  └─ (same pattern)

Row 4 — Service C (e.g. Kafka)
  └─ (same pattern)

...etc.
```

### Structure rules

1. **`grafanaSmith.mode`** = `"composite"`
2. **`grafanaSmith.template`** = `"composite"` (no single service name)
3. **Title** = `<AppName> - <Environment> Stack Overview`
4. **UID** = `<environment>-<appname>-stack`
5. **Panel IDs** are sequential across ALL services (no reuse)
6. **Template variables** are grouped: first core variables (`$datasource`,
   `$job`, `$instance`, `$interval`), then service-specific ones with a
   prefix in their name and label to avoid collision — e.g.
   `$pg_role`, `$redis_role`, `$kafka_topic`.
7. Each service section opens with a **collapsed row** whose title includes
   `<ServiceIcon> ServiceName` for visual scanning.

### Resource Overview row

The first row aggregates node-level metrics across all instances:

| Panel | PromQL |
|-------|--------|
| CPU (avg across stack) | `avg by (instance) (100 - rate(node_cpu_seconds_total{mode="idle"}[$__rate_interval]) * 100)` |
| Memory (worst node) | `max by (instance) ((1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100)` |
| Disk (worst node) | `max by (instance) ((node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100)` |
| Network (total) | `sum(rate(node_network_receive_bytes_total[$__rate_interval])) + sum(rate(node_network_transmit_bytes_total[$__rate_interval]))` |
| Instance table | `up` with `$job` filter, columns: instance, job, version, uptime |

**Fallback:** if no node_exporter scrape_configs are provided, skip the
Resource row and start directly with Service A.

### Per-service section

For each service in the stack, generate a **reduced set** of its template's
mandatory panels — about 6–8 panels (not all 25 from the individual
template). The priority order for what to include:

1. Golden Signals row — 3–4 stat panels (Throughput, Latency p99, Error Rate, Saturation)
2. One 2× panel timeseries showing the most critical pattern (e.g., replication lag for PG, consumer lag for Kafka)
3. Instance health table

The composite format is an **aggregation**, not a replacement —
individual per-service dashboards are still generated when the user
specifically asks for one.

### Iteration

Composite dashboards support the same iteration commands as single:
add/remove a service section, rename titles, adjust thresholds. Parse
structurally; `grafanaSmith.mode` is `"composite-iterate"` after
iteration.


---

## Validation (before emitting JSON)

There is a companion validation script at `tests/validate_dashboard.py`.
**After generating JSON**, run it on the output file to check structural
validity before presenting to the user:

```bash
python3 tests/validate_dashboard.py ./output.json
```

If the script reports errors, fix them before presenting to the user.

### Manual checks

1. **JSON syntax** — verify via `jq . dashboard.json` (or
   `python3 -m json.tool dashboard.json` if `jq` is not installed).
   If `existing_dashboard` is provided in iteration mode, parse it
   structurally first — any parse error must be reported to the user before
   proceeding.
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
5. **`schemaVersion` matches the Grafana version** — `39` for Grafana 10,
   `40` for Grafana 11, `41` for Grafana 12, `42` for Grafana 13+ (final
   v1 schema).

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
3. **Parse structurally** — when given `existing_dashboard` JSON, parse it
   into a native object (e.g. via `python3 -c "import json; ..."` or
   equivalent). Make changes by mutating the object tree: add/remove panels
   from `panels[]`, update `gridPos`, add/remove items in
   `templating.list`, change `thresholds` or `title` strings. Then
   serialize back to JSON. Never apply textual string replacements to raw
   JSON — that breaks with escaping, reordering, and whitespace drift.
4. **When adding a section** — compute `gridPos` so it slots in at the end
   (or where the user asked).
5. **When removing a section** — shift lower panels up to avoid empty space
   (unless the user wants to keep the gap).
6. **Show a diff** — what changed, which panels/variables are new, which
   were removed.
7. **Cache the parsed structure** — run the structural parse once and hold
   the object in memory for all subsequent modifications within the same
   iteration session.

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
block. If alert rules were generated, include them in a separate code block
after the JSON.

```markdown
## Dashboard structure
...

## Dashboard JSON

```json
{ ... }
```

## Prometheus alert rules (optional)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
...
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
- The skill **embeds version metadata** in every generated dashboard via the
  `grafanaSmith` top-level key; the user decides where to store dashboards
  (Git, Grafana provisioning, Terraform).
- The skill **works only with the Prometheus-family** of datasources
  (Prometheus, VictoriaMetrics, Mimir, Thanos).
