# Project reference register

Reference numbers are shared across all milestones. Theoretical claims use research papers and academic textbooks; Cboe sources document the actual data and contract rules. Original sources not consulted in full are identified explicitly below.

[1] B. Bahra (1997), “Implied risk-neutral probability density functions from option prices: theory and application,” Bank of England, Working Paper No. 66. Sections 2.1–2.2 and Mathematical appendix; §§3.5–3.6 additionally consulted for the mixture benchmark in Milestone 6. [Full paper](https://www.bankofengland.co.uk/-/media/boe/files/working-paper/1997/implied-risk-neutral-probability-density-functions-from-option-prices.pdf).

[2] Cboe, “SPX delayed quotes.” Retrieved 19 September 2026. [Source page](https://www.cboe.com/delayed_quotes/spx/quote_table). Primary data source; not a research paper.

[3] Cboe DataShop, “Option Quotes.” Accessed 19 September 2026. [Product documentation](https://datashop.cboe.com/option-quote-intervals).

[4] Cboe DataShop, “Option Quotes Specification,” v1.1, pp. 1–2. [File specification](https://datashop.cboe.com/documents/Option_Quotes_Layout.pdf).

[5] Cboe, “S&P 500 Index Options Product Specifications.” Accessed 19 September 2026 and rechecked 21 September 2026 for the empirical contracts. [Contract specifications](https://www.cboe.com/tradable-products/sp-500/spx-options/spx-specifications).

[6] D. T. Breeden and R. H. Litzenberger (1978), “Prices of State-Contingent Claims Implicit in Option Prices,” *The Journal of Business*, vol. 51, no. 4, pp. 621–651. [doi:10.1086/260618](https://doi.org/10.1086/260618). Original attribution; the derivation was consulted through Bahra [1] and Aït-Sahalia and Lo [10].

[7] T. A. Driscoll and R. J. Braun, *Fundamentals of Numerical Computation*, author-maintained online textbook, §§5.4–5.5. [Finite differences, especially Equation (5.4.9)](https://fncbook.com/finitediffs/); [Convergence and roundoff](https://fncbook.com/fd-converge/). Accessed 19 September 2026.

[8] F. Black and M. Scholes (1973), “The Pricing of Options and Corporate Liabilities,” *Journal of Political Economy*, vol. 81, no. 3, pp. 637–654. [doi:10.1086/260062](https://doi.org/10.1086/260062). Publisher abstract and metadata consulted; the lognormal implementation is supported by [1] and [10].

[9] Y. Aït-Sahalia and J. Duarte (2003), “Nonparametric option pricing under shape restrictions,” *Journal of Econometrics*, vol. 116, nos. 1–2, pp. 9–47. Section 2. [doi:10.1016/S0304-4076(03)00102-7](https://doi.org/10.1016/S0304-4076(03)00102-7); [author-hosted paper](https://www.princeton.edu/~yacine/cnvx.pdf).

[10] Y. Aït-Sahalia and A. W. Lo (1998), “Nonparametric Estimation of State-Price Densities Implicit in Financial Asset Prices,” *The Journal of Finance*, vol. 53, no. 2, pp. 499–547. Sections I and III.A, especially Equations (16)–(17). [Author-hosted paper](https://www.princeton.edu/~yacine/aslo.pdf).

[11] S. Boyd and L. Vandenberghe (2004), *Convex Optimization*. Cambridge University Press, §§4.4 and 6.3, especially pp. 152–153 and 305–308. [Author-hosted book](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf). The quadratic-programme formulation and smoothing-regularisation discussion were consulted directly.

[12] J. Gatheral and A. Jacquier, “Arbitrage-free SVI volatility surfaces,” *Quantitative Finance*, vol. 14, no. 1, pp. 59–71; first published online 2013. [doi:10.1080/14697688.2013.819986](https://doi.org/10.1080/14697688.2013.819986). Journal metadata checked through Crossref. The consulted text is the [author preprint, arXiv:1204.0646v4](https://arxiv.org/abs/1204.0646v4), §2, particularly §2.1 and Lemma 2.1. Accessed 20 September 2026. Their SVI estimator is not implemented here.

[13] B. Stellato, G. Banjac, P. Goulart, A. Bemporad and S. Boyd (2020), “OSQP: An Operator Splitting Solver for Quadratic Programs,” *Mathematical Programming Computation*, vol. 12, no. 4, pp. 637–672. [doi:10.1007/s12532-020-00179-2](https://doi.org/10.1007/s12532-020-00179-2). Metadata checked on the [author publication page](https://web.stanford.edu/~boyd/papers/osqp.html). Consulted [author preprint, arXiv:1711.08013v4](https://arxiv.org/abs/1711.08013v4), §§1.1, 3.4 and 4, for the formulation, stopping criteria and optional polishing. Accessed 20 September 2026. The code uses OSQP 1.1.3; current interface details are documented separately below.

[14] A. M. Malz (2014), “A Simple and Reliable Way to Compute Option-Based Risk-Neutral Distributions,” Federal Reserve Bank of New York, Staff Report No. 677, June. [Publication page](https://www.newyorkfed.org/research/staff_reports/sr677.html); [full paper](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr677.pdf). Sections 2.3 and 3.2 consulted directly on 20 September 2026 for extrapolation and threshold-based tail summaries. This is a central-bank research paper, not a peer-reviewed journal article. Its spline estimator is not implemented in this project.

[15] P. J. Goulart and Y. Chen (2024), “Clarabel: An interior-point solver for conic programs with quadratic objectives,” research preprint, arXiv:2405.12762v1, 21 May. [Paper record](https://arxiv.org/abs/2405.12762v1); [full paper](https://arxiv.org/pdf/2405.12762). Sections 1 and 2.6 consulted directly on 20 September 2026 for the quadratic/conic formulation and stopping criteria. This is a research preprint; no journal-publication claim is made.

[16] T. P. Morris, I. R. White and M. J. Crowther (2019), “Using simulation studies to evaluate statistical methods,” *Statistics in Medicine*, vol. 38, no. 11, pp. 2074–2102. [doi:10.1002/sim.8086](https://doi.org/10.1002/sim.8086); [open full journal article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/). Sections 3, 4.1 and 5.1–5.4 consulted directly on 21 September 2026 for experiment design, reproducible random streams, missing simulation results and Monte Carlo standard errors. This source supports the simulation methodology; its biomedical application examples are not used as financial models.

[17] G. C. Cawley and N. L. C. Talbot (2010), “On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation,” *Journal of Machine Learning Research*, vol. 11, pp. 2079–2107. [Journal publication page](https://jmlr.org/papers/v11/cawley10a.html); [open full article](https://jmlr.org/papers/volume11/cawley10a/cawley10a.pdf). Sections 2.1 and 5.1 consulted directly on 21 September 2026. This peer-reviewed paper supports treating model selection as part of the procedure under evaluation; its kernel-classification estimators are not implemented here.

[18] Cboe DataShop, “Option EOD Summary” and “Option EOD Summary Specification,” v1.1, pp. 1–2. [Product page](https://datashop.cboe.com/option-eod-summary); [file layout](https://datashop.cboe.com/documents/Option_EOD_Summary_Layout.pdf). Accessed 21 September 2026. Primary operational documentation, including snapshot fields and the early-close exception. The advertised sample download returned HTTP 403; no sample contents were consulted.

[19] HistoricalData.net, “Historical Options Data,” provider's dataset and field documentation. [Primary documentation](https://historicaldata.net/options.html). Accessed 21 September 2026. Used only to assess the advertised 2022 sample's unsynchronised quote convention and lack of quote timestamps for that period. The sample was not downloaded. This vendor page is not scholarly evidence for density estimation.

[20] Wharton Research Data Services, “OptionMetrics,” institutional data-vendor description. [WRDS product documentation](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/optionmetrics/). Accessed 21 September 2026. Establishes a possible institutional data route and described coverage, not access rights, the schema of an unseen export or verified observations in this project.

[21] Cboe, “Proprietary Index Marking Prices.” Accessed 21 September 2026. [Primary documentation and downloads](https://www.cboe.com/markets/us/options/market-statistics/product-data/proprietary-index-marking-prices). Operational evidence for the two price families and snapshot labels. Three supplied CSVs were independently matched to the advertised downloads; the archived verification records retain hashes and HTTP results. This provider page supplies no density-estimation theory.

[22] Cboe, “Hours & Holidays: U.S. Options,” 2026 schedule. Accessed 21 September 2026. [Exchange session schedule](https://www.cboe.com/about/hours/us-options/). Read with the SPX/SPXW specifications [5] to check the three selected expiry dates. New York civil-time conversion uses the named timezone, including the November daylight-saving transition.

[23] S. N. Cohen, C. Reisinger and S. Wang (2020), “Detecting and Repairing Arbitrage in Traded Option Prices,” *Applied Mathematical Finance*, vol. 27, no. 5, pp. 345–373; first published online 8 February 2021. [doi:10.1080/1350486X.2020.1846573](https://doi.org/10.1080/1350486X.2020.1846573). Journal metadata checked through Crossref; the consulted text is the [author preprint, arXiv:2008.09454v1](https://arxiv.org/html/2008.09454v1), §§2.1 and 3.2, accessed 21 September 2026. The publisher full-text page was unavailable. Their soft-bound price-repair LP is not the hard-bound finite-density estimator used here.

## Relationship-to-source guide

| Relationship or decision | Supporting source and scope |
|---|---|
| Equations (1)–(3): payoff valuation and density extraction | Bahra [1], §2.1; original attribution to Breeden–Litzenberger [6] |
| Lognormal benchmark and dividend adjustment | Bahra [1], §2.2; Black–Scholes [8] for original no-arbitrage framing; Aït-Sahalia–Lo [10], Equation (16) for carry |
| Equation (4), truncation error and cancellation | Driscoll–Braun [7], §§5.4–5.5 |
| Equations (5)–(6) | Arithmetic definitions chosen for this audit; not new theoretical results |
| Equation (7): parity | Aït-Sahalia–Lo [10], §III.A, Equation (17) |
| Equation (8): forward interval | Our endpoint rearrangement of Equation (7); not claimed as a quoted equation from [10] |
| Planned monotone, convex call fit | Aït-Sahalia–Duarte [9], §2; their estimator has not yet been implemented |
| Provider timestamps and contract conventions | Cboe [2]–[5]; specifications do not fill missing fields in a different payload |
| Figures, measured errors, row counts, thresholds | This project’s calculations and explicit research choices; no external endorsement implied |
| Equations (9)–(11): interval representation, constraints and prices | Project discretisation of risk-neutral valuation and the mean–forward identity in Bahra [1]; not copied formulae |
| Equation (12): constrained smoothing objective | Project-specific quadratic programme motivated by Boyd–Vandenberghe [11], §§4.4 and 6.3 |
| Equation (13): forward-normalised call value | Project rearrangement of Equation (1), with the normalisation underlying Gatheral–Jacquier [12], §2.1; discounting retained explicitly |
| Equation (14): cross-maturity consistency | Gatheral–Jacquier [12], §2.1 martingale/convexity argument, under the stated deterministic-carry and proportional-dividend assumptions |
| Equation (15): density error; calendar grid and tolerance | Project definitions and numerical evaluation choices, not claims of a new estimator |
| Equation (16): common forward-coordinate density | Project change of variables in Equations (9), (13); risk-neutral interpretation from Bahra [1] |
| Equation (17): jointly constrained objective | Project extension of Equation (12), using Gatheral–Jacquier [12] for calendar ordering and Boyd–Vandenberghe [11] for the quadratic-programme framework |
| Equations (18)–(19): quadratic gap and interior minimum | Project derivation from the uniform-bin payoff; not formulae quoted from the SVI paper |
| OSQP solution, residual-based stopping and optional polishing | Stellato et al. [13], §§1.1, 3.4, 4; application-specific tolerances are project choices |
| Equation (20): mixture density and option valuation | Bahra [1], §§3.5–3.6 and Mathematical appendix; this project's component means, volatilities and weights are declared synthetic choices |
| Equation (21): curvature-scaled discrete roughness | Driscoll–Braun [7], §5.4.2, Equation (5.4.9), supplies the second-derivative stencil; the penalty functional is a project definition |
| Equation (22): conversion of the smoothing coefficient across grids | Project algebra equating the penalties in Equations (12), (21); regularisation framework from Boyd–Vandenberghe [11] |
| Equation (23): full-domain density error | Project extension of Equation (15); outside-support probability is included because the fitted density is zero there |
| Equation (24): threshold probabilities and extrapolation dependence | Project thresholds in forward coordinates; Malz [14], §§2.3, 3.2 motivates explicit coverage and tail analysis |
| Equation (25): histogram and mixture variance | Direct uniform-bin integration and lognormal component moments under Equation (20); not an annualised-volatility estimate |
| Explicit residual variables and the Clarabel backend | Algebraically equivalent expression of Equation (12); Goulart–Chen [15], §§1, 2.6 for the solver class and stopping criteria |
| Equation (26): bounded synthetic quote errors | Project-defined error model; its mean, variance and positivity bound follow directly from uniform-distribution moments; not a calibrated microstructure relationship |
| Equation (27): simulation bias, empirical SD and root MSE | Standard sample summaries as discussed by Morris–White–Crowther [16], §5.2; the finite-sample decomposition is direct algebra with the stated variance denominator |
| Equation (28): Monte Carlo standard error of a mean | Morris–White–Crowther [16], §5.2; uncertainty in simulation performance, not a confidence interval for a market density |
| Equation (29): uncertainty of a paired contrast | Standard mean-SE formula applied to within-repetition differences; matched simulation conditions discussed in [16], §5.4 |
| Nested strike patterns, clean controls and fixed repetition count | Declared project design choices; [14] supports discussion of threshold placement and extrapolation, not the numerical results |
| Equation (30): pooled held-out price score and finite-grid selection | Project-specific interlaced-fold rule; Cawley–Talbot [17], §§2.1, 5.1 supports separating selection and performance evaluation |
| Equation (31): supplied-forward perturbation | Declared synthetic stress levels; no estimated market-error distribution is claimed |
| Equation (32): unchanged physical risk event under forward stress | Direct change of variables in Equation (16), with the physical threshold fixed at the known reference forward |
| Equation (33): call lower bound and observed-price shortfall | Project application of convexity to discounted expected-payoff valuation in Bahra [1], Equation (1); the diagnostic is not a copied estimator |
| Selected-versus-fixed and nonzero-versus-zero forward comparisons | Paired project experiments; simulation-summary conventions from Morris–White–Crowther [16] |
| Equation (34): common bid–ask forward interval and point convention | Project intersection of Equation (8); parity foundation in Aït-Sahalia–Lo [10], §III.A. The midpoint is a declared choice, not a statistical estimator claimed from that paper |
| Equation (35): minimum uniform interval widening | Project algebra from intersection of widened intervals; diagnostic only, with no quote repair |
| Equation (36): selection with training-only inferred forwards | Project extension of Equation (30); Cawley–Talbot [17] supports separation of selection and evaluation, not this particular fold construction |
| Equation (37): distance outside a bid–ask interval | Project diagnostic; call valuation and parity use Equations (11), (7) |
| Provider field mapping and current source-access assessment | Primary operational records [18]–[20]; they do not supply missing metadata in the original candidate or establish scientific validity of the fitted model |
| ACT/365F horizon, curve-age limit, source-review record and synthetic input failures | Explicit implementation/research choices, not externally endorsed sufficiency criteria |
| Equation (38): linear parity and opposite-side bounds | Project rearrangement of parity in Aït-Sahalia–Lo [10]; provider price meanings from [21] |
| Equation (39): simultaneous quote-implied discount and forward | Project constrained least-squares convention, using the convex-QP framework in Boyd–Vandenberghe [11]; feasible LP projections are not confidence intervals |
| Equation (40): implied constant-rate equivalent | Algebraic inverse of D = exp(−rT), not an independently observed rate or yield curve |
| Training-only discount and forward, lower-grid diagnostic | Project extension of Equation (36); Cawley–Talbot [17] motivates separating selection and evaluation; subsequent grid remains post-hoc |
| Actual exchange-BBO profile and reviewed 2026 sessions | Primary operational sources [5, 21–22], archived CSVs and recorded comparisons; size availability is not inferred from price validity |
| Equation (41): joint call/put spread intersection | Project endpoint rearrangement of parity in Aït-Sahalia–Lo [10]; bid–ask-aware restrictions discussed by Cohen–Reisinger–Wang [23] |
| Equation (42): conditional density-grid compatibility | Project LP with a diagnostic uniform price widening; convex-programme framework from Boyd–Vandenberghe [11]. It is not the model-independent repair procedure of [23] |
| Equation (43): minimum curvature inside original spreads | Project criterion using the finite-difference stencil in Driscoll–Braun [7] and smoothing framework in Boyd–Vandenberghe [11]; no smoothing parameter or changed quotes |
| Equation (44): conditional feasible tail ranges | Project linear optimisation of exact bin-event fractions over the declared feasible set; LP framework in [11], tail/extrapolation motivation in Malz [14]; not confidence intervals |
| Equation (45): common-horizon normalised mixture | Explicit project interpolation assumption; preservation of mass, mean and ordered call values follows from linearity of the valuation map in Equations (11), (13) |
| Equation (46): distance between two fitted normalised densities | Direct binwise integration; a descriptive distance rather than the truth-based recovery error in Equation (15) |
| Numerical row scaling, paired validation coverage and common contracts | Documented project implementation/design choices; strict solver criteria from Goulart–Chen [15] and evaluation caution from Cawley–Talbot [17] |

## Software documentation (not theoretical evidence)

The standalone companion uses Plotly.js 3.1.0 under the MIT licence, included with its attribution. Its implementation follows the primary [surface-plot documentation](https://plotly.com/javascript/3d-surface-plots/) and [function reference](https://plotly.com/javascript/plotlyjs-function-reference/), accessed 20 September 2026. These documentation links describe the software, not evidence for the financial relationships.

The joint fitter uses OSQP 1.1.3. Its interface, status fields and tolerances were checked against the official [Python interface](https://osqp.org/docs/interfaces/python.html) and [solver settings](https://osqp.org/docs/interfaces/solver_settings.html), accessed 20 September 2026. These support implementation details; reference [13] supplies the scholarly source.

Milestones 6–10 use Clarabel 0.11.1. Its problem interface and tolerance fields were checked in the official [Python guide](https://clarabel.org/stable/python/getting_started_py/) and [solver settings](https://clarabel.org/stable/api_settings/), accessed 20 September 2026. Reference [15] supplies the research source.

Milestones 7–8 use NumPy's `SeedSequence` with a child key for each repetition and the PCG64 generator. Notebook 8 adds its milestone identifier to the seed entropy to obtain separate streams. The construction was checked against the official [parallel random-number documentation](https://numpy.org/doc/stable/reference/random/parallel.html), accessed 21 September 2026. Saved generator states support exact input replay; reference [16] supplies the scholarly simulation-design context.

The empirical adapter uses Python's `zoneinfo` for named civil-time conversion. The official [Python timezone documentation](https://docs.python.org/3/library/zoneinfo.html), accessed 21 September 2026, documents the `tzdata` fallback used for cross-platform support, including Windows. This is implementation documentation, not a financial assumption.

## Writing convention

Introduce substantive borrowed ideas through the author and work—for example, “As Bahra (1997) explains in his Bank of England working paper [1]…”—then explain how the idea applies to this analysis. Use paraphrases, not invented direct quotations. Keep numerical citations for precise cross-referencing. Prefer peer-reviewed articles, research papers and academic books for theory, and primary provider documents for operational facts. Cite the consulted account when the original paper was not available in full.
