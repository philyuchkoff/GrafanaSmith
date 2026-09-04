#!/usr/bin/env python3
"""GrafanaSmith dashboard JSON validator.

Usage: python3 tests/validate_dashboard.py <dashboard.json>
Performs structural validation of a generated dashboard JSON.
"""

import json
import sys
import os

EXIT_OK = 0
EXIT_JSON_ERROR = 1
EXIT_STRUCTURAL = 2

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        return None

def check(condition, msg, errors):
    if not condition:
        errors.append(msg)

def validate_grafana_smith(dashboard, errors):
    gs = dashboard.get("grafanaSmith")
    check(gs is not None, "Missing grafanaSmith metadata block", errors)
    if not gs:
        return
    for key in ["version", "template", "template_version", "mode", "datasource_type", "generated_at"]:
        check(key in gs, f"grafanaSmith missing key: {key}", errors)

def validate_panels(dashboard, errors):
    panels = dashboard.get("panels", [])
    check(len(panels) > 0, "No panels found", errors)
    if not panels:
        return

    seen_ids = set()
    for i, panel in enumerate(panels):
        pid = panel.get("id")
        check(pid is not None, f"panel[{i}] missing id", errors)
        if pid is not None:
            check(pid not in seen_ids, f"Duplicate panel id: {pid}", errors)
            seen_ids.add(pid)

        ds = panel.get("datasource", {})
        if panel.get("type") == "row":
            continue
        if isinstance(ds, dict) and ds.get("type") == "prometheus" and "uid" in ds:
            continue
        errors.append(f"panel[{i}] (id={pid}) invalid datasource: {ds}")

        gp = panel.get("gridPos", {})
        x = gp.get("x", 0)
        y = gp.get("y", 0)
        w = gp.get("w", 1)
        h = gp.get("h", 1)
        check(x >= 0, f"panel[{i}] (id={pid}) gridPos.x < 0: {x}", errors)
        check(w >= 1, f"panel[{i}] (id={pid}) gridPos.w < 1: {w}", errors)
        check(h >= 1, f"panel[{i}] (id={pid}) gridPos.h < 1: {h}", errors)
        check(x + w <= 24, f"panel[{i}] (id={pid}) gridPos x+w={x+w} > 24", errors)

    for a_i in range(len(panels)):
        for b_i in range(a_i + 1, len(panels)):
            pa = panels[a_i]
            pb = panels[b_i]
            xa, ya, wa, ha = [pa.get("gridPos", {}).get(k, 0) for k in ("x", "y", "w", "h")]
            xb, yb, wb, hb = [pb.get("gridPos", {}).get(k, 0) for k in ("x", "y", "w", "h")]
            overlap = xa < xb + wb and xa + wa > xb and ya < yb + hb and ya + ha > yb
            check(not overlap,
                  f"Overlap: id={pa.get('id','?')} and id={pb.get('id','?')}", errors)

def validate_root_keys(dashboard, errors):
    for key in ["annotations", "description", "editable", "panels", "refresh",
               "schemaVersion", "tags", "templating", "time", "title", "uid", "version"]:
        check(key in dashboard, f"Missing root key: {key}", errors)

def validate_variables_list(dashboard, errors):
    tvars = dashboard.get("templating", {}).get("list", [])
    check(len(tvars) > 0, "No template variables", errors)
    tvar_names = [v.get("name") for v in tvars]
    for required_var in ["datasource", "job", "instance", "interval"]:
        check(required_var in tvar_names, f"Missing variable: ${required_var}", errors)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tests/validate_dashboard.py <dashboard.json>", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]
    dashboard = load_json(json_path)
    if dashboard is None:
        sys.exit(EXIT_JSON_ERROR)

    errors = []
    validate_root_keys(dashboard, errors)
    validate_grafana_smith(dashboard, errors)
    validate_panels(dashboard, errors)
    validate_variables_list(dashboard, errors)

    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(EXIT_STRUCTURAL)
    else:
        print("PASS")
        sys.exit(EXIT_OK)

if __name__ == "__main__":
    main()
