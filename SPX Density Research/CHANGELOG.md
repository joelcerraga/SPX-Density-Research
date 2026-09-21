# Project development record

## Milestone 10 — empirical validation and dated comparison

- Added the tenth executed notebook, using all three unchanged source snapshots on two dates.
- Replaced the call-midpoint target in this new stage with minimum curvature inside original call and put spreads; all three primary fits pass, covering 5,518 option intervals.
- Retained the infeasible late 120-bin control and its diagnostic widening; used a common 240-bin grid after disclosed pilots, without repairing quotes.
- Recorded unsuccessful physical-price formulations, objective-scaling trials and independent-price-check failures; equivalent row scaling resolves some cases while one late holdout fold remains unaccepted.
- Completed 16 of 18 attempted fit cases and 72 conditional tail-extremum LPs, retaining held-out errors and incomplete-fold coverage. Bounds are finite-basis/fixed-carry compatibility ranges, not confidence intervals.
- Added fixed-expiry and assumed common-60-day comparisons, a separately re-estimated common-contract control, and an offline explorer with observed-snapshot playback.
- Added Figures 29–33, Tables 31–36, Equations (41)–(46) and peer-reviewed reference [23]; retained author-led attribution and the Bank of England source.
- Extended the development reflection through Notebook 10, including setbacks and the unresolved numerical limitation. Updated all shared registers, input guidance and roadmap; final-paper assembly remains.
- Passed 84 tests; preserved the nine previous notebooks, three previous explorers and Figure 4 explanation placement.

## Milestone 9 — first empirical case

- Verified three supplied Cboe CSVs against the official downloads and archived them unchanged. They cover two dates, with two September snapshots.
- Added a separate actual exchange-BBO profile with unavailable market depth, explicit timing/contract screens and constrained quote-implied discount/forward estimation.
- Fitted 969 matched pairs across three SPXW horizons. Both carry inputs are re-estimated inside every selection fold.
- Preserved the primary grid's 650/1,938 spread misses and a separate post-hoc lower-grid diagnostic, which improves the call-price score but leaves 501 misses, predominantly puts. No empirical density truth or confidence band is claimed.
- Extended Notebook 9 under its existing filename; added Figures 26–28, Tables 26–30, Equations (38)–(40), source references [21]–[22] and the empirical offline 3D explorer.
- Updated the reflection, input guide, access record and roadmap. Notebook 10 and final-paper assembly remain.
- Preserved the first eight notebooks and both earlier explorers, including Figure 4 placement. See `results/marking_delivery_checks.json` for final verification.

## Notebook 9 preparation

- Reassessed primary data documentation without obtaining an accepted empirical export. Recorded the failed Cboe EOD sample request and an alternative sample's unsuitable timing; retained the original candidate unchanged.
- Added a canonical quote/discount bundle and explicit source-evidence record, with timestamp, settlement, curve-availability and row-quality checks. Supplied empty templates and a practical input guide.
- Implemented matched-pair forward intersections and a diagnostic minimum uniform widening for incompatible intervals. Incompatible cases are blocked without modifying quotes.
- Re-estimated quote-derived forwards inside every validation fold, holding out calls and puts together; allowed different pair counts across horizons.
- Executed a labelled 282-row synthetic fixture: ten joint fits, all passing the numerical checks. Retained the put price about 0.01993 points outside its spread and evaluated separate clean prices and full-domain density errors.
- Added working Notebook 9, Figures 24–25, Tables 22–25 and Equations (34)–(37). New provider references describe operational data facts; theory continues to use the scholarly sources, including Bahra.
- Extended the development reflection with data-access setbacks, training-only forward inference, distinct validity checks and the plotting-range correction. Updated the roadmap honestly: eight completed notebooks, Notebook 9 preparation in progress, Notebook 10 planned.
- Passed all 66 project tests. Verified the executed notebook, figure attachments and captions, numbering, local links, blocked-run output and protection of existing results. Preserved all eight earlier notebooks, both 3D companions and the Figure 4 explanation placement. No empirical calibration is claimed.

## Milestone 8

- Added three-candidate, three-fold smoothing selection using noisy quotes only, with endpoint retention, observation-weighted scores and a predeclared exact-tie rule.
- Evaluated the complete rule against the fixed baseline over 20 new paired realisations per benchmark/pattern, using separate clean prices, full-domain density errors and fixed tail events.
- Recorded 80 selection experiments and 160 nonzero forward stresses: 1,000 accepted joint fits and 8,000 marginals, with no failed or blocked experiment. Saved every CV fit and the dependencies between selected fits and forward cases.
- Retained the observed selection limitation: better interior price fit could accompany worse extrapolation or density recovery. Added an explicitly post-hoc range diagnostic without changing the selection rule.
- Tested ±0.1% and ±0.5% forward-input errors with unchanged physical risk thresholds and a supplied-forward call lower-bound diagnostic.
- Added Notebook 8, Figures 21–23, Tables 18–21 and Equations (30)–(33), plus Cawley and Talbot's peer-reviewed reference [17]. Retained the Bank of England source and author-led attribution.
- Extended the development reflection through Notebook 8, covering evaluation targets, uneven folds, coordinate consistency, incompatible price inputs and the corrected uniform-distribution test fixture.
- Added a working ten-notebook roadmap: two empirical stages remain conditional on verified observations, followed by the combined paper and its requested opening pages and lists.
- Passed 55 tests. Preserved all seven earlier notebooks, both interactive companions and the user's Figure 4 placement. This remains a synthetic study.

## Milestone 7

- Added 50 paired repetitions for each of two benchmark families, four nested strike patterns and two bounded-error amplitudes, plus eight clean-input controls: 808 accepted joint fits and 6,464 marginals.
- Separated quote count from quote placement through two 41-quote designs and evaluated every pattern on the same withheld prices.
- Declared a symmetric positivity-preserving synthetic error model, recorded its limitations and exported every observation and generator state.
- Distinguished bias, empirical SD and Monte Carlo standard errors, with paired contrasts and explicit clean-input approximation errors.
- Added Notebook 7, Figures 18–20, Tables 14–17 and Equations (26)–(29), with data-generated numerical commentary.
- Preserved each attempted case with solver diagnostics, code/protocol fingerprints and content checksums; incomplete groups are excluded from aggregate publication rather than silently averaged.
- Added Morris, White and Crowther's peer-reviewed simulation-methodology paper; retained the Bank of England source and updated the final-paper registers.
- Extended the development reflection through Notebook 7 with the comparison-design problem, bounded-noise decision, repeated-error interpretation and remaining limitations.
- Detected an empty standalone figure during the final artifact check, recovered the intact notebook image and added verified temporary-file exports before replacing figure files.
- Passed 45 tests. Preserved all six earlier notebooks, both offline 3D companions and the user's Figure 4 layout.

## Milestone 6

- Added seven declared support, resolution and smoothing choices for each of two known synthetic benchmark families, giving 14 joint fits and 112 marginals.
- Added a two-lognormal mixture benchmark with common forwards and maturity-independent mixture weights; reused the original strike grids and paired quote noise.
- Made smoothing comparisons explicit across grids and included omitted benchmark probability in full-domain density error.
- Added exact histogram tail probabilities and terminal-level variance, with known values beside sensitivity ranges.
- Added an equivalent residual-variable formulation and Clarabel backend after OSQP failed strict convergence checks on the broader benchmark. Retained earlier OSQP defaults and tested agreement on a controlled problem.
- Added Notebook 6, Figures 15–17, Tables 11–13 and Equations (20)–(25), with data-generated tables and commentary.
- Added primary research by Malz and Goulart–Chen, retained Bahra and updated the front-matter registers.
- Added the paper section **Development challenges, corrective actions and lessons learned**, covering Notebooks 1–6 with supporting artifacts, unsuccessful attempts and unresolved limitations.
- Passed 35 tests, including independent mixture payoff/moment integration and reconstruction of calendar and risk results from saved weights.
- Preserved the first five notebooks, both interactive companions and the user's Figure 4 placement. This remains a synthetic study using one noise realisation.

## Milestone 5

- Added joint calendar-constrained fitting and an independent OSQP control on unchanged Milestone 4 synthetic inputs.
- Added an interval-level check, including interior quadratic minima, and iterative constraint refinement. The joint fit passes at the stated tolerance across adjacent fitted maturities; no intermediate-maturity model is claimed.
- Added Notebook 5, Figures 12–14, Tables 9–10 and Equations (16)–(19). Documented the remaining tail discrepancy and the small trade-off in density error.
- Added an offline 3D comparison of joint, independent and known surfaces, with linked density slices and a calendar-gap plot.
- Added the peer-reviewed OSQP reference, retained the Bank of England source and updated the paper's working registers.
- Retained raw signed numerical residuals without clipping or renormalisation, and recorded solver histories and input checksums.
- Passed 24 numerical and artifact checks; verified interactive controls offline in Chromium and inspected desktop/mobile layouts.
- Preserved the first four notebooks, including the user's Figure 4 explanation placement. No empirical calibration or historical animation was added.

## Milestone 4

- Added eight synthetic maturity fits, an explicit calendar-consistency diagnostic and a transparent report of extrapolated-wing violations.
- Added an offline interactive 3D explorer with rotation, zoom, hover, known/fitted surface selection, maturity play/pause and a linked exact histogram slice.
- Added Notebook 4, Figures 10–11, Tables 7–8 and Equations (13)–(15), with captions beneath the plots.
- Added Gatheral and Jacquier's research paper through author-led attribution; retained the Bank of England source and updated all paper registers.
- Recorded historical-date animation as a future stage conditional on suitable verified snapshots. No historical animation or empirical calibration is claimed.
- Kept the first three notebooks unchanged, including the user's Figure 4 explanation placement.
- Passed 16 project tests and verified the explorer's controls offline in Chromium, including hover, rotation and zoom.

## Milestone 3

- Added a finite-support, regularised probability-density estimator and its synthetic validation runner.
- Added the third notebook, Equations (9)–(12), Figures 7–9 and Tables 5–6.
- Added independent payoff-integration and price-derivative tests, with nine project tests passing at handoff.
- Added the working paper registers and a data-access decision note.
- Retained the section symbols (§ and §§) and the author-led scholarly referencing style.
- Preserved the first notebook's Figure 4 → caption → explanation order, now protected by a regression test.
- All market-calibration limitations from Milestone 2 remain in effect. This milestone is synthetic only.

## Milestones 1–2

- Established the clean synthetic density benchmark and a candidate SPX quote audit.
- Moved figure captions outside the exported images and introduced consistent equation numbering.
- Expanded the bibliography and attributed established methods separately from this project's findings.

Each milestone ZIP contains the complete project at that stage. Keep locally edited files backed up before replacing a downloaded folder.
