# GrafanaSmith

> A toolkit for SRE engineers who build Grafana dashboards for production services.

GrafanaSmith is a curated collection of skills, templates, and conventions
for turning Prometheus `scrape_configs` and a short service description
into production-ready Grafana dashboards.

The centerpiece is the
[`grafana-dashboard`](skills/grafana-dashboard/SKILL.md) skill — an
opinionated generator that knows the metrics, panels, and variables that
matter for the most common infrastructure components. The skill follows
the standard `SKILL.md` format and is **engine-agnostic**: it works in
[opencode](https://opencode.ai), Claude Code, Cursor, and any other agent
that can load a skill from a `SKILL.md` file.

## Why GrafanaSmith

Most Grafana dashboards in the wild suffer from the same problems:

- panels with no clear narrative (Golden Signals missing);
- `rate(node_cpu_seconds_total[5m])` copy-pasted everywhere, even when the
  service is not a CPU-bound one;
- hardcoded instance names instead of templated variables;
- thresholds picked at random, with no link to SLOs.

GrafanaSmith encodes the SRE best practices — RED, USE, Golden Signals —
into a repeatable workflow so every dashboard you ship has the same shape
and the same quality bar.

## The `grafana-dashboard` skill

The skill accepts three inputs and produces a Grafana-compatible JSON
dashboard:

| Input | Required | Description |
|-------|----------|-------------|
| `scrape_configs` | yes | Prometheus job definitions (job_name, static_configs, relabel_configs, metrics_path) |
| `service_description` | yes | What the service is and how it is deployed (single, cluster, primary-replica, sharded...) |
| `context` | no | Environment, expected load, SLO, presence of Alertmanager |

The skill operates in two modes:

- **create** — generate a new dashboard from scratch.
- **iterate** — refine an existing dashboard without rewriting it from scratch.

### Built-in service templates

The skill ships with nine service templates under
[`skills/grafana-dashboard/templates/`](skills/grafana-dashboard/templates/):

- PostgreSQL
- MySQL / MariaDB
- Redis
- Kafka
- NGINX
- PowerDNS Authoritative
- Node Exporter (generic host)
- Kubernetes Pods (kube-state-metrics + cAdvisor)
- Generic / unknown service (Golden Signals fallback)

Each template defines the panel sections, **ready-to-use PromQL
expressions**, alert thresholds, and template variables that make sense
for that service. Adding a new service is a matter of creating one
`templates/<service>.md` file following the same layout — no changes to
the skill itself.

### What the skill generates

Every dashboard produced by the skill includes:

- **Overview row** with Golden Signals (QPS, latency p99, error rate, saturation) as `stat` panels.
- **Traffic / Queries row** with time-series breakdowns by label.
- **Saturation / Resources row** (CPU, memory, disk, network when node_exporter is present).
- **Errors & latency distribution row** with heatmaps and p50/p95/p99.
- **Topology row** (when the service has a non-trivial topology).
- **Templating variables**: `$datasource`, `$job`, `$instance`, `$interval`, plus profile-specific ones (`$role`, `$datname`, `$topic`, `$consumergroup`, `$namespace`, ...).
- **Optional**: thresholds on critical panels, separate Prometheus alert rules for Alertmanager, deployment annotations.

The generated JSON follows modern Grafana conventions:

- `schemaVersion: 39` for Grafana 9–10, `40` for Grafana 11;
- `gridPos` validated against the real grid rules (`x + w <= 24`, no overlaps);
- `$__rate_interval` in all `rate()` windows (fixed `[5m]` only in alert rules);
- `unit` set on every panel (`reqps`, `s`, `percentunit`, `bytes`, ...);
- `legendFormat` on every series;
- stable `uid` convention (`<environment>-<service>-<purpose>`).

The skill also embeds canonical reference panels (stat, timeseries, table)
so every generated panel follows the same field contract, and closes the
loop by asking you to import the JSON and feed back Grafana errors for a
second iteration.

## Installation

The skill is a `SKILL.md` file plus its `templates/` directory. Any
agent that loads skills (opencode, Claude Code, Cursor, ...) picks it up
from the relevant skills location.

### opencode

```bash
git clone https://github.com/philyuchkoff/GrafanaSmith.git
ln -s "$(pwd)/GrafanaSmith/skills/grafana-dashboard" \
      ~/.config/opencode/skills/grafana-dashboard
```

Restart opencode so the new skill is loaded.

### Claude Code / Cursor

```bash
git clone https://github.com/philyuchkoff/GrafanaSmith.git
mkdir -p ~/.claude/skills
cp -R GrafanaSmith/skills/grafana-dashboard ~/.claude/skills/
```

(Claude Code loads `~/.claude/skills/<name>/SKILL.md`; Cursor reads
`.cursor/skills/` in the project or the equivalent user-level directory.)

### Project-scoped install

To use the skill only inside one repository, copy it into the project's
skill directory (e.g. `.opencode/skills/` for opencode):

```bash
mkdir -p .opencode/skills
cp -R skills/grafana-dashboard .opencode/skills/
```

## Usage

Invoke the skill by describing the service and pasting the scrape config:

> "Generate a Grafana dashboard for our PostgreSQL 14 cluster — 1 primary,
> 2 replicas, production, ~5000 QPS. Here is the scrape config: ..."

The skill will:

1. Parse the scrape config and identify available metrics, label structure,
   and instance roles.
2. Load the matching template from `templates/` and match it against the
   service description.
3. Ask at most 3-4 clarifying questions (topology, SLI, alerting, time
   aggregation) if anything is ambiguous.
4. Produce a complete dashboard JSON plus a short description of the panel
   structure, then ask you to import it and report any errors.

To refine an existing dashboard:

> "Add a Replication section to the dashboard and tighten the error rate
> threshold to 80/95."

The skill will keep the existing panels intact and apply only the requested
change, showing a diff at the end.

## Repository layout

```
GrafanaSmith/
├── README.md                          # this file
├── README-ru.md                       # Russian version
└── skills/
    └── grafana-dashboard/
        ├── SKILL.md                   # the skill itself
        └── templates/                 # per-service templates (PromQL, alerts, variables)
            ├── postgresql.md
            ├── mysql.md
            ├── redis.md
            ├── kafka.md
            ├── nginx.md
            ├── powerdns.md
            ├── node-exporter.md
            ├── kubernetes-pods.md
            └── generic.md
```

## Conventions

When you add a new service template, follow these rules:

1. **Pick metrics the exporter actually emits.** Verify against the exporter
   documentation; do not invent metric names.
2. **Use `$__rate_interval` in `rate()` windows** so the dashboard behaves
   well at any zoom level. Fixed windows (`[5m]`) are only valid in
   Prometheus alert rules, where `$__rate_interval` does not exist.
3. **Always include `legendFormat`** with at least one label interpolated.
4. **Thresholds must map to an SLO or an incident-driven signal.** Random
   thresholds are noise.
5. **Group panels into rows** with `collapsed: false` so the dashboard
   stays navigable.
6. **Variables are case-sensitive and snake_case.** `$replica_type` over
   `$ReplicaType`.
7. **Set `unit` on every panel** and follow the `uid` convention
   `<environment>-<service>-<purpose>`.

## Contributing

Contributions are welcome. The most useful additions are:

- New service templates (Cassandra, MongoDB, RabbitMQ, Elasticsearch,
  ClickHouse, Envoy, HAProxy, ...) — create `templates/<service>.md`.
- Better defaults for thresholds based on real-world SLOs.
- Additional PromQL patterns for hard-to-expose signals.
- Translations of the documentation.

Open a pull request with the new template under
`skills/grafana-dashboard/templates/<service>.md`.

## Roadmap

- [ ] Templated drill-down dashboards (cluster -> node -> query).
- [ ] Auto-export of Prometheus alert rule files alongside the dashboard.
- [ ] Provisioning manifests (Grafana provisioning, Terraform).
- [ ] Linter that validates a Grafana JSON against the conventions.

## License

MIT. See [`LICENSE`](LICENSE).
