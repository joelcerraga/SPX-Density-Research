# Selecting smoothing and testing the supplied forward

## 1. Research question and scope

The previous notebooks held the smoothing coefficient fixed while measuring recovery error. This notebook asks whether selecting that coefficient from noisy observed prices improves subsequent recovery, and how the fitted result changes when the supplied forward is wrong. These are separate questions: the first changes the selection rule; the second perturbs a required input while holding the selected coefficient fixed.

As Cawley and Talbot explain in *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*, choosing a model and assessing its performance are distinct parts of an evaluation procedure [17, §§2.1, 5.1]. Here, selection uses noisy quotes alone. Known synthetic prices at separate strikes, densities and tail probabilities are reserved for evaluation. The selector is rerun in every repetition. This is a fixed-design simulation, not a historical market forecast or a claim that cross-validation identifies the true density.

The two benchmark families, eight horizons, 120 density bins and interval-level calendar checks remain those of Notebooks 6–7. The experiment uses Original 81 and Extended 121 quote patterns, the bounded errors in Equation (26) with $a=0.5$ index points, and 20 new random realisations per benchmark/pattern. Within each repetition, both patterns and benchmark families share the master random draws. New child streams distinguish this study from Notebook 7. A runtime/feasibility pilot was completed before the full batch; the fixed repetition count was retained, and no early stopping rule depends on favourable results.

## 2. Selecting one coefficient for all maturities

As Boyd and Vandenberghe discuss in *Convex Optimization*, a regularisation term balances fit against a chosen notion of complexity [11, §6.3]. Our existing quadratic objective supplies that balance through Equation (12). The candidate set is deliberately small: $\Lambda=\{10^{-7},10^{-6},10^{-5}\}$, corresponding to the earlier 0.1×, 1× and 10× baseline values at unchanged bin width. The experiment evaluates this finite rule; it does not search continuously for an optimum.

For each quote pattern, the ordered interior strikes are assigned in turn to three folds. Both endpoint quotes remain in every training set, retaining the observed span. Each interior quote is held out exactly once. Original 81 has 27, 26 and 26 held-out quotes per maturity; Extended 121 has 40, 40 and 39. The same fold positions are used at each maturity. All eight maturities are fitted jointly for every candidate and fold, using only that fold's training quotes.

Let $\mathcal H_k$ contain the quote positions held out in fold $k$, and let $\widehat C_{m,\lambda}^{(-k)}$ denote the resulting training-only call fit. The pooled criterion is

$$
\operatorname{CV}(\lambda)=
\frac{\displaystyle\sum_{k=1}^{3}\sum_{m=1}^{M}\sum_{i\in\mathcal H_k}
\left[\frac{\widehat C_{m,\lambda}^{(-k)}(K_{mi})-y_{mi}}{F_m}\right]^2}
{\displaystyle M\sum_{k=1}^{3}|\mathcal H_k|},
\qquad
\widehat\lambda=\max\!\left(\operatorname*{arg\,min}_{\lambda\in\Lambda}\operatorname{CV}(\lambda)\right).
\tag{30}
$$

The maximum resolves exact score ties in favour of stronger smoothing; no numerical tie band or one-standard-error rule is used. Pooling individual errors gives each held-out observation equal weight after forward scaling. Averaging the three fold means equally would instead overweight the smaller folds. Scaling by $F_m$ matches the price-loss convention of Equation (12); it is not division by the discount factor or inverse weighting by the noise variance.

The endpoints are excluded from the validation score, and the fitted training grids are thinner than the final grid. These deliberate choices make this an interior-price interpolation rule. It does not directly target unobserved tails, recover omitted wings or estimate the best coefficient for a full grid without approximation. Selection takes place within each quote pattern: the patterns' different spans and error variances mean that their absolute CV scores do not share an identical validation target. Three dependent folds also do not supply three independent repetitions: uncertainty is measured across the 20 separately generated quote realisations.

The selected coefficient is then used to refit all observations. A full-data fit with the fixed baseline $\lambda=10^{-6}$ is the paired control, using exactly the same quotes and numerical settings. When selection chooses the baseline, that fit is reused and the comparison is exactly zero. Clean-price errors, full-domain density errors and risk summaries are calculated only after selection and both full-data fits have been fixed. The final price grid contains the same 120 arithmetic master-strike midpoints per maturity as Notebook 7: 960 prices, none supplied to a fit. With Original 81, that common test grid includes extrapolation; with Extended 121, it lies within the observed span.

**Table 18.** Smoothing selections in 20 repetitions per benchmark and strike pattern. All columns refer to the declared candidate set; selecting an endpoint does not establish that it is optimal beyond this set.

{{SELECTION_TABLE}}

![Noisy validation scores for the three candidate penalties](../figures/figure_21_smoothing_selection_scores.png)

Figure 21. Mean pooled noisy-price validation MSE for each smoothing coefficient, with ±2 Monte Carlo standard errors across the 20 repetitions. The dimensionless score is multiplied by $10^9$ for display and the vertical scale is logarithmic. Lines connect the three evaluated candidates. These scores select the coefficient; they are not the final recovery-performance estimates.

{{SELECTION_COMMENT}}

## 3. Evaluating the complete selection rule

As Morris, White and Crowther discuss in *Using simulation studies to evaluate statistical methods*, finite simulation summaries have their own Monte Carlo uncertainty [16, §§5.2–5.4]. Tables 19–21 therefore show a mean followed by its MCSE in parentheses. Equation (29) is applied to within-repetition differences for Table 20. These MCSEs describe the declared experiment, not confidence intervals for a market distribution. All 20 planned repetitions must succeed before a group's performance is reported.

**Table 19.** Recovery after full-data refitting. The clean-price RMSE pools 960 withheld prices in each repetition. Full-density $L_1$ is averaged across eight maturities and includes the known omitted tails as in Equation (23). Upper-tail bias is the mean error in $Q(S_T>1.8F)$ at 365 days, expressed in percentage points. Entries are mean (MCSE).

{{PERFORMANCE_TABLE}}

![Selected and fixed smoothing compared on separate evaluation measures](../figures/figure_22_selected_and_fixed_recovery.png)

Figure 22. Mean clean-price RMSE and full-domain density error after refitting with selected or fixed smoothing, using the same quote realisations in each comparison. Bars show ±2 MCSE. A small price error does not, by itself, establish a small density error, since prices integrate the density through the payoff relationship in Equation (1).

**Table 20.** Paired selected-minus-fixed differences, reported as mean (MCSE). Negative values indicate lower error under the selection rule. The last column compares absolute errors for the fixed 365-day upper-tail event; it is not a difference between signed biases.

{{PAIRED_TABLE}}

{{RECOVERY_COMMENT}}

## 4. Perturbing the forward without changing the event

As Bahra explains in his Bank of England research paper, the risk-neutral valuation framework links the terminal mean to the forward under the stated assumptions [1, §2.1 and Mathematical appendix]. Equation (10) therefore enforces the supplied forward as an input. Meeting that constraint cannot establish that the input is correct.

The forward stress uses Extended 121, both benchmark families and the same 20 realisations. For every maturity, it supplies

$$
\widetilde F_m^{(\varepsilon)}=(1+\varepsilon)F_m,
\qquad
\varepsilon\in\{-0.005,-0.001,0,0.001,0.005\}.
\tag{31}
$$

These are declared ±0.5% and ±0.1% stresses, not estimated error probabilities or empirically calibrated forward uncertainty. Option strikes, observed prices, discounts and maturity times stay fixed. Each repetition retains the coefficient selected at the correct forward. Thus the study measures conditional sensitivity to forward inputs; it does not evaluate reselecting smoothing under an incorrect forward.

The support stays $[0.3,2.2]$ in supplied-forward coordinates. Its physical endpoints therefore move with $\widetilde F_m$. The fitted mean, normalised price loss, density roughness and calendar normalisation also use that supplied forward. These consequences are part of this estimator's response to changing its input, not separately isolated causal effects.

For evaluation, all fitted distributions must be expressed relative to the same known reference forward. In particular,

$$
\widehat g_m^{(\varepsilon),\mathrm{ref}}(x)
=F_m\widehat f_m^{(\varepsilon)}(F_m x),
\qquad
\widehat p_{1.8,m}^{(\varepsilon)}
=\int_{1.8}^{\infty}\widehat g_m^{(\varepsilon),\mathrm{ref}}(x)\,\mathrm dx.
\tag{32}
$$

The event remains $S_T>1.8F_m$, even when the supplied forward changes. The lower 0.8 and upper 1.2 thresholds are treated identically. In the code, the evaluation copy retains the fitted physical bin edges and probabilities and changes only the reference used to interpret them. It does not move, refit or renormalise the distribution. Independent uniform-distribution and physical-integration checks verify this conversion. The normalised variance remains centred at the fitted mean. The fitted mean relative to the reference forward is approximately $1+\varepsilon$ by construction, so it is not reported as an independent accuracy success.

Gatheral and Jacquier's martingale/convexity argument motivates the calendar ordering used here [12, §2.1]. In this stress experiment, passing that numerical check is conditional on the supplied forward curve. It does not verify the benchmark's correct curve, nor does it establish accuracy of the recovered density.

## 5. A diagnostic for incompatible forward inputs

The discounted expected-payoff relationship described by Bahra [1] also implies a useful lower bound. For a nonnegative, unit-mass distribution with mean $\widetilde F_m$, convexity of the positive-part payoff gives

$$
C_m(K_{mi})\geq L_{mi}^{(\varepsilon)}
=D_m\bigl(\widetilde F_m^{(\varepsilon)}-K_{mi}\bigr)_+,
\qquad
v_{mi}^{(\varepsilon)}=\bigl(L_{mi}^{(\varepsilon)}-y_{mi}\bigr)_+.
\tag{33}
$$

This is a project derivation from Equation (1), not a new pricing relationship attributed verbatim to a source. We record the number of quotes with shortfall $v>10^{-10}$ points, the maximum shortfall and its root mean square. The RMS shortfall is a theoretical lower bound on RMS fitting error at the observed quotes under exact probability constraints. It is distinct from the clean-price RMSE at the separate test strikes. No quotes are clipped or replaced. The bounded noise in Equation (26) prevents negative call prices but does not enforce this intrinsic-value bound; some zero-shift observations can therefore fail it too.

**Table 21.** Forward stress with the selected zero-shift coefficient held fixed. Entries are mean (MCSE); all errors use the same benchmark and physical risk events. The last column counts supplied-forward lower-bound violations among the 968 observed calls in each repetition. It diagnoses incompatible inputs, rather than failed solver convergence.

{{FORWARD_TABLE}}

![Recovery sensitivity to the supplied forward](../figures/figure_23_forward_input_sensitivity.png)

Figure 23. Sensitivity of the selected fit to the supplied forward, under Extended 121 coverage. Points are repetition means with ±2 MCSE; connecting lines are visual guides between the five stated stress levels. The price-error axis is logarithmic. The tail event remains $S_T>1.8F_{\mathrm{true}}$ at 365 days throughout. Calendar feasibility is checked separately in supplied-forward coordinates.

{{FORWARD_COMMENT}}

## 6. Numerical evidence, limitations and next stage

{{NUMERICAL_COMMENT}}

The source-and-protocol fingerprint, complete random states, observed-price export, fold memberships, fold residuals, fitted probabilities and solver histories are retained. The forward cases identify the exact selected parent case. Matching completed cases can be reused; altered inputs, code, content or parent results are rejected. Numerical success is reported separately from price, density and tail errors. The figure exporter validates temporary PNG and SVG files before replacing their destinations, retaining the correction introduced after Notebook 7's artifact check.

This experiment retains idealised bounded independent quote errors, deterministic rates/dividends, two chosen benchmark families and fixed support/resolution. It evaluates only three candidate penalties and 20 new realisations. Its interlaced folds are suitable for the declared interpolation question; a historical validation design must respect observation dates and contemporaneous quote structure. No clean density target is available for selecting a coefficient in real market data, and no empirical SPX density is claimed here.

The working [project roadmap](project_roadmap.md) now has eight completed notebooks and two planned empirical stages, followed by assembly of the final paper. The remaining gate is verified quote provenance, timestamps, settlement horizons, usable bid/ask observations and justified discount/forward inputs. Existing offline 3D maturity explorers remain available; historical-date animation depends on verified observations across dates. The [development reflection](development_reflection.md) records this notebook's observed difficulties, decisions and remaining limitations.

## Sources and reproducibility

References use the [shared bibliography and source mapping](references.md). The substantive sources used here are Bahra [1] for valuation and the forward mean; Boyd and Vandenberghe [11] for regularisation; Gatheral and Jacquier [12] for calendar ordering; Goulart and Chen [15] for the Clarabel solver; Morris, White and Crowther [16] for simulation summaries; and Cawley and Talbot [17] for separating selection from evaluation. The fold arrangement, candidate grid, shock levels, thresholds and numerical findings are project choices or calculations, not results asserted by those papers.

Evidence: [declared protocol](../results/selection_protocol.json), [feasibility pilot](../results/selection_pilot.json), [complete numerical report](../results/selection_validation.json), [post-hoc range diagnostic](../results/selection_range_diagnostic.json), [observed inputs](../results/selection_quotes.csv), [performance export](../results/selection_metrics.csv), [independent checks](../tests/test_selection.py), and the `results/selection_cases/` records.
