# SPX option-implied density research
## Final paper and all ten analytical notebooks complete

A reproducible investigation of option-implied risk-neutral densities. Notebook 10 fits the original call and put spreads across **three observed snapshots on two dates**, using archived exchange-BBO inputs and separately inferred carry. All 5,518 retained option prices fall within their original spreads at the declared tolerance in the three primary 240-bin fits. Held-out spread errors, an unresolved late-snapshot validation fold and broad conditional tail ranges remain explicit.

All ten planned analytical notebooks and the final paper are complete. Read **`paper/SPX-Option-Implied-Density-Final-Paper.pdf`** for the assembled report, or edit **`paper/SPX-Option-Implied-Density-Final-Paper.docx`**. The paper includes the conclusion, development chapter, full front matter and verified numbered lists. The limited two-date case study retains its unresolved fold and other qualifications. Earlier milestone notes below record their historical handoffs.

![Recovered density](figures/figure_02_density_recovery.png)

### Start here
1. Open the final PDF or Word paper in `paper/`. See `paper/README.md` for the source and document-rebuild instructions.
2. Read `research/methodology.md` for the derivation, assumptions and references.
3. Open `01_synthetic_density.ipynb` in VS Code with the Python and Jupyter extensions. Saved outputs are included.
4. Continue through `02_market_data_audit.ipynb`, `03_constrained_density.ipynb`, `04_density_surface.ipynb`, `05_joint_density.ipynb`, `06_density_robustness.ipynb`, `07_noise_and_coverage.ipynb`, `08_smoothing_and_forwards.ipynb`, then `09_empirical_preparation.ipynb` and `10_empirical_comparison.ipynb`. The ninth retains its synthetic preparation and first empirical case; the tenth adds price compatibility and dated comparisons.
5. Use the runners below to regenerate the corresponding figures and results.
6. Open `interactive/dated_density_surface.html` for the new date-aware 3D explorer. The three earlier explorers remain at `interactive/empirical_density_surface.html`, `interactive/joint_density_surface.html` and `interactive/density_surface.html`. No Python installation is needed to view these offline files.
7. Read `research/development_reflection.md` for the paper's account of challenges, attempted solutions, checked outcomes and lessons through Notebook 10, including unresolved limitations.

### Local setup
Install Python 3.11 or newer. Open a terminal in this extracted project folder.

```bash
python -m venv .venv
```
Windows PowerShell: `.venv\Scripts\Activate.ps1`  
macOS/Linux: `source .venv/bin/activate`

```bash
python -m pip install -r requirements.txt
python run_experiment.py
```
Select this environment as the notebook kernel, then run its cells from top to bottom. The notebook uses the project folder as its working directory. Figure-display cells load the generated files; rerun `run_experiment.py` after changing its experiment parameters.

### Files
- `src/density.py`: call pricing, analytical density, finite differences and diagnostics.
- `run_experiment.py`: deterministic figure generation and acceptance checks.
- `01_synthetic_density.ipynb`: executed explanatory notebook.
- `research/methodology.md`: working methodology, not a finished empirical paper.
- `figures/`: numbered PNG and editable SVG figures.
- `results/`: numerical density, validation metrics and noise diagnostic.
- `environment.json`: versions used to generate the supplied outputs.

### Validation
Mass, non-negativity, density error, forward consistency and repricing checks pass for the supplied synthetic parameters. Grid refinement confirms approximately second-order convergence. No clipping or renormalisation is used. Repricing compares five strikes (4,800–7,200) and is measured in index points, not dollars per contract.

### Initial benchmark scope (Milestone 1)
The benchmark assumes European exercise, deterministic rates and dividends, and constant volatility. It has no smile, bid/ask spread, calibration, historical backtest or predictive claim. The original data assessment is recorded in Milestone 2; the subsequent supplied-file assessment and market case are in Notebook 9, Part B. Graph diffusion and trading-strategy work belong to a later, separate project.

### Milestone 2: candidate quote audit
Open `02_market_data_audit.ipynb` and read `research/market_data_methodology.md`.

```bash
python run_quote_audit.py
python -m unittest discover -s tests -v
```

The new runner verifies the raw snapshot checksum, preserves row-level exclusion reasons, writes expiry coverage and a JSON report, and regenerates Figures 5–6. Captions are outside the images. Equations (5)–(8) continue the methodology numbering.

The full quote date/timezone and settlement horizons are unresolved, and all quoted sizes in this payload are zero. `local_price_screen_pass` does not mean a quote is approved for calibration. The audit deliberately reports `density_estimation_ready: false`. No empirical density or forward is estimated.

`data/raw/` preserves the candidate JSON and provenance. `data/processed/quote_audit.csv` retains every row with screening results. Keep raw and row-level data private until redistribution rights are established. This package is not yet a public GitHub release.

### Research references
The methodology and notebooks now use author-led academic attribution. See `research/references.md` for the shared bibliography, source access notes and the equation-to-source mapping. Calculations and figures are unchanged by this reference revision.

### Milestone 3: constrained synthetic density

Open `03_constrained_density.ipynb` and read `research/constrained_methodology.md`.

```bash
python run_constrained.py
python -m unittest discover -s tests -v
```

The fitter estimates nonnegative interval probabilities with unit mass and a mean equal to the supplied forward. It balances squared price errors against a smoothing penalty. Equations (9)–(12) describe the implementation, and Figures 7–9 show the price fit, density comparison and smoothing sensitivity. Probability and forward consistency are constraints, not independent evidence of density accuracy.

This benchmark uses 81 synthetic call prices and 120 density intervals. The baseline has 0.246113 index-point RMSE at withheld clean strikes, and an integrated density absolute error of approximately 0.031 on the selected support. It is one controlled experiment, not a verified market fit or a historical out-of-sample result. See `research/data_access_status.md` for the remaining quote-data questions.

Additional files:

- `src/constrained.py`: exact interval-payoff matrix and constrained fitting.
- `tests/test_constrained.py`: independent pricing checks, invalid inputs, shape and layout checks.
- `results/constrained_validation.json`: settings and diagnostics for all three penalties.
- `results/constrained_bin_masses.csv`: the fitted baseline interval probabilities.
- `research/paper_registers.md`: working figures, tables, equations, abbreviations and symbols for the final paper.
- `build_milestone3_notebook.py`: rebuilds the third notebook from the methodology and regenerates its outputs.

The paper's final title page, abstract, contents and page-numbered lists will be assembled in the Word/PDF stage. Section symbols (§/§§) are retained. A regression test protects the Figure 4 → caption → explanation order in the first notebook.

### Milestone 4: multiple maturities and the first dynamic 3D companion

Open `04_density_surface.ipynb` and read `research/surface_methodology.md`.

```bash
python run_surface.py
python build_surface_html.py
python -m unittest discover -s tests -v
```

Alternatively, `python build_milestone4_notebook.py` executes the experiment, rebuilds the offline explorer and refreshes the fourth notebook's embedded figures. The saved notebook was built by directly executing its Python runner, without assuming a local Jupyter kernel.

The explorer includes a rotatable, zoomable 3D surface, hover values, a known/fitted comparison, an eight-horizon maturity slider and a play/pause sweep. A linked 2D panel preserves the exact fitted histogram steps. Both plots have fixed scales across selections. Captions remain below their plots.

**This is a synthetic maturity sweep, not a historical market animation.** The eight horizons run from 30 to 365 days at one valuation setup. Connecting surface facets are graphical interpolation, not fitted intermediate maturities. Historical-date animation is explicitly planned, but requires verified snapshots and documented horizon alignment.

All eight marginal fits satisfy their probability constraints. A separate calendar diagnostic finds 2,762 decreases above tolerance in 13,307 full-grid comparisons, all outside the shared quote ranges. This fitted collection is **not arbitrage-free across maturities**. Joint calendar constraints and tail-support sensitivity are the next numerical steps; no inconsistencies are hidden or repaired after fitting. The known analytical benchmark passes the same diagnostic.

Additional files:

- `src/surface.py`: normalised call prices, calendar diagnostic and exact interval probability.
- `run_surface.py`: deterministic multi-maturity experiment and Figures 10–11.
- `results/surface_validation.json`: marginal and cross-maturity diagnostics.
- `results/maturity_surface.json`: display data and assumptions used by the explorer.
- `results/maturity_quotes.csv`, `results/maturity_bin_masses.csv`: synthetic inputs and fitted probabilities.
- `interactive/surface_template.html`, `build_surface_html.py`: editable explorer source and offline builder.
- `interactive/vendor/`: pinned plotting bundle and its MIT licence; no network download occurs when viewing or rebuilding.
- `tests/test_surface.py`: numerical, export and notebook checks.

At the Milestone 4 handoff, all 16 project tests passed. That explorer was also checked in Chromium with the network disabled: pointer hover, rotation, scroll zoom, keyboard maturity selection, known/fitted switching and play/pause all worked, with no JavaScript errors or external requests. Its browser-check record is `results/surface_browser_checks.json`.

Milestone 4 extended the paper registers to 11 figures, 8 tables and 15 equations. Reference [12] adds Gatheral and Jacquier's research on calendar and slice consistency. The Bank of England source remains in use, and the earlier notebooks—including the Figure 4 layout—are unchanged.

### Milestone 5: fitting the maturities together

Open `05_joint_density.ipynb` and read `research/joint_methodology.md`. Install the updated requirements to add OSQP before regenerating this milestone.

```bash
python -m pip install -r requirements.txt
python run_joint.py
python build_joint_html.py
python -m unittest discover -s tests -v
```

Alternatively, `python build_milestone5_notebook.py` runs both builders and refreshes the fifth notebook's embedded figures. Its saved Python cell was executed directly, without assuming a Jupyter kernel. The comparison reads the included Milestone 4 result files; it does not overwrite the first four notebooks or their results.

The joint estimator adds calendar constraints to the existing eight-maturity experiment. A new check evaluates endpoints and interior quadratic minima, covering all nonnegative strikes for each adjacent maturity pair under the common-bin model. It catches violations that bin-boundary constraints alone miss and adds those locations to the next solve. Five solves meet the refinement target.

The independent OSQP control has 2,763 violations on the comparison grid; the joint fit has zero above the $10^{-8}$ tolerance. The interval-level minimum joint gap is approximately $-8.56\times10^{-10}$. Small signed solver residuals are retained and disclosed. These are numerical checks at the fitted maturities, not an exact symbolic guarantee or a fitted interpolation across time.

Pooled withheld-price RMSE changes from 0.119513 to 0.119153 index points; mean density $L_1$ increases slightly, from 0.035158 to 0.035162. The principal result is improved consistency. Tail accuracy, support sensitivity and empirical validity remain separate questions. Figure 13 explicitly shows the remaining tail discrepancy.

The updated offline explorer compares joint, independent-control and known surfaces. It retains rotation, zoom, hover, keyboard maturity selection and play/pause, adds a three-curve slice, and displays the calendar-gap comparison. This remains a synthetic maturity sweep; historical-date animation awaits verified snapshots.

Additional files:

- `src/joint.py`: joint quadratic programme and interval-level calendar check.
- `run_joint.py`: unchanged-input comparison and Figures 12–14.
- `results/joint_validation.json`: probability, price, density and solver diagnostics, including input checksums.
- `results/joint_bin_masses.csv`, `results/joint_surface.json`: probabilities and explorer data.
- `interactive/joint_surface_template.html`, `build_joint_html.py`: editable source and self-contained HTML builder.
- `tests/test_joint.py`: a non-lognormal counterexample, joint fitting and saved-output checks.
- `results/joint_browser_checks.json`: offline browser verification of the new controls and mobile layout.

At the Milestone 5 handoff, the suite contained 24 passing tests. Offline Chromium checks found no JavaScript errors or external requests. Its paper registers covered 14 figures, 10 tables and 19 equations. Reference [13] adds Stellato and co-authors' peer-reviewed OSQP paper, with author-led attribution. The Bank of England reference and planned final-paper front matter are retained.

The first four notebooks are byte-for-byte unchanged from Milestone 4, including the Figure 4 explanation placement. New figure captions appear beneath their plots.

### Milestone 6: support, resolution and smoothing sensitivity

Open `06_density_robustness.ipynb` and read `research/robustness_methodology.md`.

```bash
python -m pip install -r requirements.txt
python build_milestone6_notebook.py
python -m unittest discover -s tests -v
```

The builder reruns all 14 joint fits, updates the methodology's numerical tables and commentary, and embeds Figures 15–17 in the notebook. It can take several minutes. Edit `research/robustness_methodology_template.md` for lasting prose changes; its rendered counterpart is generated. For prose-only edits, use `python build_milestone6_notebook.py --refresh-narrative` to retain the existing numerical run and its execution output. `python run_robustness.py` regenerates numerical files, tables and figures without rebuilding the narrative notebook.

The study compares seven declared choices across the original single-lognormal benchmark and a mixture with weights 0.75/0.25 and volatilities 14%/40%. It reuses the existing strike grids and the same quote-noise realisation for both families. The mixture is a known test distribution; the estimator still fits histogram probabilities.

The resolution and support comparisons keep the coefficient of a grid-scaled roughness penalty fixed. This accounts for the fact that the raw smoothing coefficient in Equation (12) is not directly comparable across bin widths. Full-domain density error includes known probability outside each fitting support. Exact histogram integrals report tail probabilities and normalised terminal-level variance. The displayed ranges are sensitivity summaries, not statistical confidence intervals.

This milestone uses the Clarabel backend and an equivalent formulation with explicit residual variables after strict OSQP convergence checks failed for the broader mixture. The earlier OSQP defaults remain available. All study cases use the same solver, formulation and acceptance criteria, and the code rejects inaccurate solver status. The two formulations are compared on an independently specified test problem.

Additional files:

- `src/robustness.py`: mixture benchmark, smoothing conversion, density errors and risk summaries.
- `run_robustness.py`: paired-input study, generated tables and scientific figures.
- `build_milestone6_notebook.py`: executes the study and updates the sixth notebook and methodology.
- `results/robustness_validation.json`: complete final-study diagnostics and solver histories.
- `results/robustness_quotes.csv`, `results/robustness_bin_masses.csv`, `results/robustness_metrics.csv`: auditable numerical exports.
- `tests/test_robustness.py`: independent payoff/moment integration, penalty scaling, solver equivalence and saved-result checks.
- `research/development_reflection.md`: paper section covering documented setbacks, unsuccessful attempts, corrective actions and remaining limitations; maintained through the latest notebook.

The suite now contains 35 passing tests. The paper registers cover 17 figures, 13 tables and 25 equations. References [14] and [15] add Malz's New York Fed research paper and Goulart and Chen's Clarabel research preprint; their publication types are stated explicitly. Author-led attribution and the Bank of England source are retained.

The first five notebooks and both offline 3D companions are byte-for-byte unchanged from Milestone 5. Your Figure 4 explanation remains below its figure and caption. Historical-date animation and empirical calibration still depend on suitable verified market data.

The combined paper will include **Development challenges, corrective actions and lessons learned** as a dedicated section. Its current draft links the account to the saved calculations and distinguishes unexpected problems, deliberate stress tests and unresolved data questions. Extend this record with each subsequent notebook; retain unsuccessful approaches where they explain a methodological decision. The final title page, abstract, contents and all requested lists remain tracked in `research/paper_registers.md`.

### Milestone 7: repeated quote errors and strike coverage

Open `07_noise_and_coverage.ipynb` and read `research/repeated_methodology.md`.

```bash
python build_milestone7_notebook.py
python -m unittest discover -s tests -v
```

The builder checks and reuses matching saved cases, computes missing cases, and generates the report's tables, numerical commentary and embedded Figures 18–20. To recompute the complete experiment, use:

```bash
python run_repeated.py --fresh --workers 4
python build_milestone7_notebook.py
```

A fresh run takes several minutes, depending on hardware. Use `--workers 1` for a sequential run. The runner fixes numerical-library thread counts to one per process. Each completed case has a code-and-protocol fingerprint and content checksum; a mismatch requires an explicit fresh run. Edit `research/repeated_methodology_template.md` for lasting narrative changes. `python build_milestone7_notebook.py --refresh-narrative` refreshes prose, tables and figures without rerunning the numerical fits.

This study has 50 paired repetitions for each combination of two benchmark families, four quote patterns and two noise limits, plus eight clean-input controls: **808 accepted joint fits and 6,464 marginal distributions**. The patterns distinguish reducing quote count from narrowing the range at a fixed count. The extended pattern adds both range and observations. All patterns use the same withheld evaluation prices.

The new bounded-error model keeps small synthetic option prices positive without clipping. Its assumptions differ from the earlier uncapped perturbations and are stated in Equation (26). Performance summaries distinguish signed bias, dispersion across repetitions and Monte Carlo uncertainty in an average. These are simulated performance measurements, not market-probability confidence intervals.

At the 0.5-point noise limit, the mixture's mean density error is approximately 0.1223 with the central 41 quotes and 0.0623 with 41 quotes across the original span. Extended coverage reduces mean absolute error in the one-year probability above 1.8F relative to the original grid, but a residual mean error remains. The clean-input controls also retain approximation errors. Tables 15–17 report the uncertainty of the repeated comparisons.

Additional files:

- `src/repeated.py`: nested strike design, paired errors and sampling summaries.
- `run_repeated.py`: reproducible case execution, resumption and numerical exports.
- `build_repeated_report.py`, `build_milestone7_notebook.py`: scientific figures, tables and notebook assembly.
- `results/repeated_protocol.json`, `results/repeated_random_states.json`, `results/repeated_quotes.csv`: declared design and reproducible inputs.
- `results/repeated_cases/`: every attempted case with solver histories and probability weights.
- `results/repeated_validation.json`, `results/repeated_metrics.csv`, `results/repeated_bin_masses.csv`: diagnostics and statistical summaries.
- `results/repeated_pilot.json`, `results/repeated_noise_bound_check.json`: pilot and noise-model checks used in the development reflection.
- `tests/test_repeated.py`: independent moment checks, paired-error calculations, saved-result reconstruction and artifact checks.

All **45 tests** passed. The paper registers now cover **20 figures, 17 tables and 29 equations**, with the new statistical symbols and abbreviations. Reference [16] adds Morris, White and Crowther's peer-reviewed simulation-methodology paper. The development reflection is updated through Notebook 7, including the unsuccessful uncapped noise construction, comparison design and remaining tail errors.

The first six notebooks and both offline interactive companions are byte-for-byte unchanged from Milestone 6. The Figure 4 explanation remains below its figure and caption. The main paper's title page, abstract, contents and requested lists remain part of the final assembly. The next numerical questions concern smoothing selection with separate evaluation, and sensitivity to the supplied forwards; empirical fitting and historical-date animation still require verified data.

### Milestone 8: smoothing selection and supplied-forward sensitivity

Open `08_smoothing_and_forwards.ipynb` and read `research/selection_methodology.md`.

```bash
python build_milestone8_notebook.py
python -m unittest discover -s tests -v
```

The builder verifies and reuses the included results, then regenerates tables, numerical commentary and embedded Figures 21–23. A complete new run can take tens of minutes:

```bash
python run_selection.py --fresh --workers 4
python build_milestone8_notebook.py
```

Use `--workers 1` for sequential execution. Edit `research/selection_methodology_template.md` for lasting prose changes; `python build_milestone8_notebook.py --refresh-narrative` updates the narrative and scientific figures without new fitting. Each saved experiment checks its source/protocol fingerprint and content checksum; forward stresses also check the parent selection case.

The declared rule chooses among three smoothing coefficients using three interlaced folds of noisy interior quotes. Both endpoints remain in training, scores weight actual observation counts, and a single coefficient is selected for all eight maturities. Twenty new realisations per benchmark/pattern give 80 selection experiments. The known density and 960 separate clean prices are used only after full-data refitting. A fixed-coefficient control uses exactly the same observations.

The single-lognormal benchmark selects the baseline in every repetition. The mixture selects the lower candidate, but improved interior pricing does not ensure improved density recovery. With Extended 121 quotes, mean clean-price RMSE decreases from approximately 0.1587 to 0.1174 points while mean full-density error increases from 0.0524 to 0.0630. With Original 81, separate evaluation also exposes worse extrapolation. That finding is retained and explained, rather than used to revise the declared rule after evaluation.

The forward study holds the selected zero-shift coefficient fixed and tests ±0.1% and ±0.5% input changes. Physical tail events remain fixed relative to the known reference forward. The fitted surfaces pass their imposed calendar checks, while incorrect forward inputs can sharply increase price and density errors. A discounted intrinsic-value bound diagnoses observed calls incompatible with the supplied mean; no quote repair is applied.

The complete study contains **1,000 accepted joint fits and 8,000 marginals**, including 720 CV training fits, with no failed or blocked experiment. All **55 tests** passed. The paper registers now cover **23 figures, 21 tables and 33 equations**. Reference [17] adds Cawley and Talbot's peer-reviewed model-selection paper; the Bank of England source remains in use. The development reflection covers selection-target mismatch, unequal fold weighting, fixed-event scoring and incompatible forward inputs, including the post-hoc diagnostic and a corrected test fixture.

Additional files:

- `src/selection.py`, `run_selection.py`: selection and forward-stress design, execution and complete case accounting.
- `build_selection_report.py`, `build_milestone8_notebook.py`: scientific figures, calculated tables, post-hoc range diagnostic and notebook assembly.
- `results/selection_protocol.json`, `results/selection_random_states.json`, `results/selection_quotes.csv`: declared experiment and reproducible observed inputs.
- `results/selection_cases/`: candidate/fold scores, weights, residuals, solver histories and forward-parent links.
- `results/selection_validation.json`, `results/selection_metrics.csv`, `results/selection_range_diagnostic.json`: complete summaries and the explicitly labelled follow-up diagnostic.
- `tests/test_selection.py`: independent weighting, payoff-bound and fixed-coordinate checks, saved-score reconstruction and artifact preservation.
- `research/project_roadmap.md`: two planned empirical stages, final-paper requirements and unresolved data gate.

All seven earlier notebooks and both offline 3D companions remain byte-for-byte unchanged from Milestone 7, including the Figure 4 explanation below the figure and caption. The final paper still includes the requested title page, abstract, contents, numbered lists, abbreviations and symbols. Historical-date animation requires verified observations across dates.

The ZIP is cumulative. Extract it into a new folder if you have made additional local edits; keep those files backed up before merging versions. Candidate market-data files remain private pending redistribution-rights checks.

### Notebook 9 preparation: documented inputs and matched-pair forwards

All **66 project tests** passed for this release, including the new timing, pairing, forward-inference and saved-fit checks. The previous Figure 4 placement remains covered by its existing test.

Open `09_empirical_preparation.ipynb`, read `research/empirical_methodology.md`, and use `research/empirical_input_guide.md` for the input format.

```bash
python build_milestone9_notebook.py
python -m unittest discover -s tests -v
```

The builder regenerates a clearly labelled synthetic bundle, executes nine training fits and one selected refit, and updates the narrative and embedded Figures 24–25. The fixture contains 282 rows, three horizons and unequal pair counts. No network access is used by the builder. Its invented dates do not assert actual exchange sessions or listed contracts.

The input workflow checks common observation times, settlement declarations, duplicate quotes, usable prices/sizes, matching discounts and curve availability. Matched call–put intervals must admit a common forward; incompatible intervals are reported without repair. Each validation fold holds out both sides of a strike pair and infers its forward from training pairs only. The fitter keeps the existing joint constraints and reports residuals against both calls' and puts' bid–ask ranges. One fixture put remains about 0.01993 points outside its range, illustrating why parity feasibility and smoothed-price reproduction are separate checks.

At the preparation handoff, the source assessment had obtained no accepted market export. The Cboe EOD sample returned HTTP 403, and another provider's advertised historical sample did not have the required synchronised timing. The original candidate remains unchanged. That preparation-stage dependency was subsequently resolved for a separate exchange-BBO profile by the supplied marking-price files, as described in Part B and the section below.

For an assessed, populated bundle, use a new output path:

```bash
python run_market_calibration.py data/your_reviewed_bundle --output results/your_snapshot_fit.json
```

Additional files:

- `src/empirical.py`, `run_market_calibration.py`: canonical import, auditable exclusions, conditional forwards, training-only selection and joint calibration.
- `run_empirical_preparation.py`, `build_empirical_report.py`, `build_milestone9_notebook.py`: reproducible fixture, scientific figures, tables and executed working notebook.
- `data/templates/empirical_input/`: empty quote, discount and manifest templates that intentionally fail until completed.
- `data/fixtures/empirical/`: explicitly synthetic quotes, discounts, known answers and random-state records.
- `results/empirical_preparation.json`: row audit, all ten fitted surfaces, fold membership, forward intervals, residuals, failure exercises and source/input checksums.
- `results/empirical_preparation_validation.json`, `tests/test_empirical.py`: constraints and independent timing, matching, leakage and reconstruction checks.

The registers now contain **25 figures, 25 tables and 37 equations**, with updated abbreviations and symbols. The development reflection covers unavailable data, forward inference within validation, distinct compatibility checks and the corrected residual-plot range. All eight earlier notebooks and both offline 3D companions remain byte-for-byte unchanged from Milestone 8, including the Figure 4 edit. Historical-date animation and the final paper remain on the roadmap.

### Notebook 9 empirical application: supplied marking-price files

The complete ninth notebook keeps its filename for continuity and has two executed sections: the existing synthetic acceptance exercise and the observed-data application. Run `python build_milestone9_notebook.py` to recompute both, the primary empirical grid, the explicitly post-hoc lower-grid diagnostic, Figures 24–28, Tables 22–30 and the offline empirical explorer. The builder uses only archived data and performs no downloads. The direct empirical runners are `run_marking_calibration.py` and `run_marking_diagnostic.py`.

The three original CSVs and their source-verification record are in `data/raw/marking_prices/`. The primary protocol, row audit, retained pairs, scores, weights, residuals and numerical checks are saved as `results/marking_*.json`. `src/marking.py` is a separate adapter: indicative sizes are not asserted to be market depth, and inferred discounts are not an external curve. The existing `src/empirical.py` profile remains available for exports that meet its original requirements.

Read `research/marking_methodology.md` for Equations (38)–(40), Figures 26–28 and Tables 26–30. The registers now cover **28 figures, 30 tables and 40 equations**. The reflection records the source interpretation, quote-implied carry workaround, training-only estimation, boundary-selected smoothing, remaining put residuals, tail sensitivity and corrected invalid-row reporting. All eight earlier notebooks and two earlier offline explorers remain byte-for-byte preserved, including the Figure 4 edit. The ZIP is cumulative; extract it into a new folder if you have additional local edits.

Verification for this release: **74 tests passed**; the new explorer was checked offline in Chromium, including controls, hover, rotation, zoom and narrow-screen layout. The `tzdata` dependency supplies named timezone rules on systems such as Windows, following the [Python documentation](https://docs.python.org/3/library/zoneinfo.html).

### Notebook 10: empirical validation and dated comparisons

Open `10_empirical_comparison.ipynb`, read `research/comparison_methodology.md` and open `interactive/dated_density_surface.html` directly in a browser.

```bash
python build_milestone10_notebook.py
python -m unittest discover -s tests -v
```

The builder recomputes the new cases, 72 conditional risk extrema, Figures 29–33, Tables 31–36 and the offline companion, then executes and saves the notebook. Its equations continue at (41)–(46). All inputs are archived; no network is required for this calculation. For separate stages, use `run_comparison.py`, `build_comparison_report.py` and `build_comparison_html.py`. Regenerating older milestones is not needed and would replace their saved output records.

The criterion minimises discrete density curvature subject to original call and put intervals, nonnegative unit mass, unit normalised mean and continuous within-snapshot calendar ordering. Feasibility is checked first without repairing quotes. The late 120-bin control is blocked; all primary 240-bin cases pass. Sixteen of 18 attempted fit cases are accepted; the other case is an unresolved late validation fold. Independent price checks retain tiny signed numerical residuals. Successful holdouts still contain spread misses, and conditional risk ranges are not confidence intervals.

The comparison retains fixed expiries and adds an explicitly assumed 60-day normalised mixture without extrapolation. A common-contract control re-estimates carry. The explorer steps through the three observed snapshots, with rotation, zoom, hover, linked histogram comparisons and risk ranges. It does not interpolate observation dates or imply an observed 60-day forward.

Important additions:

- `src/comparison.py`, `run_comparison.py`: separate hard-bound estimator, numerical records and paired holdouts.
- `results/comparison_protocol.json`, `results/comparison_summary.json`, `results/comparison_cases/`: choices, checksums, all accepted/unaccepted cases and LP extrema.
- `research/comparison_methodology.md`, `research/development_reflection.md`: referenced findings, setbacks and remaining limits.
- `tests/test_comparison.py`: independent mathematical examples and saved-evidence reconstruction.
- `results/comparison_browser_checks.json`, `results/milestone10_delivery_checks.json`: offline interaction and delivery checks.

All 84 numerical tests pass at this handoff. The shared registers contain 33 figures, 36 tables, 46 equations and 23 references, retaining Bahra's Bank of England paper. The nine prior notebooks and three prior explorers are byte-for-byte unchanged, including the Figure 4 caption/explanation placement. The complete analytical material is ready for final-paper assembly, with the limitations carried forward.
