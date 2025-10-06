# Report Schemas

This document tracks schema versions for generated validation reports.

## Layout Drift Report (compare_grafana_layout.py)

Current schema_version: 2

Fields:

- schema_version (int)
- status ("pass" | "fail")
- baseline_panel_count (int)
- current_panel_count (int)
- missing_panels (string[])
- overlaps (array of [title_a, title_b])
- minor_drift (array of [title, dx, dy])
- major_drift (array of [title, dx, dy, dw, dh])
- minor_drift_percent_current (float)
- minor_drift_percent_baseline (float)
- size_changes_minor (array of [title, dw, dh])
- size_changes_major (array of [title, dw, dh])
- size_change_percent_baseline (float)
- size_threshold (int) - percentage threshold used (-1 means disabled)
- size_threshold_breach (bool)
- tolerance (int) - positional tolerance

Prometheus Metrics Emitted (when --prom-metrics provided):

- layout_minor_drift_panels
- layout_major_drift_panels
- layout_size_change_panels
- layout_size_change_percent_baseline
- layout_minor_drift_percent_baseline
- layout_minor_drift_percent_current
- layout_failing
- layout_total_panels
- layout_baseline_panels
- layout_missing_panels
- layout_overlapping_pairs
- layout_size_threshold_breach (only if breached)
- layout_total_area_current (total summed area w*h of current panels)
- layout_total_area_baseline (total summed area of baseline panels)
- layout_area_changed_panels (count of panels whose area changed)
- layout_area_cumulative_delta (sum of absolute area deltas)

## Alert Validation Report (validate_alert_rules.py)

Current schema_version: 2

Fields:

- schema_version (int)
- errors (string[])
- warnings (string[])
- info (string[])
- alerts_checked (string[])
- required_labels (string[])
- taxonomy_size (int)
- per_alert (object keyed by alert name):
  - missing_required_labels (string[])
  - label_mismatches (object label -> {rule, taxonomy})
- error_count (int)
- warning_count (int)

Prometheus Metrics Emitted (when --prom-metrics provided):

- alert_validation_errors
- alert_validation_warnings
- alert_validation_info
- alert_validation_alerts_checked
- alert_validation_required_labels
- alert_validation_taxonomy_size
- alert_validation_failing
- alert_validation_severity_count{severity="<label>"} (one series per severity observed)

## Versioning Guidelines

- Increment schema_version when field names change semantics, fields are removed, or incompatible transformations occur.
- Adding new optional fields is backward-compatible (no version bump required but may warrant a
  minor version note in changelog if introduced).

## Future Ideas

- (Done) Add layout panel area change aggregate statistics.
- (Done) Add alert rule category breakdown counts (by severity).
- (Done) Introduce unified meta report referencing component report schema versions.
- Consider adding per-panel area delta distribution metrics (histogram or buckets) if needed.
- Potential integration of panel type/category metrics (e.g., by visualization kind) for layout governance.

## Unified Validations Index (run_observability_validations.py)

Schema Version: 1

Fields:

- schema_version (int)
- layout:
  - exit_code (int) underlying layout script exit code
  - report (string|null) path to layout JSON report if produced
- alerts:
  - exit_code (int)
  - report (string|null) path to alert JSON report if produced
- overall_status ("pass" | "fail") aggregate status (pass only if both exit codes are 0)

Artifacts Produced:

- combined_metrics.prom : concatenated Prometheus exposition from both validators (order: layout then alerts)
- validations_index.json : meta index described above

Versioning Notes:

Index schema is intentionally minimal; adding new top-level keys is backward-compatible.
Increment schema_version on removal or semantic change of existing keys.
