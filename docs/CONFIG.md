# CONFIG.md
# Configuration Files (recommended)

## target_catalog.yaml
Defines targets and their logic:
- id, label
- occurred_rule (expr)
- event_bar_col (optional)
- default_plots (overall/timing/period)
- group tags (Gap, OR12, OR18, HTF, Extremes)

## fields.yaml
Defines fields:
- dtype: numeric/categorical/event_bar/bucket
- reducer: FIRST/LAST/MAXEVENT
- label mappings (bucket -1/0/1)
- allowed thresholds (quantiles or domain thresholds)

## case_templates.yaml
Defines case studies:
- name
- filter clauses
- primary targets
- chart overlays
- export template choice