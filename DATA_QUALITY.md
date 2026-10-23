# Raw snapshot and sales-only eligibility policy

## Confirmed source condition

The supplied full-data diagnostics identified 249 negative-quantity order lines out of 44,290. All 249 have missing StoreID. Another 236 positive-quantity lines have missing StoreID. No zero/missing quantities or excess returned units on positive-quantity sales were reported. There are 23 return records linked to the negative-quantity lines.

This does not establish whether negative quantities were intended reversals, injected training anomalies, or preparation errors. Neither a generator nor authoritative transaction semantics has been recovered. Do not describe the source values as corrected.

## Explicit analysis decision

Keep the original CSVs unchanged and pin their seven SHA-256 hashes. Preserve raw signed quantities in raw reproduction. For a separate sales-only analysis, quarantine all nonpositive/missing-quantity order lines and all return records linked to those excluded lines. No ABS conversion, quantity cap, inferred StoreID, relinking, or source deletion is performed. Linked returns are unresolved, not proven incorrect.

For this fixed snapshot, expect 249 quarantined order lines and 23 quarantined returns. The sales-only tables contain 44,041 order lines and 2,634 returns. Keep the 236 positive lines with missing stores in company-wide results as unassigned. Existing regional queries still exclude unassigned stores. Distinct order count and financial metrics must be calculated, not assumed unchanged.

## Run

Python 3.12 with its bundled SQLite is the CI environment; no pip dependencies are required.

```sh
python -m unittest discover -s tests -v
python scripts/analyze_layers.py
```

The older scripts/reproduce.py remains a strict raw-data validator and is expected to reject the known negative quantities. Its failure must not be mistaken for failure of the new explicitly scoped sales-only workflow. REPRODUCIBILITY.md describes the underlying loader and original strict workflow; this document defines the layered policy.

## Checks and outputs

The layered runner checks source hashes and raw row counts, keys, references, numeric domains, the exact negative/missing-store profile, linked-return count, and over-returns on positive sales. The raw snapshot is labeled known-dirty, even when its observed exceptions match the documented snapshot. Both raw KPI and category outputs must still match the historical reference CSVs.

A separate in-memory database is then copied from the raw database and partitioned. All existing strict validation checks run on the sales-only tables with their adjusted counts and 236 expected missing stores. The existing ten analytical SQL files run unchanged against both databases. Any new source hash, unexpected profile, baseline mismatch, or strict sales-only failure stops the workflow.

- build/raw/: raw analytical outputs, including unresolved signed quantities.
- build/sales_only/: outputs from the explicitly scoped sales-only population.
- build/quarantine/: excluded source records with reasons, preserving original values.
- build/kpi_comparison.csv: raw versus sales-only KPI values and differences in reported units; percentage differences are percentage-point differences.
- build/layers_manifest.json: validation evidence, input/code hashes, runtime versions, policy, and both KPI sets.

The manifest is invalidated at the beginning of each run and published last after success. Older CSVs may remain after a failed local rerun; they are not evidence of a current passing run. CI uses a clean checkout. Published results/ files remain raw reference outputs and are never overwritten automatically.

## Verification boundaries

Six isolated fixture tests of raw exception validation and partition behavior passed during preparation. On October 22, 2026, the maintainer subsequently reported that the workflow passed after the portability update. See VERIFICATION.md for the evidence level and limitations; the assistant did not independently retrieve that Actions result. New sales-only financial figures remain unpublished pending review.

Do not claim improved business performance, recovered source intent, or a fully clean original dataset. Sales-only results describe an eligible subset. July 2026 is incomplete; the existing regional query reports matched sales/target combinations only. Revenue is after discounts and is not adjusted for returns. Reassess conclusions and any Power BI comparison before updating headline portfolio metrics.
