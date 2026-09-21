# Research roadmap and completion criteria

The completed scope contains **ten analytical notebooks and the assembled final paper**. This is a scope estimate rather than a fixed promise: verified market observations may expose an additional data or modelling issue. Notebook count is not an equal measure of effort.

| Notebook | Purpose | Status after Notebook 10 |
|---|---|---|
| 1 | Establish and validate density extraction on clean synthetic prices | Complete |
| 2 | Audit candidate SPX data, provenance and quote quality | Complete; original candidate remains an audit example |
| 3 | Fit nonnegative, unit-mass densities with the required forward mean | Complete |
| 4 | Extend across maturities and build interactive 3D views | Complete |
| 5 | Enforce and check cross-maturity consistency jointly | Complete |
| 6 | Test support, resolution, smoothing and a mixture benchmark | Complete |
| 7 | Repeat quote-error experiments and compare strike coverage | Complete |
| 8 | Separate smoothing selection from evaluation; stress supplied forwards | Complete |
| 9 | Calibrate to verified SPX observations with documented settlement, discounts and parity forwards | Complete first case: 969 observed SPXW pairs, quote-implied carry, residual and sensitivity checks; limitations retained |
| 10 | Validate empirical fits, compare observation dates and add historical-date interaction | Complete limited case: original-spread fits, three-snapshot comparison, conditional risk ranges, paired holdouts and dated 3D explorer; one unresolved fold disclosed |

All **ten planned analytical notebook stages are complete**, with their limitations retained. **The final Word and PDF paper is assembled, with its conclusion and consolidated development reflection.** Notebook 10 reports 16 accepted fit cases, one grid-incompatible control and one numerically unresolved holdout fold. All three primary fits meet the original call/put spreads at the stated tolerance, but the held-out errors and conditional tail ranges show why this does not establish density accuracy. Completion denotes the documented scope of this two-date case study, not a claim of universal empirical validation.

## What counts as finished

The synthetic method must be reproducible, numerically checked and explicit about recovery errors. The empirical stage must have an archived, permitted research source, a verified observation timestamp and timezone, contract settlement details, usable contemporaneous bid/ask observations and justified discount/forward inputs. A calendar-consistent fitted surface does not validate missing source metadata. The original candidate still fails its gate. The supplied marking-price files support a separate exchange-BBO profile with quote-implied carry and unavailable actual depth; see [data access status](data_access_status.md).

The empirical notebooks should report coverage, exclusions, residuals against usable bid–ask information, density/tail sensitivity and limitations. Comparing dates also requires consistent contract treatment and horizons. Neither paid access nor a particular provider is assumed by this plan. If adequate data remain unavailable, the final scope must explicitly become a synthetic methodology study with a documented data audit, rather than claim empirical SPX findings.

## Assembled final paper

The final paper combines the research question, referenced mathematical foundation, data assessment, method, synthetic and empirical evidence, development reflection and limitations into one argument. It includes Joel Cerraga's title page, abstract, table of contents, lists of figures, tables and equations, abbreviations, mathematical symbols and units, and a shared reference list. Printed page references are reconciled against the rendered layout; the editable source and document checks are in `paper/`. The maintained [paper registers](paper_registers.md) and [development reflection](development_reflection.md) supply the material for this stage.

Four offline explorers are delivered: two synthetic, the first empirical maturity surface, and the dated comparison in `interactive/dated_density_surface.html`. The last steps through three observed snapshots on two dates, with separately labelled common-horizon interpolation and common-contract controls. Two dates do not establish a historical time series. The previous notebooks and their captions—including the Figure 4 explanation beneath the figure—remain preserved in cumulative releases.
