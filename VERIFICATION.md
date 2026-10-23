# Verification record

## Maintainer-reported workflow pass

On October 22, 2026, the maintainer reported that the SQL workflow passed after the portability update in commit 76b4cca39ea53d77888b36987b7227d1d746a007.

Workflow: .github/workflows/sql-validation.yml
Entry point: python scripts/analyze_layers.py
Configured environments: Python 3.12 on ubuntu-24.04 and windows-2022.

Evidence level: maintainer-reported workflow success. The assistant did not independently retrieve the Actions check result or download the successful run's artifacts. No specific run ID, separate per-platform result, runtime duration, or new sales-only financial value is asserted here.

## What the workflow checks

The configured workflow runs the regression suite and layered runner. The runner requires the pinned source CSV hashes, the documented raw exception profile, successful raw KPI/category reference comparisons, quarantine counts, strict validation of the sales-only tables, and execution of the ten analytical SQL scripts against both populations before publishing its success manifest.

A passing run is evidence for those implemented checks, not proof of all business definitions, source intent, or data ownership. The raw snapshot is explicitly not clean.

## Results publication boundary

The README and committed results/ files retain labeled historical raw-snapshot figures. New sales-only KPI values have not been supplied for review or committed as published reference figures. Consult the successful run's raw_kpis, sales_only_kpis, KPI comparison, and layers manifest before updating headline figures or comparing with Power BI.

## Remaining limitations

The source generator and meaning of negative quantities remain unverified. Sales-only exclusion is an explicit scope decision, not a source correction. July 2026 is incomplete. Regional reporting uses matched combinations and excludes unassigned stores. Revenue is not adjusted for returns. No business savings, operational improvement, or full production readiness is claimed.
