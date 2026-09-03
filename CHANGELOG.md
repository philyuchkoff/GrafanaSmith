# Changelog

## [0.2.0] — Unreleased

### Added

- **Versioning metadata** — every generated dashboard now includes a
  `grafanaSmith` top-level key with `version`, `template`,
  `template_version`, `mode`, `datasource_type`, and `generated_at`.
- **Exporter compatibility matrix** — documents known metric renames
  across exporter versions (postgres_exporter `tup_` → `tuples_`, Kafka
  JMX vs danielqsj styles, Redis/PowerDNS/NGINX variants) to avoid
  broken PromQL.
- **Structural JSON parsing in iteration mode** — when editing an existing
  dashboard, parse JSON into a native object, mutate the tree, serialize
  back. No more fragile text replacements.
- **Test infrastructure** — `tests/validate_dashboard.py` validates
  generated dashboard JSON: root keys, grafanaSmith block, panel IDs
  (uniqueness), gridPos (bounds, no overlap), datasource references,
  mandatory template variables.
- **GitHub Actions CI** — `.github/workflows/test-skill.yml` checks
  SKILL.md frontmatter, template version headers, and runs the JSON
  validator on each push.
- **Five new templates:**
  - `elasticsearch.md` — cluster health, shards, indexing/search rate and
    latency, JVM heap/GC, circuit breakers, thread pools. Supports both
    `elasticsearch_` and `opensearch_` prefixes.
  - `mongodb.md` — opcounters per type, read/write latency p99, replication
    lag, oplog window, WiredTiger cache, connections, locks.
  - `rabbitmq.md` — queue depth, publish/deliver/ack rates, memory
    watermark, disk free, Erlang VM metrics. Supports kbudde exporter and
    built-in plugin.
  - `postgresql-patroni.md` — Patroni cluster health, leader election, sync
    replication, timeline divergence, DCS heartbeat, failover detection.
  - `redis-cluster.md` — cluster state, slots assignment/migration, cluster
    bus, master/replica per node, failover detection.
- **Smart inference** — auto-detect topology, instance roles, multi-tenancy,
  and app name from `relabel_configs` and `job_name`. High-confidence
  decisions use without asking. Medium ask for opt-out. Low ask one question.
- **Composite dashboard mode** — generates a single dashboard for multiple
  services (e.g. PG+Redis+Kafka+NGINX). Includes shared Resource
  Overview row + per-service collapsed rows with Golden Signals panels and
  health tables.
- **PrometheusRule generation** — when user mentions Alertmanager, generate
  a separate `PrometheusRule` YAML with proper severity levels, alert naming
  (`<Service><Description>` PascalCase), and `annotations.summary`,
  `annotations.description`, `annotations.runbook_url` per alert.
- **runbook_url support** — skill asks for a Confluence page URL to link in
  every alert's `annotations.runbook_url`.

### Changed

- SKILL.md dialog strategy now asks about Confluence runbook URL alongside th
  alert thresholds.
- New location of Validation script is referenced in the skill instructions.

### Fixed

- Iteration mode now requires structural JSON parsing (was: text-based
  string replacements that broke with escaped or reordered JSON).
