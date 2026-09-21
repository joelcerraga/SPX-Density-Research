# Inputs for the empirical calibration and dated comparison

Notebooks 9 and 10 use the three supplied marking-price CSVs for the first empirical calibration and a limited dated comparison. **No additional file is required to reproduce these cases.** The original canonical profile remains available for future sources with documented external discounts and actual sizes. These profiles have different evidence and must not be mixed.

## Supplied marking-price profile: ready to reproduce

The original files are archived in `data/raw/marking_prices/`. The [empirical methodology](marking_methodology.md) records source verification, field meanings, contract times and limits. This profile uses actual exchange bid/ask columns, records actual size as unavailable, and estimates both discount and forward from matched call–put quotes. It does not populate canonical NBBO/size fields with indicative data or describe inferred carry as an external curve.

The first fit uses 18 September 2026 at 15:00 Chicago time and three SPXW expiries. The EOM file contains 31 August; the late EOD file is a second September snapshot. Notebook 10 now uses both alongside the first snapshot; they comprise two dates and three observations. Raw inputs remain unchanged, and their hashes match the archived official-download checks.

```bash
python run_marking_calibration.py
python run_marking_diagnostic.py
python build_marking_report.py
python build_marking_html.py
```

The second command is an explicitly post-hoc lower-smoothing diagnostic. The primary fit misses 650 of 1,938 spreads, and its tails are sensitive; the separate diagnostic improves the call-price criterion without resolving put reproduction. These outcomes are recorded rather than suppressed. `python build_milestone9_notebook.py` recomputes the synthetic preparation and both empirical runs, then assembles the complete ninth notebook and offline companion. No network access is required.

## Notebook 10: the same archived inputs

Run `python build_milestone10_notebook.py` to recompute the original-spread feasibility checks, minimum-curvature fits, conditional tail ranges, paired holdouts and date-aware offline explorer. This keeps the previous notebooks and outputs unchanged. The [comparison methodology](comparison_methodology.md) records the post-pilot 240-bin choice, one blocked coarse-grid control, one numerically unresolved holdout fold and the limits of common-horizon interpolation. No quotes are repaired or widened in the accepted fits.

The files support a two-date case study. A longer time-series analysis, independently supplied carry or uncertainty beyond the finite-bin/fixed-carry family would require additional evidence. Those are limitations of this completed scope rather than missing inputs for its reproduction.

## External-curve profile for future exports

### What this separate profile requires

A provider's original CSV export, its field specification and the observation date would be the most useful next inputs. Include its quote timestamp/timezone and snapshot convention, contract settlement information, bid/ask prices and sizes, and the source or basis for the discount curve. An existing authorised Cboe or institutional research export can be assessed; no purchase or subscription has been assumed. Keep the original file intact. If some metadata come in separate documentation, provide those files too: they should not be guessed from the prices.

The canonical workflow fits **one synchronised observation, one trading class and at least two distinct settlement horizons**, with at least seven usable call–put pairs per horizon. These are this implementation's requirements, not a universal statistical sufficiency rule. More pairs do not by themselves establish adequate tail coverage. SPX and SPXW are assessed in separate bundles; their settlement conventions must be verified for the actual contracts [5].

The model retains deterministic carry and proportional-dividend assumptions for cross-maturity ordering, as discussed through Gatheral and Jacquier [12]. Their suitability for an empirical application needs to be stated. The importer does not establish them from a quote file.

## Canonical bundle

Copy the three empty files in `data/templates/empirical_input/` into a new data folder and populate them from the source. Empty templates intentionally fail validation. The supplied, executable example in `data/fixtures/empirical/` is labelled synthetic throughout and must not be reclassified as observations.

**`quotes.csv`** has one row per quoted option:

| Field | Meaning and required convention |
|---|---|
| `quote_id` | Unique source-linked row identifier; duplicates are excluded, not averaged |
| `snapshot_id` | Identifier for this one common observation |
| `observed_at` | Complete ISO datetime with an explicit offset, e.g. `2026-01-15T15:45:00-05:00`; this example is a format illustration |
| `root` | One class, `SPX` or `SPXW`, throughout the bundle |
| `expiry` | Provider's contract expiry date, `YYYY-MM-DD` |
| `settlement_at` | Verified settlement datetime with offset; do not infer it from the expiry date alone |
| `exercise` | `European` |
| `settlement_style` | `AM` for SPX or `PM` for SPXW; the actual settlement datetime still needs evidence |
| `option_type` | `C` or `P` |
| `strike`, `bid`, `ask` | Index points; finite positive values with bid no greater than ask |
| `bid_size`, `ask_size` | Positive integer displayed contract counts under the documented source convention |

All observation timestamps must identify the same instant after UTC conversion. Retrieval time, underlying last-trade time and the last update of each separate option are not interchangeable with that snapshot. Time to settlement is elapsed UTC seconds divided by $365\times24\times60\times60$; this ACT/365F convention is a project choice. A UTC-offset change therefore affects the horizon. Expiry dates remain labels, not replacements for settlement times.

The first screen uses spread divided by midpoint no greater than 25%, consistent with Equation (6), and requires positive sizes. This deliberately conservative size policy cannot be applied to undocumented zero fields as an explanation of market liquidity. Every exclusion retains its reason; duplicate sides also leave their surviving counterpart unmatched. Conflicting metadata block the bundle. Entirely excluded expiries remain visible in the failure report.

**`discounts.csv`** contains one record per snapshot, class and settlement datetime:

| Field | Meaning |
|---|---|
| `snapshot_id`, `root`, `settlement_at` | Exact matching keys for the quoted horizon |
| `discount` | Positive finite discount factor from quote time to settlement; values above one are allowed |
| `observed_at` | Time represented by the source curve |
| `available_at` | Time that curve information became available; must be no later than the quote snapshot |
| `source_reference` | Curve source, tenor interpolation and conversion basis, or a reference to an accompanying methodology file |

Curve observation cannot follow its availability. The age limit is an explicit screening input, set to 86,400 seconds in the test fixture, rather than a universal accepted staleness threshold. The application must justify its choice. Quote-time discounts are supplied directly: the code does not silently substitute today's rate, infer a curve from the calls, or assume a vendor's implied-volatility rate is the appropriate discount factor.

**`manifest.json`** records the classification, conventions, source evidence, numerical screens and SHA-256 checksums of both CSVs. Market inputs also need an attributable source-review record: reviewer, review datetime, decision and supporting notes. This is a record of evidence reviewed for the project, not software certification or a new approval service. Nonempty fields and matching checksums do not prove authenticity, synchronisation, correct economics or permission. Those claims must be checked against the actual documentation. A file hash detects changes after that review.

As Aït-Sahalia and Lo explain in their option-density paper [10, §III.A], put–call parity connects the European call, put and forward. This workflow uses matched bid/ask pairs and a supplied discount to construct a conditional forward interval, then uses call midpoints for the density objective. It does not treat the call and put as two independent training observations. Notebook 9 explains the intersection, blocked cases and separate put residuals.

## Mapping a provider export

For Cboe's **Option EOD Summary**, the documented 15:45 fields are `bid_1545`, `ask_1545`, `bid_size_1545` and `ask_size_1545`, alongside `root`, `expiration`, `strike` and `option_type` [18]. Map `expiration` to `expiry`. Supply the verified snapshot and settlement datetimes separately: the 15:45 columns represent **12:45 Eastern on early-close days**. The exchange-session calendar must therefore be checked before conversion. No automatic date-to-time adapter is claimed from an uninspected sample.

For an institutional OptionMetrics export, provide the applicable field specification and sampling convention with the file. WRDS documents option bid/ask and curve data as part of that product [20], but this does not establish access, availability timestamps or the exact schema of an unseen export. It needs the same source assessment.

## Run and interpret

After populating and reviewing the bundle, from the project folder:

```bash
python run_market_calibration.py data/your_reviewed_bundle --output results/your_snapshot_fit.json
```

The output path must be new. Missing evidence, inconsistent metadata, missing discounts or an empty parity intersection produce a blocked result rather than a density. The runner exits with code 2 for a blocked run. Suitable inputs proceed through three candidate smoothing values, three paired interior holdouts per candidate, training-only forward inference and the selected full-data joint fit. Every fold retains weights, forward bounds, membership, residuals and solver diagnostics. Both end strikes stay in training; this is interpolation-based selection, not a temporal backtest.

Assess the resulting row audit, strike coverage, parity bounds, numerical constraints and **both call and put spread residuals**. The objective does not impose bid/ask inequalities, so passing the structural checks is not a guarantee of fitting every spread. The selected CV score is not an unbiased empirical performance estimate. Market tail uncertainty still requires the sensitivity and separate validation planned for the empirical stage; a fixture's known density is unavailable in market data.

To reproduce the preparation exercise and its notebook:

```bash
python build_milestone9_notebook.py
python -m unittest discover -s tests -v
```

The builder regenerates the labelled fixture, first empirical case, range diagnostic, figures, Notebook 9 and new empirical companion. Earlier notebooks and both earlier interactive companions remain unchanged. Source records, publication types and attribution are maintained in [references.md](references.md).
