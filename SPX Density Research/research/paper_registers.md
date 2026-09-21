# Registers for the assembled research paper

The final Word/PDF front matter is assembled in `paper/`. These source registers retain the shared equation, figure, table, abbreviation and symbol definitions. Printed page references are generated from the rendered paper and recorded in `paper/page_map.json`; they are not inferred from notebook positions.

## Final opening pages

1. Title page, including the final research title, Joel Cerraga, date and version.
2. Abstract, completed after the results are finalised.
3. Table of contents.
4. List of figures.
5. List of tables.
6. List of equations.
7. List of abbreviations.
8. List of mathematical symbols, with units where applicable.

The main paper brings the milestones into a single argument: research question, mathematical foundation, data assessment, estimation method, validation, results, development challenges and lessons learned, limitations and conclusion. References and reproducibility appendices will follow. Milestone documents are development material, not a prescribed chapter structure.

## Development and reflection section

The dedicated section **Development challenges, corrective actions and lessons learned** is drafted in [development_reflection.md](development_reflection.md). It covers all ten notebooks, including the empirical comparisons, conditional tail ranges and unresolved numerical fold, linking each documented difficulty to the approaches tested, supporting calculations, checked outcome and remaining limitation. It includes unsuccessful approaches where they explain the eventual decision and distinguishes intentional stress tests from unexpected failures. The maintained record includes final assembly; its substantive findings are incorporated into Chapter 9 of the paper. It uses the existing equation, figure, table and reference numbers. The [working roadmap](project_roadmap.md) records completion of the analytical notebooks separately from final-paper assembly.

## List of figures

| Number | Short title | Current source |
|---|---|---|
| 1 | Synthetic European call prices | `methodology.md` |
| 2 | Known and recovered synthetic density | `methodology.md` |
| 3 | Strike-spacing convergence | `methodology.md` |
| 4 | Sensitivity to independent quote errors | `methodology.md` |
| 5 | Candidate quote coverage by expiry and root | `market_data_methodology.md` |
| 6 | Candidate coverage under spread thresholds | `market_data_methodology.md` |
| 7 | Constrained synthetic call-price fit and residuals | `constrained_methodology.md` |
| 8 | Constrained density versus raw differentiation | `constrained_methodology.md` |
| 9 | Smoothing-penalty sensitivity | `constrained_methodology.md` |
| 10 | Synthetic multi-maturity density surface; interactive companion | `surface_methodology.md` |
| 11 | Known and fitted density slices across horizons | `surface_methodology.md` |
| 12 | Calendar gap before and after joint fitting | `joint_methodology.md` |
| 13 | Joint density comparison and remaining tail differences | `joint_methodology.md` |
| 14 | Joint synthetic maturity surface; interactive comparison | `joint_methodology.md` |
| 15 | Density sensitivity across support, resolution and smoothing choices | `robustness_methodology.md` |
| 16 | Price and full-density error across sensitivity settings | `robustness_methodology.md` |
| 17 | Tail-probability errors under alternative fitting choices | `robustness_methodology.md` |
| 18 | Nested strike patterns and tail-threshold coverage | `repeated_methodology.md` |
| 19 | Repeated recovery errors and Monte Carlo precision | `repeated_methodology.md` |
| 20 | Repeated upper-tail errors and clean-input controls | `repeated_methodology.md` |
| 21 | Noisy held-out price scores for smoothing selection | `selection_methodology.md` |
| 22 | Selected and fixed smoothing on separate recovery measures | `selection_methodology.md` |
| 23 | Density, price and fixed-event tail sensitivity to supplied forwards | `selection_methodology.md` |
| 24 | Matched-pair forward intervals and an intentionally incompatible quote | `empirical_methodology.md` |
| 25 | Synthetic input-fixture density recovery and bid–ask residuals | `empirical_methodology.md` |
| 26 | Observed market prices and complete call–put spread residuals | `marking_methodology.md` |
| 27 | Empirical density sensitivity on full support and central detail | `marking_methodology.md` |
| 28 | First empirical maturity surface and offline explorer | `marking_methodology.md` |
| 29 | Original call/put spread residuals before and after hard-bound fitting | `comparison_methodology.md` |
| 30 | Fixed-expiry comparisons across the three observed snapshots | `comparison_methodology.md` |
| 31 | Assumed common-60-day densities and common-contract control | `comparison_methodology.md` |
| 32 | Chosen tail estimates and conditional feasible probability ranges | `comparison_methodology.md` |
| 33 | Dated density surfaces on shared scales; offline date-aware companion | `comparison_methodology.md` |

## List of tables

| Number | Short title | Current source |
|---|---|---|
| 1 | Measured baseline validation | `methodology.md` |
| 2 | Data-source assessment and access status | `market_data_methodology.md` |
| 3 | Candidate-snapshot audit results | `market_data_methodology.md` |
| 4 | Required market-data fields | `market_data_methodology.md` |
| 5 | Baseline constrained-fit diagnostics | `constrained_methodology.md` |
| 6 | Smoothing sensitivity | `constrained_methodology.md` |
| 7 | Synthetic validation by expiry horizon | `surface_methodology.md` |
| 8 | Cross-maturity calendar diagnostic | `surface_methodology.md` |
| 9 | Independent and joint consistency and recovery accuracy | `joint_methodology.md` |
| 10 | Joint-fit recovery accuracy by horizon | `joint_methodology.md` |
| 11 | Declared sensitivity settings and comparable smoothing coefficients | `robustness_methodology.md` |
| 12 | Recovery accuracy across two benchmarks and seven settings | `robustness_methodology.md` |
| 13 | Known and fitted tail probabilities and variance at 365 days | `robustness_methodology.md` |
| 14 | Quote patterns, counts and threshold coverage | `repeated_methodology.md` |
| 15 | Mean recovery errors and Monte Carlo standard errors | `repeated_methodology.md` |
| 16 | Clean-input and repeated upper-tail errors | `repeated_methodology.md` |
| 17 | Paired changes in density and absolute tail errors | `repeated_methodology.md` |
| 18 | Smoothing-selection frequencies across repetitions | `selection_methodology.md` |
| 19 | Recovery under selected and fixed smoothing | `selection_methodology.md` |
| 20 | Paired selected-minus-fixed recovery errors | `selection_methodology.md` |
| 21 | Forward sensitivity and incompatible lower-bound quotes | `selection_methodology.md` |
| 22 | Updated source-access assessment for empirical calibration | `empirical_methodology.md` |
| 23 | Synthetic input pairs and conditional forward inference | `empirical_methodology.md` |
| 24 | Separate fixture recovery and in-sample spread diagnostics | `empirical_methodology.md` |
| 25 | Deliberately invalid input cases and observed responses | `empirical_methodology.md` |
| 26 | Supplied marking-price files, dates and assigned roles | `marking_methodology.md` |
| 27 | Quote-implied discount/forward inputs and feasible discount projections | `marking_methodology.md` |
| 28 | Primary empirical coverage and call/put spread residuals | `marking_methodology.md` |
| 29 | Primary and post-hoc smoothing grids and fit diagnostics | `marking_methodology.md` |
| 30 | Conditional empirical tail probabilities and variance sensitivity | `marking_methodology.md` |
| 31 | Dated quote coverage, common strikes and inferred carry | `comparison_methodology.md` |
| 32 | Finite-grid price feasibility and equivalent numerical formulations | `comparison_methodology.md` |
| 33 | Original call/put spread fit and midpoint residual comparisons | `comparison_methodology.md` |
| 34 | Paired held-out price errors and successful-fold coverage | `comparison_methodology.md` |
| 35 | Common-horizon conditional risk summaries and sample sensitivity | `comparison_methodology.md` |
| 36 | Conditional feasible ranges for common-horizon tail events | `comparison_methodology.md` |

These administrative registers are not additional numbered research tables.

## List of equations

| Number | Descriptive name | Current source |
|---|---|---|
| 1 | Discounted expected call payoff | `methodology.md` |
| 2 | First strike derivative of the call price | `methodology.md` |
| 3 | Breeden–Litzenberger density-extraction relationship | `methodology.md` |
| 4 | Centred finite-difference density estimate | `methodology.md` |
| 5 | Bid–ask midpoint | `market_data_methodology.md` |
| 6 | Relative bid–ask spread | `market_data_methodology.md` |
| 7 | Discounted put–call parity | `market_data_methodology.md` |
| 8 | Indicative forward interval from bid–ask quotes | `market_data_methodology.md` |
| 9 | Piecewise-constant probability density | `constrained_methodology.md` |
| 10 | Non-negativity, total-mass and forward constraints | `constrained_methodology.md` |
| 11 | Exact call valuation under interval probabilities | `constrained_methodology.md` |
| 12 | Regularised constrained fitting objective | `constrained_methodology.md` |
| 13 | Forward-normalised call value | `surface_methodology.md` |
| 14 | Cross-maturity consistency at fixed forward moneyness | `surface_methodology.md` |
| 15 | Integrated absolute density error on fitting support | `surface_methodology.md` |
| 16 | Common forward-coordinate density and physical density | `joint_methodology.md` |
| 17 | Joint quadratic programme with calendar constraints | `joint_methodology.md` |
| 18 | Within-bin quadratic calendar gap | `joint_methodology.md` |
| 19 | Interior calendar-gap minimum | `joint_methodology.md` |
| 20 | Lognormal-mixture density and weighted option prices | `robustness_methodology.md` |
| 21 | Grid-scaled discrete density roughness | `robustness_methodology.md` |
| 22 | Equivalent smoothing coefficient across grids | `robustness_methodology.md` |
| 23 | Full-domain density error including omitted tails | `robustness_methodology.md` |
| 24 | Risk-neutral tail probabilities at stated forward thresholds | `robustness_methodology.md` |
| 25 | Normalised terminal-level variance for histograms and mixtures | `robustness_methodology.md` |
| 26 | Paired bounded synthetic quote perturbations | `repeated_methodology.md` |
| 27 | Simulation bias, empirical variance and finite-sample MSE decomposition | `repeated_methodology.md` |
| 28 | Monte Carlo standard error of a mean | `repeated_methodology.md` |
| 29 | Mean paired contrast and its Monte Carlo standard error | `repeated_methodology.md` |
| 30 | Pooled noisy-price validation score and penalty selection | `selection_methodology.md` |
| 31 | Relative perturbation of the supplied forward curve | `selection_methodology.md` |
| 32 | Density evaluation and fixed risk event in reference coordinates | `selection_methodology.md` |
| 33 | Supplied-forward call lower bound and quote shortfall | `selection_methodology.md` |
| 34 | Common bid–ask forward intersection and point convention | `empirical_methodology.md` |
| 35 | Minimum uniform widening of incompatible forward intervals | `empirical_methodology.md` |
| 36 | Smoothing selection with training-only inferred forwards | `empirical_methodology.md` |
| 37 | Fitted option-price distance outside its bid–ask range | `empirical_methodology.md` |
| 38 | Linear put–call parity and bid–ask difference bounds | `marking_methodology.md` |
| 39 | Constrained quote-implied discount and forward estimation | `marking_methodology.md` |
| 40 | Quote-implied continuously compounded rate equivalent | `marking_methodology.md` |
| 41 | Intersection of original call and parity-transformed put intervals | `comparison_methodology.md` |
| 42 | Minimum diagnostic quote widening under the finite density basis | `comparison_methodology.md` |
| 43 | Minimum-curvature density inside original quote restrictions | `comparison_methodology.md` |
| 44 | Conditional feasible lower and upper event probabilities | `comparison_methodology.md` |
| 45 | Assumed interpolation of normalised distributions at a common horizon | `comparison_methodology.md` |
| 46 | Absolute distance between two fitted normalised densities | `comparison_methodology.md` |

## List of abbreviations

| Abbreviation | Meaning |
|---|---|
| AM / PM | Before / after noon; settlement conventions require contract-specific confirmation |
| ACT/365F | Actual elapsed time divided by a fixed 365-day year; UTC seconds are used here |
| API | Application programming interface |
| 3D | Three-dimensional |
| BBO | Best Bid and Offer on the stated exchange; not necessarily consolidated NBBO |
| CT / ET | Chicago / New York civil time, with the date-specific UTC offset |
| EOM | End of month |
| LP | Linear programme |
| OSI | Options Symbology Initiative; encoded contract identifier |
| CSV | Comma-separated values |
| CV | Cross-validation; here an interlaced interior-price selection rule |
| BS | Black–Scholes, used as a component-pricing subscript |
| DOI | Digital object identifier |
| EOD | End of day; a provider product can also contain a separately specified intraday snapshot |
| JSON | JavaScript Object Notation |
| ISO | International Organization for Standardization; ISO datetime notation is used in the input format |
| LN | Lognormal, used as a component-density subscript |
| MCSE | Monte Carlo standard error of an estimated simulation summary |
| MSE | Mean squared error |
| HTML | HyperText Markup Language |
| NBBO | National Best Bid and Offer |
| OSQP | Operator Splitting Quadratic Program; the solver used in Milestone 5 |
| PDF | Probability density function; a `.pdf` document separately denotes Portable Document Format |
| PCG64 | NumPy's 64-bit permuted congruential random-number generator |
| QP | Quadratic programme |
| QDLDL | Named sparse LDL factorisation implementation used by the Clarabel backend |
| RMSE | Root-mean-square error |
| RND | Risk-neutral density |
| SD | Standard deviation |
| SHA-256 | Secure Hash Algorithm with a 256-bit digest |
| SLSQP | Sequential least-squares programming |
| SPX | Cboe S&P 500 Index option identifier; a product symbol rather than an ordinary abbreviation |
| SPXW | SPX option trading-class identifier; kept separate from SPX in the quote audit |
| SVI | Stochastic volatility inspired; the parameterisation in reference [12], not the estimator used here |
| UTC | Coordinated Universal Time |
| WRDS | Wharton Research Data Services |

## List of mathematical symbols

| Symbol | Definition | Units |
|---|---|---|
| $S_0$ | Initial index level | Index points |
| $S_T$, $s$ | Terminal index level, or its possible value | Index points |
| $K$, $K_i$ | Option strike | Index points |
| $T$ | Time from observation to settlement | Years |
| $r$ | Continuously compounded risk-free rate | Per year |
| $q$ | Continuous dividend yield; `dividend` in the code | Per year |
| $\sigma$ | Annualised volatility | Per square-root year |
| $Q$ | Risk-neutral probability measure | Not applicable |
| $f_Q$, $\widehat f_Q$ | Known/theoretical and estimated risk-neutral densities | Inverse index points |
| $C$, $P$ | European call and put prices | Index points |
| $F(T)$ | Forward index level for the horizon | Index points |
| $D(T)$ | Discount factor, $e^{-rT}$ | Dimensionless |
| $T_i$ | The $i$th increasing synthetic expiry horizon | Years |
| $\kappa$ | Forward moneyness, $K/F(T)$; not log-moneyness | Dimensionless |
| $\overline C$ | Call value divided by $D(T)F(T)$ | Dimensionless |
| $\mathbb{E}^{Q}$ | Expectation under the risk-neutral measure | Same as the random quantity averaged |
| $L_1(T)$ | Integrated absolute density error on the fitting support | Dimensionless |
| $h$ | Strike spacing in finite differences | Index points |
| $B_i$, $A_i$ | Bid and ask of option observation $i$ | Index points |
| $M_i$ | Quote midpoint | Index points |
| $R_i$ | Spread divided by midpoint | Dimensionless |
| $a_j$, $b_j$ | Lower and upper terminal-level interval boundaries | Index points |
| $\Delta s_j$, $m_j$ | Interval width and centre | Index points |
| $w_j$, $\mathbf w$ | Probability in interval $j$, and vector of these probabilities | Dimensionless |
| $J$ | Number of terminal-level intervals | Count |
| $N$ | Number of observed or synthetic option prices | Count |
| $A_{ij}$ | Discounted call payoff for strike $i$ under unit uniform mass in interval $j$ | Index points |
| $y_i$ | Noisy synthetic price supplied to the fitter | Index points |
| $g_j$ | Density height in coordinates normalised by the forward | Dimensionless |
| $m$, $M$ | Maturity index and number of jointly fitted maturities | Count |
| $T_m$, $F_m$ | Maturity and its forward in the joint problem | Years; index points |
| $x$ | Terminal level divided by the forward, $s/F_m$ | Dimensionless |
| $u_j$, $\bar u_j$, $\Delta u$ | Common normalised edge, bin centre and equal bin width | Dimensionless |
| $w_{mj}$, $\mathbf w_m$ | Bin probability and probability vector at maturity $m$ | Dimensionless |
| $\widehat g_m(x)$ | Fitted density of the normalised terminal level | Dimensionless |
| $B_j(\kappa)$, $\mathbf B(\kappa)$ | Uniform-bin normalised call payoff and its row vector | Dimensionless |
| $\ell_m(\mathbf w_m)$ | Per-maturity objective from Equation (12) | Dimensionless |
| $\mathcal K_m$ | Calendar-constraint locations for adjacent pair $m,m+1$ | Set of dimensionless ratios |
| $\delta_{mj}$ | Later minus earlier probability in bin $j$ | Dimensionless |
| $\Delta_m(\kappa)$ | Later minus earlier normalised call value | Dimensionless |
| $z$, $z^*_{mj}$ | Offset from the left bin edge; eligible interior-minimum offset | Dimensionless |
| $X_T$ | Normalised terminal random level, $S_T/F(T)$ | Dimensionless |
| $L$, $\ell$ | Number of mixture components and component index | Count |
| $\pi_\ell$ | Probability weight of mixture component $\ell$ | Dimensionless |
| $\sigma_\ell$ | Annualised volatility of mixture component $\ell$ | Per square-root year |
| $g_{\mathrm{mix}}$, $g_{\mathrm{LN}}$ | Mixture and component densities of the normalised terminal level | Dimensionless |
| $C_{\mathrm{mix}}$, $C_{\mathrm{BS}}$ | Mixture call price and component Black–Scholes call price | Index points |
| $R_{\Delta u}(\mathbf g)$ | Discrete roughness of the normalised density-height sequence | Dimensionless |
| $\alpha$, $\alpha_0$ | Grid-comparable roughness coefficient and its baseline | Dimensionless |
| $L_1^{\mathrm{full}}(T)$ | Density absolute error across the entire positive domain | Dimensionless |
| $p^-_{0.8}$, $p^+_{1.2}$, $p^+_{1.8}$ | Lower- and upper-tail probabilities relative to the forward | Dimensionless; optionally displayed as percentages |
| $\widehat\mu$ | Fitted mean of the normalised terminal level | Dimensionless |
| $\widehat V$, $V_{\mathrm{known}}$ | Fitted and known variance of the normalised terminal level | Dimensionless |
| $\nu$, $n_{\mathrm{sim}}$ | Simulation repetition index and number of repetitions | Count |
| $a$, $\eta_{mi}(a)$ | Declared error half-width limit and its price-dependent bound | Index points |
| $C_{mi}$, $y_{\nu mi}(a)$ | Clean and perturbed call value at horizon $m$ and master strike $i$ | Index points |
| $U_{\nu mi}$, $\mathcal U[-1,1]$ | Shared random draw and its uniform distribution | Dimensionless |
| $\theta$, $\widehat\theta_\nu$, $\overline\theta$ | Known target, repetition-level estimate and mean estimate | Units of the stated target; dimensionless for probability |
| $\widehat{\operatorname{Bias}}$, $s_\theta$ | Estimated bias and empirical SD of repeated estimates | Same as $\theta$ |
| $z_\nu$, $\overline z$, $s_z$ | Repetition-level performance scalar, its mean and sample SD | Units of the selected performance measure |
| $\Delta_\nu$, $\overline\Delta$ | Paired difference and its mean across repetitions | Same as $z_\nu$ |
| $\operatorname{MCSE}$ | Standard error due to a finite simulation repetition count | Units of the estimated summary |
| $\lambda$ | Smoothing penalty coefficient in the specified scaled objective | Dimensionless |
| $\Lambda$, $\widehat\lambda$ | Declared candidate set and selected smoothing coefficient | Set of dimensionless values; dimensionless |
| $k$, $\mathcal H_k$ | Validation-fold index and its held-out quote positions | Count; index set |
| $\widehat C_{m,\lambda}^{(-k)}$ | Call-price fit trained without fold $k$ at maturity $m$ | Index points |
| $\operatorname{CV}(\lambda)$ | Pooled mean squared noisy-price residual after forward scaling | Dimensionless |
| $\varepsilon$ | Relative supplied-forward error in the stress experiment | Dimensionless; optionally displayed as a percentage |
| $\widetilde F_m^{(\varepsilon)}$ | Forward supplied to the stressed fit | Index points |
| $\widehat g_m^{(\varepsilon),\mathrm{ref}}$ | Stressed fitted density expressed using the fixed reference forward | Dimensionless |
| $\widehat p_{1.8,m}^{(\varepsilon)}$ | Stressed fitted probability above the fixed physical level $1.8F_m$ | Dimensionless |
| $D_m$ | Discount factor at maturity $T_m$ | Dimensionless |
| $\ell^F_{mi}$, $u^F_{mi}$ | Lower and upper conditional forward bounds from matched pair $i$ | Index points |
| $\underline F_m$, $\overline F_m$ | Largest pair lower bound and smallest pair upper bound | Index points |
| $\widehat F_m$, $\widehat F_m^{(-k)}$ | Declared forward point from all pairs or fold-$k$ training pairs only | Index points |
| $s_m^*$ | Minimum common widening of forward intervals needed for intersection; diagnostic only | Index points |
| $\mathcal H_{km}$ | Pair positions held out in fold $k$ at maturity $m$ | Index set |
| $C^{\mathrm{mid}}_{mi}$ | Observed or fixture call midpoint used for fitting/selection | Index points |
| $\operatorname{CV}_F(\lambda)$ | Pooled call-price selection loss using training-only inferred forwards | Dimensionless |
| $o$, $\widehat V_{mi,o}$ | Option type (call/put) and corresponding fitted price | Type label; index points |
| $B_{mi,o}$, $A_{mi,o}$ | Matched option's bid and ask | Index points |
| $d^{\mathrm{spread}}_{mi,o}$ | Fitted-price distance outside the option's bid–ask range | Index points |
| $L_{mi}^{(\varepsilon)}$, $v_{mi}^{(\varepsilon)}$ | Supplied-forward call lower bound and positive observed-price shortfall | Index points |
| $\mathbf 1_{[a,b)}$ | Indicator of the half-open interval | Dimensionless |
| $(x)_+$ | Positive part, $\max(x,0)$ | Same as $x$ |
| $\widehat{\phantom f}$ | Estimated quantity | Same as the quantity |
| $\partial$ | Partial differentiation | Determined by the variables |
| $O(h^2)$ | Second-order truncation-error notation | Order statement |
| § / §§ | Section / sections in a cited source; not a mathematical variable | Not applicable |
| $H_m$, $\widehat H_m$ | Discounted forward, $D_mF_m$, and its quote-implied estimate | Index points |
| $\widehat D_m$, $\widehat r_m$ | Quote-implied discount factor and equivalent continuously compounded rate | Dimensionless; per year |
| $b^-_{mi}$, $b^+_{mi}$ | Opposite-side bid–ask bounds on the call-minus-put difference | Index points |
| $y_{mi}$ | Observed call-midpoint minus put-midpoint difference | Index points |
| $K_{0m}$ | Median training strike, used to centre and scale the carry regression | Index points |
| $\beta_0$, $\beta_1$ | Scaled parity intercept $(H-DK_0)/K_0$ and discount factor $D$ | Dimensionless |
| $\varepsilon_{\mathrm{carry}}$ | Positive lower bound for scaled carry inputs in Equation (39), $10^{-8}$ | Dimensionless |
| $N_m$ | Retained call–put pair count used in a full-sample or training-only carry fit | Count |

| $K_{mi}$ | Strike of matched pair $i$ at maturity $m$ | Index points |
| $\ell^C_{mi}$, $u^C_{mi}$ | Intersection bounds from original call and parity-transformed put quotes | Index points |
| $W$ | Matrix of probability masses over all jointly fitted maturities | Dimensionless |
| $\mathcal P_J$, $\mathcal F_J$ | Finite-bin probability/calendar family, and its original-spread-feasible subset | Sets of mass matrices |
| $\delta_J^*$ | Minimum common quote widening on the stated density grid; diagnostic only | Index points |
| $\mathcal R_J(W)$ | Discrete density-curvature criterion used without a price-error tradeoff | Dimensionless |
| $\mathbf a$ | Exact bin-event fractions, including time weights where applicable | Dimensionless |
| $\operatorname{vec}(W)$ | Mass matrix flattened in maturity-major order | Dimensionless |
| $\underline p_J$, $\overline p_J$ | Conditional minimum/maximum event probability in the finite feasible family | Dimensionless; optionally percentages |
| $T_a$, $T_b$, $T_*$ | Adjacent interpolation horizons and target horizon; all in the same unit | Elapsed days in Notebook 10 |
| $\omega_*$ | Linear common-horizon time-mixture weight | Dimensionless |
| $\mathbf w_*$ | Assumed common-horizon mixture of normalised bin masses | Dimensionless |
| $d_1(\widehat g^{(a)},\widehat g^{(b)})$ | Integrated absolute difference between two fitted normalised densities | Dimensionless |

The ask $A_i$ and payoff-matrix entry $A_{ij}$ are distinct objects and must be defined locally. Likewise, $B_i$ denotes an observed bid, whereas $B_j(\kappa)$ denotes a model payoff; $M_i$ denotes a midpoint, whereas $M$ counts maturities. The event coefficient vector $\mathbf a$ differs from the scalar synthetic quote-error amplitude $a$; $\mathcal R_J$ is a curvature criterion, whereas $R_i$ is a relative spread. References use one shared numerical register in `references.md`. Captions remain below figures, and the explanation of Figure 4 remains after its caption in `01_synthetic_density.ipynb`.
