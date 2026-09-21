# 1 Introduction

## 1.1 Research background

Option prices contain information about the distribution of future outcomes, but extracting that information requires more than drawing a smooth curve through observed prices. As Bahra explains in *Implied risk-neutral probability density functions from option prices: theory and application*, a European option price is a discounted expected payoff under a risk-neutral probability measure [1]. The relationship allows prices to be used to recover a distribution. It also determines how that distribution should be interpreted: the probabilities are valuation probabilities, rather than direct estimates of how frequently an event will occur in the real world.

Breeden and Litzenberger established the relationship between the curvature of a call-price curve and its implied state-contingent claims [6]. Following the derivation presented by Bahra [1], this project begins with numerical differentiation of a known price curve and develops a constrained estimator for discrete observations. As Aït-Sahalia and Duarte explain in *Nonparametric option pricing under shape restrictions*, the direction and curvature of an estimated price function should respect the restrictions implied by option valuation [9]. These restrictions provide the foundation for the estimation work, although their particular locally polynomial estimator is not implemented here.

The practical difficulty is that market observations are finite, spreads are nonzero and information is unevenly distributed across strikes. In his study of option-based distributions, Malz discusses the importance of interpolation and extrapolation when calculating tail probabilities [14]. This motivates the central question of the present work: **how far can a numerically consistent option-implied density be trusted when the available price information is incomplete?**

## 1.2 Aim and objectives

The aim is to develop and critically evaluate a reproducible method for recovering risk-neutral terminal distributions from European SPX option prices. The work has five linked objectives: establish the price–density relationship on a known benchmark; replace unstable differentiation with a probability-constrained estimator; enforce consistency across observed maturities; measure sensitivity and recovery error in controlled simulations; and apply the method to traceable market observations while retaining its empirical and numerical limitations.

These objectives distinguish four questions that recur throughout the paper. Does the fitted object satisfy the probability and pricing restrictions? Does the numerical solution meet its stated tolerances? Does it reproduce the observations used to fit it? Finally, how accurately is the underlying distribution identified? A favourable answer to one question does not answer the others. In synthetic experiments, the last question can be measured against a known distribution. In the market application, that truth is unavailable, so the analysis instead reports sensitivity and conditional feasible probability ranges.

## 1.3 Scope and contribution

The project comprises ten analytical notebooks, progressing from a single synthetic expiry to dated empirical comparisons. Its contribution is the integrated implementation and evaluation of a finite histogram estimator, exact bin-payoff valuation, analytical checks between calendar-constraint locations, controlled recovery experiments and bid–ask-compatible empirical estimation. The individual valuation identities, optimisation principles and simulation summaries are established relationships; the discretisation, experiment designs and reported numerical findings are this project's work.

The empirical sample contains two dates, 31 August and 18 September 2026, with a second intraday observation on the latter date. It uses three SPXW settlement horizons per snapshot and documented exchange best bid and offer prices. It is a small conditional case study, not a historical backtest or an event study. Discount factors and forwards are estimated jointly from matched call–put observations; an independently observed discount curve and executable market depth are unavailable in this profile.

## 1.4 Organisation of the paper

Chapter 2 establishes the valuation relationships and the limitations of numerical differentiation. Chapter 3 addresses data assessment and the constrained single-maturity method. Chapter 4 links the maturity slices and develops the interval-level calendar check. Chapters 5 and 6 evaluate robustness, repeated perturbations, smoothing selection and forward sensitivity. Chapter 7 develops the empirical input process and the first market fit, before Chapter 8 addresses original bid–ask compatibility and dated comparisons. Chapter 9 consolidates the development setbacks and lessons. Chapters 10 and 11 discuss the evidence, answer the research question and identify further work. The appendices describe the reproducibility package and the four interactive companions.

# 2 Valuation relationships and numerical recovery

## 2.1 From European calls to a risk-neutral density

Let $S_T$ denote the terminal index level, $K$ the strike and $T$ the time to settlement in years. A density gives probabilities through integration over ranges of outcomes; its value at one exact outcome is not itself a probability. As Bahra explains in his Bank of England paper [1], deterministic discounting and a continuous terminal density give the expected-payoff representation in Equation (1).

{{EQ:1}}

Here $r$ is the continuously compounded rate and $f_Q$ is the density under the risk-neutral measure $Q$. Differentiating across strikes at one observation instant and one maturity gives Equation (2). The moving-boundary term is zero because the call payoff vanishes at $s=K$.

{{EQ:2}}

Differentiating once more gives the Breeden–Litzenberger extraction relationship [6], following its derivation in Bahra [1]. The argument requires the stated smoothness and valuation assumptions; it is not differentiation across maturities or observation dates.

{{EQ:3}}

## 2.2 Controlled benchmark and finite differences

Black and Scholes derive option valuation through a no-arbitrage argument [8]. As Bahra describes [1], the constant-volatility benchmark provides a lognormal terminal distribution. It is used here as a known answer against which the implementation can be assessed. The synthetic initial index level is 6,000, the annual rate is 4%, the continuous dividend yield is 1.5%, the annual volatility is 20% and the maturity is half a year. The dividend adjustment follows the spot–forward relationship discussed by Aït-Sahalia and Lo [10, Equation (16)]. These are illustrative inputs and do not assert a lognormal empirical SPX distribution.

As Driscoll and Braun explain in *Fundamentals of Numerical Computation*, §5.4, a three-point centred difference approximates the second derivative [7]. Substituting their stencil into Equation (3) gives Equation (4), where $h$ is the strike spacing.

{{EQ:4}}

The validated call grid spans 2,500–14,000 index points with spacing 5; density values use the interior points, 2,505–13,995. Grid endpoints are excluded because a centred stencil is unavailable there. No negative estimates are clipped and no density is renormalised. Figure 1 shows the input price curve and Figure 2 compares the recovered density with its analytical counterpart.

{{FIG:1}}

{{FIG:2}}

The curves nearly coincide in this controlled example. The forward is 6,075.470709 index points and is the risk-neutral mean under the assumptions described by Bahra [1, Mathematical appendix]. It is distinct from the density's mode. Table 1 records the numerical checks rather than relying on visual agreement alone.

{{TABLE:1}}

## 2.3 Convergence, cancellation and noisy observations

As Driscoll and Braun discuss in §5.5 [7], the centred second-difference truncation error is of order $h^2$ when the price function is sufficiently smooth. Refining the grid from 80 to 5 points produces approximately second-order convergence, as Figure 3 demonstrates. However, smaller steps also increase exposure to roundoff through subtraction of nearly equal values.

{{FIG:3}}

An initial lower boundary of 1,000 produced tiny negative second differences in the far left tail, where call prices were nearly linear. Raising the boundary to 2,500 reduced cancellation while retaining essentially all the known benchmark mass. This was a benchmark-specific numerical decision, not a rule transferred automatically to the empirical sample.

{{FIG:4}}

{{FIG4EXPLANATION}}

The clean-data result therefore validates the implementation within the tested conditions. It does not validate direct numerical differentiation of market quotes. The subsequent estimator addresses this failure by fitting probabilities subject to explicit restrictions, rather than interpreting clipped negative derivatives as recovered probabilities.

# 3 Quote assessment and constrained estimation

## 3.1 Assessing observations before calibration

Cboe's source and contract documentation distinguishes product conventions, observation fields and settlement classes [2–5]. These operational facts must be established before a statistical or numerical method can supply an interpretable market result. The first candidate payload contained 27,782 option records across 61 root/expiry groups. Its time-only field, 17:43:22, did not establish a complete quote observation instant. The underlying's last-trade timestamp described a different event, and every bid/ask size field was zero. Those fields were treated as unavailable information, not evidence that all contracts lacked liquidity.

Table 2 records the initial access assessment. It is a historical assessment of that stage: the separately supplied marking-price files used in Chapters 7–8 subsequently enabled the empirical application. They did not resolve the original payload's missing interpretation.

{{TABLE:2}}

For finite, ordered bid and ask prices, the audit uses the arithmetic midpoint and relative spread in Equations (5)–(6). These are project definitions rather than new pricing relationships.

{{EQ:5}}

{{EQ:6}}

At a 25% maximum relative spread, 25,866 records passed the provisional price screen; 1,916 were wider and 697 had a zero bid, with overlapping exclusion reasons retained. Tightening the threshold to 10% retained 24,721 records, while 50% retained 26,475. Counts describe the candidate data and do not establish usable observation timing or executable depth.

{{TABLE:3}}

{{FIG:5}}

{{FIG:6}}

As Aït-Sahalia and Lo explain in their state-price-density paper [10, §III.A], European put–call parity links prices at the same strike and maturity. Equation (7) states the relationship, and Equation (8) rearranges the opposite sides of the quoted spreads into an indicative forward interval conditional on the discount factor.

{{EQ:7}}

{{EQ:8}}

The interval requires matched contracts and compatible observation information. A provider specification cannot fill missing metadata in another payload. Table 4 identifies the required fields and the treatment at the initial audit stage. The later empirical adapter supplies a separate, explicit profile based on the information actually available.

{{TABLE:4}}

## 3.2 Representing a valid terminal distribution

As Aït-Sahalia and Duarte explain [9], imposing the shape restrictions of option valuation helps prevent inconsistent estimated price curves. The present implementation takes a direct probability approach. Interval $j$ has boundaries $a_j,b_j$, width $\Delta s_j$ and centre $m_j$. A mass $w_j$ is uniformly distributed inside it, giving the histogram in Equation (9).

{{EQ:9}}

The stepwise density is intentional and is zero outside its finite support. Following the mean–forward identity discussed by Bahra [1], the masses satisfy non-negativity, unit total mass and the supplied forward mean.

{{EQ:10}}

These are imposed conditions. Recovering a total mass of one or the supplied forward does not independently establish recovery accuracy. Integrating the positive-part payoff over each interval gives the exact bin-pricing map in Equation (11), a project discretisation of Equation (1).

{{EQ:11}}

Here $(x)_+=\max(x,0)$ and $A_{ij}$ is a discounted payoff coefficient, not an ask quote. The map is linear in the unknown probabilities. It produces a decreasing, convex, continuously differentiable call curve that is quadratic within each bin; its strike slope lies between $-D$ and zero. Its second derivative recovers the histogram away from bin boundaries.

## 3.3 Fitting noisy calls with a smoothness penalty

Boyd and Vandenberghe explain in *Convex Optimization* that regularisation balances agreement with observations against a chosen complexity criterion [11, §6.3]. Equation (12) applies that principle to second differences of the forward-normalised density heights $g_j=w_j/(\Delta s_j/F)$.

{{EQ:12}}

The observations $y_i$ and price residuals are in index points before division by $F$. The parameter $\lambda$ controls the penalty. The precise normalisation is a project choice; in particular, equal numerical coefficients do not produce equal effective smoothing when the bin width changes. This issue is examined explicitly in Chapter 5.

As Boyd and Vandenberghe describe [11, §4.4], a convex quadratic objective with affine restrictions has a quadratic-programme formulation. The initial implementation uses sequential least-squares programming with an analytical gradient and independent residual checks. No negative masses are clipped and no fitted density is renormalised.

## 3.4 Single-maturity validation

The experiment uses 81 calls between $0.65F$ and $1.45F$, independent Gaussian errors with standard deviation 0.5 points and seed 2026, and 120 bins on $[0.3F,2.2F]$. This is a separate noise experiment from Figure 4. The baseline is $\lambda=10^{-6}$, with $10^{-8}$ and $10^{-4}$ as sensitivity cases. Known prices at 80 interleaved strikes are excluded from fitting and used only for subsequent evaluation.

{{TABLE:5}}

{{FIG:7}}

{{FIG:8}}

The baseline achieves a withheld clean-price RMSE of 0.246113 points and integrated absolute density error of 0.030998 on the fitting support. Raw differentiation gives 18 negative estimates among 79 interior strikes, whereas the constrained masses remain nonnegative. This demonstrates the intended structural improvement within the chosen experiment. It does not establish an optimal penalty or resolve tail extrapolation.

{{TABLE:6}}

{{FIG:9}}

Changing the penalty alters both the price residuals and recovered shape. The analytical benchmark probability outside the chosen support is approximately $8.21\times10^{-9}$, so truncation is negligible in this particular case. Broader distributions need an explicit outside-support accounting, developed in Chapter 5.

# 4 Consistency across maturity

## 4.1 Valid marginal densities can form an inconsistent family

The next experiment fits eight horizons: 30, 60, 90, 120, 180, 240, 300 and 365 days, each divided by 365 for valuation. Each horizon contains 81 strikes spanning $F\exp(\pm2.5\sigma\sqrt T)$, with linear spacing between the endpoints. The known volatility determines this synthetic design, not empirical strike selection. Bounded independent price errors are uniform on $[-0.5,0.5]$ points, with standard deviation approximately 0.288675 points. The seed at each horizon is 20260920 plus its day count.

As Gatheral and Jacquier explain in their calendar-arbitrage discussion [12, §2.1], normalised call values should be ordered across increasing maturities under the relevant martingale and carry assumptions. Retaining discounting explicitly gives Equation (13), with $\kappa=K/F(T)$.

{{EQ:13}}

Under the project's deterministic-carry and proportional-dividend assumptions, the implemented ordering is Equation (14). It is checked within an observation snapshot, not between separate observation dates.

{{EQ:14}}

The initial independent fits retain 120 normalised bins on $[0.3,2.2]$ and $\lambda=10^{-6}$. Equation (15) defines their integrated absolute error on the fitting support. It is a project evaluation measure, not a claim that the estimator minimises density error.

{{EQ:15}}

{{TABLE:7}}

{{FIG:10}}

{{FIG:11}}

The visual surface connects the fitted maturity slices for viewing. It is not an estimated continuous-time model. All individual distributions satisfy their probability restrictions, yet 2,762 of 13,307 sampled calendar comparisons fail at the stated tolerance. The worst normalised gap is approximately $-1.90808\times10^{-4}$. None of the 4,267 comparisons inside both adjacent quote ranges fail; the difficulty is concentrated where prices are extrapolated.

{{TABLE:8}}

## 4.2 A joint programme in common coordinates

To link the maturities, define $x=s/F_m$ and common bin edges $u_j$, width $\Delta u$ and centres $\bar u_j$. Equation (16) relates the normalised and physical densities. A common coordinate system allows adjacent maturities to be compared at the same forward moneyness.

{{EQ:16}}

Equation (17) minimises the sum of the per-maturity objectives while imposing the mass, mean and calendar restrictions jointly. The payoff row $\mathbf B(\kappa)$ is the exact uniform-bin normalised call map, and $\mathcal K_m$ initially contains the internal bin boundaries. The quadratic-programme framework follows Boyd and Vandenberghe [11]; the calendar motivation follows Gatheral and Jacquier [12].

{{EQ:17}}

An independent fit with the same OSQP solver provides a control for the change of optimisation software. As Stellato and colleagues explain in their OSQP paper [13], the method uses residual-based stopping criteria. The project additionally checks the returned probabilities and full interval calendar gaps. Numerical status alone is insufficient.

## 4.3 Checking between the constraint locations

A coarse grid can miss a negative gap between checked locations. For adjacent maturities, let $\delta_{mj}=w_{m+1,j}-w_{mj}$. Exact bin integration makes the later-minus-earlier normalised call gap quadratic within each bin, as Equation (18) shows.

{{EQ:18}}

Endpoints are always checked. Where the quadratic is convex and its stationary point lies inside the bin, Equation (19) supplies the additional eligible minimum.

{{EQ:19}}

These are project derivations from the uniform-bin payoff, rather than formulae taken from the SVI parameterisation in [12]. Violating interior minima are added as constraint locations and the programme is solved again. A deliberately constructed mean-one counterexample passed boundary checks but reached a gap of $-0.009375$ at $\kappa=0.875$, independently demonstrating why the interval check is needed.

## 4.4 Results of joint fitting

The baseline joint problem has 960 masses. Its initial 833 calendar rows grow to 858 after five refinement rounds. The boundary-only solution reaches an interval minimum of approximately $-3.14\times10^{-7}$; refinement improves it to $-8.56\times10^{-10}$, inside the $10^{-8}$ reporting tolerance and the $10^{-9}$ refinement target.

{{TABLE:9}}

{{FIG:12}}

The same-solver independent control has 2,763 sampled violations and the joint fit has zero. Withheld clean-price RMSE changes only from 0.119513 to 0.119153 points. Mean density error changes from 0.035158 to 0.035162, a slight deterioration. The regularised objective increases by approximately 0.03994%, as expected when adding restrictions. The extra independent-control violation relative to the earlier count reflects a numerical threshold difference, not new observations.

{{TABLE:10}}

{{FIG:13}}

{{FIG:14}}

The joint fit resolves the stated calendar inconsistency but retains a tail bump beyond the largest one-year quoted strike, approximately 10,143 points. This is the motivation for the subsequent sensitivity analysis. The maximum mass and normalised-mean residuals are $8.44\times10^{-15}$ and $5.11\times10^{-15}$; a minimum signed mass of approximately $-1.57\times10^{-12}$ is retained as a numerical residual. The accepted OSQP result is not described as polished, because polishing was not accepted.

# 5 Robustness and repeated synthetic evaluation

## 5.1 Extending the benchmark and making smoothing comparable

As Bahra discusses in his treatment of mixture distributions [1, §§3.5–3.6], a weighted mixture provides a more flexible terminal distribution than a single lognormal component. The second benchmark uses component weights 0.75 and 0.25, volatilities 14% and 40%, and a common component mean equal to the forward. Equation (20) states the corresponding mixture density and weighted call values. These parameters are declared synthetic choices.

{{EQ:20}}

The sensitivity study varies support, bin count and smoothing across seven settings for each benchmark. Changing bin width also changes the action of an unscaled second-difference penalty. Applying the stencil discussed by Driscoll and Braun [7] motivates the grid-scaled roughness in Equation (21).

{{EQ:21}}

Equating this penalty with the convention in Equation (12) gives Equation (22). The baseline $\alpha_0$ reproduces $\lambda=10^{-6}$ on the original 120-bin grid. Thus changing resolution is not inadvertently treated as a simultaneous arbitrary change in smoothing strength.

{{EQ:22}}

{{TABLE:11}}

The narrower and wider supports use nested edges with the same bin width as the baseline. The settings are a declared sensitivity study, not parameters optimised against the known density. The finite fitted support remains a substantive restriction even when its edge selection is numerically convenient.

## 5.2 Measuring density and tail errors

Because the fitted density is zero outside its support, evaluating only the central integral would omit a known source of error. Equation (23) extends the density measure to the full positive domain by adding the benchmark probability outside the fitted range.

{{EQ:23}}

Following Malz's discussion of threshold-based summaries and extrapolation [14], Equation (24) defines three risk-neutral events. The thresholds are project choices in forward coordinates, not calibrated statements about economically exceptional moves.

{{EQ:24}}

Equation (25) gives exact histogram variance and the corresponding known mixture variance. These are variances of the normalised terminal level, not annualised implied volatilities. In the fitted case $\widehat\mu$ is its normalised mean.

{{EQ:25}}

{{TABLE:12}}

{{FIG:15}}

{{FIG:16}}

For the single lognormal, moving from 80 to 160 bins changes withheld price RMSE only from 0.119451 to 0.119123 points, while density error changes from 0.048880 to 0.028548. Similar price agreement therefore conceals a noticeable difference in the recovered density. At one year, the known mixture probability omitted by the narrow support is 1.9339%, compared with 0.1273% for the wider support.

{{TABLE:13}}

{{FIG:17}}

The known probability above $1.8F$ is 0.118709% for the single lognormal, while the seven fitted values range from 0.010066% to 0.058278%. For the mixture, the corresponding truth is 1.188550% and fitted values range from 1.745535% to 2.720848%. All fourteen joint fits pass their structural checks. The ranges are sensitivity summaries, not confidence intervals, and their common bias shows why apparent stability alone is insufficient.

The broader benchmark also exposed a solver limitation. OSQP reached its strict iteration limit; increasing the allowance from 100,000 to 300,000 and trying objective scaling did not establish an acceptable solution. An algebraically equivalent formulation retained explicit price and roughness residual variables and used Clarabel. As Goulart and Chen describe [15], that solver supports conic programmes with quadratic objectives. Controlled cross-solver checks preceded its use in the sensitivity batch. The accepted fourteen fits retain their original tolerances and independently checked constraints.

## 5.3 Separating noise from missing strike information

As Morris, White and Crowther explain in *Using simulation studies to evaluate statistical methods*, the experiment design and uncertainty of its reported summaries require explicit treatment [16]. A repeated study therefore compares four nested quote patterns: Original 81, Sparse 41 across the original span, Central 41 within a narrower span, and Extended 121 with twenty additional strikes at each side. Comparing the two 41-strike patterns isolates a coverage difference while holding the count fixed.

{{TABLE:14}}

{{FIG:18}}

Each benchmark, pattern and error amplitude uses fifty repetitions. Equation (26) supplies bounded independent quote perturbations with amplitude limits of 0.1 and 0.5 points. The minimum with half the clean call price keeps supplied prices positive on the extended grid. Its amplitude is a half-width, not a standard deviation.

{{EQ:26}}

The errors have conditional mean zero and variance $\eta_{mi}^2/3$, but do not preserve every arbitrage inequality. This is a deliberately idealised synthetic mechanism, not an empirical bid–ask noise model. Shared PCG64 child streams pair the master-strike errors across comparable designs; their states are retained for replay. Eight clean-input controls distinguish limitations that exist without price perturbations.

The common validation grid has 120 arithmetic master-strike midpoints per maturity, giving 960 known prices never supplied to a fit. Results distinguish points inside and outside the observed range. Empty outside-range subsets are reported as unavailable, rather than assigned zero error. Equations (27)–(29) define the simulation summaries, Monte Carlo standard error of a mean and precision of a paired contrast, following the framework discussed by Morris and colleagues [16].

{{EQ:27}}

{{EQ:28}}

{{EQ:29}}

The $n_{\mathrm{sim}}-1$ variance denominator explains the finite-sample factor in Equation (27). The spread of individual estimates is different from the MCSE of their mean. Neither is an empirical confidence interval for an SPX density. Paired differences use within-repetition contrasts before estimating their standard error.

## 5.4 Results across repeated quote realisations

Table 15 reports the complete repeated comparison, with one MCSE alongside each mean. Figure 19 separates price and density performance so that a favourable value of one does not conceal a poor value of the other.

{{TABLE:15}}

{{FIG:19}}

At amplitude 0.5 points, Central 41 minus Sparse 41 increases mean density error by 0.00614 for the single lognormal, with MCSE 0.00038, and by 0.06001 for the mixture, with MCSE 0.00064. The narrower span is materially worse despite having the same number of observations. Even with clean mixture prices, Central 41 gives a within-range price RMSE of 0.1186 points but 7.7981 points on the common validation grid. This exposes extrapolation error without attributing it to random noise.

{{TABLE:16}}

{{FIG:20}}

{{TABLE:17}}

For the single lognormal, the mean estimated probability above $1.8F$ moves from 0.0744% under Original 81 to 0.1161% under Extended 121, against truth 0.1187%. The paired reduction in absolute probability error is 0.0231 percentage points, with MCSE 0.0050. For the mixture, the estimates move from 1.4994% to 1.1450%, against truth 1.1885%; the paired reduction in absolute error is 0.2632 percentage points, with MCSE 0.0338.

The full batch contains 800 noisy and eight clean fits, or 6,464 marginal densities. All 808 joint fits meet the acceptance rule; the worst calendar gap is $-9.995\times10^{-10}$. These successes describe numerical completion. They do not remove the model, support or missing-information errors measured above.

# 6 Smoothing selection and forward sensitivity

## 6.1 Evaluating a complete selection procedure

As Cawley and Talbot explain in *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*, tuning a method and assessing its performance are distinct operations [17]. This study therefore selects smoothing from noisy prices alone and reserves clean prices, densities and event probabilities for evaluation. It uses Original 81 and Extended 121, both benchmarks and twenty new paired realisations at amplitude 0.5 points.

The declared candidates are $\Lambda=\{10^{-7},10^{-6},10^{-5}\}$. Interior strikes are assigned in order to three interlaced folds, while both endpoints remain in training. All eight maturities are fitted jointly in every fold. Equation (30) pools the individual held-out errors after forward scaling and resolves exact ties in favour of the larger coefficient.

{{EQ:30}}

Pooling matters because the folds have different numbers of observations. Equal weighting of fold means would overweight smaller folds. The score targets interpolation at interior strikes; it does not directly target density recovery or unobserved tails. Every repetition reruns selection, then refits all observations at the selected coefficient. The fixed $10^{-6}$ refit is a paired control using exactly the same quotes.

{{TABLE:18}}

{{FIG:21}}

Across eighty selection experiments, the three coefficients are selected forty, forty and zero times. A boundary choice establishes only a preference within the declared grid. The grid is not extended after inspecting the synthetic evaluation results.

## 6.2 Price selection and density recovery are different targets

The selected rule is assessed against the fixed baseline on the same quote realisations. Tables 19–20 and Figure 22 retain price, density and tail measures separately, with paired differences used to assess the change.

{{TABLE:19}}

{{FIG:22}}

{{TABLE:20}}

For the mixture under Original 81, selection changes mean common-grid clean-price RMSE from 0.8887 to 1.0928 points and density error from 0.0574 to 0.0704. Under Extended 121, price RMSE improves from 0.1587 to 0.1174 points while density error worsens from 0.0524 to 0.0630. The latter paired density increase is 0.0107, with MCSE 0.0004. These findings concern the specified selector and benchmarks; they do not establish that cross-validation is generally ineffective.

A post-hoc range diagnostic explains the Original 81 discrepancy without changing the selector. At the 640 evaluation strikes inside the quoted span, price RMSE improves from 0.1571 to 0.1235 points; at the 320 outside it, RMSE worsens from 1.5224 to 1.8847. Better interior interpolation accompanies worse extrapolation. The diagnostic is labelled as subsequent analysis, rather than presented as a predeclared performance result.

## 6.3 Perturbing the input without moving the risk event

As Bahra explains [1], the terminal mean is linked to the forward under the valuation assumptions. Enforcing that mean cannot prove that an externally supplied forward is correct. The Extended 121 experiment therefore perturbs the supplied forward as in Equation (31), retaining strikes, prices, discounts and the coefficient selected at the correct forward.

{{EQ:31}}

The support remains $[0.3,2.2]$ relative to the supplied forward, so its physical endpoints move. Mean restrictions, residual scaling, smoothing and calendar normalisation also depend on the supplied input. The exercise measures their combined conditional response, not separately identified causal effects.

Equation (32) evaluates every fitted distribution against the same known reference forward. In particular, the event remains $S_T>1.8F_m$ even when the fitting input changes. The conversion changes the interpretation coordinate of a saved fit; it does not move or refit its physical probabilities.

{{EQ:32}}

Applying convexity of the positive-part payoff to Equation (1) gives the call lower bound and quote-shortfall diagnostic in Equation (33). This is a direct project derivation from the valuation relationship described by Bahra [1].

{{EQ:33}}

The RMS shortfall is a lower bound on training-price RMSE under exact probability restrictions, not on the separate clean-price evaluation error. No supplied observations are clipped to satisfy it.

{{TABLE:21}}

{{FIG:23}}

For the mixture, mean clean-price RMSE is 0.1174 points at the correct forward, 1.7653 points at a −0.5% shift and 10.2713 at +0.5%. The positive shift places an average of 227.3 of 968 supplied calls below the implied lower bound. This helps explain the asymmetry without claiming to isolate every consequence of the input change.

The study contains 1,000 unique accepted joint fits, or 8,000 marginal densities, including training fits. No planned experiment is silently omitted. The worst calendar gap is $-9.996\times10^{-10}$. The experiment still assumes idealised independent bounded quote errors, two benchmark families and fixed support. Its success does not validate a market forward curve or convert risk-neutral events into physical forecasts.

# 7 Empirical inputs and the first market calibration

## 7.1 Establishing an auditable input route

A working estimator did not initially provide usable observations. The advertised Cboe end-of-day sample request returned HTTP 403 [18]; another provider's advertised 2022 sample did not support the required contemporaneous timestamp interpretation [19]; WRDS described an institutional route but did not establish access to an unseen export [20]. Table 22 preserves that source assessment. No purchase or account access was undertaken.

{{TABLE:22}}

The original candidate remained unaccepted. A subsequent API retrieval with a fuller timestamp returned the same option array but did not establish the timezone or meaning needed to treat it as a verified quote instant. The implementation therefore separated the file format and validation rules from market access, using an explicitly synthetic input bundle to exercise the process.

The preparation profile requires a quote CSV, a discount CSV and a manifest recording conventions and source evidence. Full UTC-offset timestamps distinguish observation from settlement; ACT/365F uses elapsed UTC seconds. External discounts must have been available at the observation instant. A positive discount above one is permitted. Hashes support traceability but do not prove provenance, permission or economic suitability.

## 7.2 Conditional forwards and training-only inference

Using the parity foundation in Aït-Sahalia and Lo [10], Equation (34) intersects the pairwise intervals from Equation (8). Its midpoint is a declared point-input convention conditional on the supplied discount, not a statistically identified true forward.

{{EQ:34}}

An empty intersection blocks density fitting. Equation (35) records the minimum uniform widening needed to intersect the conditional forward intervals. It is measured in forward index points and is diagnostic only; no quote repair is applied.

{{EQ:35}}

{{FIG:24}}

In the synthetic example, shifting one call's bid and ask by five points leaves its row positive and ordered but destroys the common intersection. The required widening is 1.7234 forward points. Row screening therefore cannot replace cross-strike compatibility checks.

As Cawley and Talbot's discussion of selection makes clear [17], inferred inputs are part of the procedure being evaluated. Whole call–put pairs are held out, and the forward is recomputed from each training subset. Equation (36) extends the selection score accordingly. Endpoints stay in training and exact score ties choose the larger coefficient.

{{EQ:36}}

## 7.3 Synthetic acceptance exercise

The fixture contains 282 invented quote rows: 41, 47 and 53 pairs across three nominal horizons. Prices come from the two-lognormal mixture. Each analytical price receives a half-spread equal to the smaller of 0.75 points and 8% of that price; a midpoint perturbation of at most one fifth of the half-spread leaves the known price inside the range. Seed entropy is (20260921, 9). Dates, sizes and identifiers test the input process and do not claim actual exchange observations.

{{TABLE:23}}

The three candidate scores select $10^{-7}$, the lower grid boundary. Nine training fits and one refit produce ten accepted joint fits. Separate analytical prices at 138 strike midpoints and the known density are used only after fitting. Equation (37) defines a point-distance diagnostic for both option types, including puts inferred from parity.

{{EQ:37}}

{{TABLE:24}}

{{FIG:25}}

One fitted price lies approximately 0.01993 points outside its quoted range. The result is retained. Parity compatibility does not imply that a regularised midpoint objective will satisfy every spread, and this residual does not prove that a spread-feasible fit is impossible. The distinction becomes central in Chapter 8.

{{TABLE:25}}

The deliberately invalid fixtures test missing or conflicting metadata, unsuitable discounts and incompatible forwards. Additional checks change held-out observations and verify that their training-only inputs remain unchanged. The fixture demonstrates a complete file-to-fit process; it is kept distinct from the empirical evidence that follows.

## 7.4 The supplied market files and contract scope

Cboe's marking-price documentation distinguishes indicative prices from exchange BBO fields [21]. The application uses the last-disseminated market bid and ask columns for calls and puts, not the final indicative marks. The supplied files were matched byte-for-byte to the advertised downloads, with hashes and retrieval records retained. Table 26 describes their initial roles; all three are analysed in Chapter 8.

{{TABLE:26}}

The files supply two observation dates and three snapshots. Concatenating the two September snapshots would mix observation instants. Indicative size entries of one are not demonstrated market depth. A separate exchange-BBO adapter records actual size as unavailable and makes no consolidated NBBO or execution-depth claim; the original external-curve profile remains separate.

The first market case uses 18 September 2026 at 15:00 Chicago time, with SPXW expiries on 16 October, 20 November and 18 December. Cboe's specifications and 2026 schedule support the PM settlement convention used here [5,22]. Settlement is represented at 16:00 New York civil time, including the November offset change. The elapsed horizons are 28, 63 plus 1/24, and 91 plus 1/24 days. The extra hour comes from daylight saving, not an additional trading session.

The adapter checks the encoded root, expiry, type and strike, requires finite positive ordered prices on both sides, limits each relative spread to 25%, and excludes duplicates without averaging. Both last-update messages must be no later than the snapshot and no more than sixty seconds old. These are declared activity criteria, not proof of execution availability. The three selected expiries retain 364, 344 and 261 pairs: 969 pairs and 1,938 option intervals.

## 7.5 Inferring a quote-implied carry proxy

The files do not contain a discount curve. Rearranging the parity relationship discussed by Aït-Sahalia and Lo [10] gives Equation (38), where $H_m=D_mF_m$ and opposite bid–ask sides define the admissible difference range.

{{EQ:38}}

Equation (39) jointly estimates discount and forward through equal-weight constrained least squares. The strike normalisation $K_{0m}$ is the median retained strike, and the small positive carry floor is a numerical convention. This estimator is a project choice supported by the convex-QP framework in Boyd and Vandenberghe [11].

{{EQ:39}}

The implementation centres strikes and independently verifies every parity bound. Separate LPs project the feasible discount interval. That projection is a compatibility set, not a confidence interval. An empty or unbounded projection blocks calibration. The forward is the regression-implied ratio $\widehat H/\widehat D$, rather than the midpoint of Equation (34)'s conditional interval.

{{EQ:40}}

Equation (40) merely converts the fitted discount into an equivalent continuously compounded rate. It is not an independently observed risk-free curve or a finding about a particular funding mechanism. Bid–ask effects and the assumed parity inputs can influence it.

{{TABLE:27}}

## 7.6 Market fit, selection and remaining spread misses

Both discount and forward are re-estimated from training pairs in each of the three interior-strike folds. The primary grid remains $\{10^{-7},10^{-6},10^{-5}\}$ on 120 bins. Its weakest coefficient wins. The criterion predicts call midpoints; puts provide parity information and separate fit diagnostics.

{{TABLE:28}}

{{FIG:26}}

The curves are close on the plotted price scale, yet 650 of 1,938 fitted call/put values miss their original spreads at a $10^{-7}$-point counting tolerance. The largest miss is 1.8661 points. Narrow put spreads can amplify modest point discrepancies in half-spread units. This is an in-sample failure of quote reproduction, not a failure of the probability constraints.

A separately recorded post-hoc grid, $\{10^{-10},10^{-9},10^{-8}\}$, tests whether weaker smoothing explains the result. It selects $10^{-10}$, again at the boundary, with a call-price score approximately 60% lower. Nevertheless, 501 prices still miss their spreads: three calls and 498 puts. The $10^{-9}$ refit has fewer misses, 496, despite a slightly worse score. Optimising call interpolation and satisfying both quote intervals are different targets.

{{TABLE:29}}

{{FIG:27}}

{{TABLE:30}}

As Malz discusses [14], tail interpretation requires attention to extrapolation. Retained upper strikes reach only about $1.0905F$, $1.1571F$ and $1.2188F$ across the three horizons. The $1.8F$ event is outside all these spans. The first-horizon point estimate for this event changes from approximately 0.009674% under the primary coefficient to 0.000001186% under the weaker diagnostic fit. Neither is validated against an observable market density.

All twenty-four empirical joint fits, including the diagnostic grid, have strict solved status and pass the interval calendar check. The smallest final gap is $-5.749\times10^{-10}$, and signed numerical masses are retained. The within-snapshot ordering is conditional on inferred deterministic carry and proportional dividends, following the assumptions underlying Gatheral and Jacquier's argument [12]. The index's actual cash-dividend process is not reconstructed.

{{FIG:28}}

The empirical explorer provides exact histogram slices as well as the visual surface. It labels post-hoc settings and spread-miss counts with the selected curve. These presentation choices ensure that a convincing 3D view does not hide the fitting limitations.

# 8 Original-spread compatibility and dated comparisons

## 8.1 Defining a common empirical comparison

The final analytical stage uses all three snapshots and the same October, November and December SPXW expiries. It retains 840 pairs in August, 969 in the standard September snapshot and 950 in the later snapshot. Carry is inferred separately for each observation and expiry. A common-contract control uses the intersection of retained contracts across snapshots and re-estimates carry on that sample; it changes composition and carry together.

{{TABLE:31}}

As Cohen, Reisinger and Wang discuss in *Detecting and Repairing Arbitrage in Traded Option Prices*, bid–ask information is relevant to assessing price compatibility [23]. Their soft-bound repair formulation is not implemented here. Instead, the project checks compatibility within its finite density family and then requires the fit to satisfy the original intervals without quote repair.

## 8.2 Distinguishing grid feasibility from quote inconsistency

Equation (41) intersects the call spread with the parity-transformed put spread, using the point carry inputs. A call inside that intersection has a parity-implied put inside the original put interval.

{{EQ:41}}

Let $\mathcal P_J$ denote the masses satisfying non-negativity, unit mass, unit normalised mean and the interval calendar restrictions. Equation (42) calculates the minimum uniform price widening needed for the exact bin-price map to meet the interval bounds.

{{EQ:42}}

The LP uses the linear-programming framework described by Boyd and Vandenberghe [11], with interval refinement for calendar restrictions. The widening is diagnostic only. A positive value blocks that representation; the widened prices are not used for estimation. Its result is conditional on carry, support and bin basis and does not establish model-independent market arbitrage.

{{TABLE:32}}

The late snapshot requires approximately 0.026564 points of widening on 120 bins, both with independent maturities and with calendar constraints. On 240 bins, the original spreads are feasible. The finer common grid is therefore used for all three primary fits. This decision follows pilots on all snapshots; none is an untouched temporal test set. The 120-bin controls remain available.

## 8.3 Selecting a smooth member of the feasible family

Let $\mathcal F_J$ be the subset satisfying the original intervals without widening. Equation (43) chooses the member with minimum density-height curvature, using the finite-difference stencil described by Driscoll and Braun [7] and the smoothing framework discussed by Boyd and Vandenberghe [11].

{{EQ:43}}

For a fixed equal-width grid this is a positive multiple of Equation (21), so it gives the same minimisers when used alone. There is no trade-off parameter against midpoint error. Spread compatibility is now imposed; a zero in-sample miss count is therefore a construction property, not independent density validation.

As Goulart and Chen's solver discussion makes clear [15], numerical stopping criteria are formulation dependent in finite precision. The physical-price QP initially returned AlmostSolved. Objective multipliers of 0.1, 10 and 100 did not resolve it. Dividing quote rows and bounds by the forward achieved strict Solved status for the primary fits without changing their feasible sets. Accepted QPs require solver tolerances of $10^{-11}$ and independent checks in original price units.

A September 120-bin control returned Solved but missed a physical bound by $2.97\times10^{-7}$ points, above the $10^{-7}$ acceptance threshold. An equivalent positive quote-row multiplier of ten resolved that case. The runner records all attempts with multipliers one, ten and one hundred; it neither modifies the quotes nor loosens the acceptance rule.

{{TABLE:33}}

{{FIG:29}}

All 5,518 original option intervals across the three primary snapshots have zero counted misses at the stated tolerance. The September 120-bin hard-bound control also achieves zero, showing that its improvement does not require increased resolution. Across the wider run, sixteen of eighteen attempted QP cases are accepted, giving forty-eight marginal fits. The late 120-bin case is blocked by grid feasibility, and one late validation fold remains numerically unresolved.

## 8.4 Held-out pairs and the unresolved fold

Whole call–put pairs are withheld at interlaced interior strikes. Carry is recomputed using training pairs only. As Cawley and Talbot discuss [17], evaluation after inspected design choices must be described carefully: these are descriptive interpolation checks, not blind evidence of future-date performance.

{{TABLE:34}}

The first late-snapshot fold is feasible in its LP, but its QP does not meet the complete numerical rule. Row multiplier one returns Solved with a physical miss of approximately $1.29\times10^{-7}$ points; multipliers ten and one hundred return AlmostSolved. The case is retained and excluded with explicit coverage of two accepted folds out of three. It is not reclassified as quote incompatibility or silently replaced.

Even successful folds leave some held-out prices outside their ranges: forty of 1,668 evaluated option quotes in August and forty-six of 1,926 in standard September. The late result covers only 1,256 quotes and is not directly comparable as a complete-fold score. Exact in-sample compatibility does not automatically extend to unseen strikes.

## 8.5 Conditional ranges rather than a single tail answer

As Malz explains [14], tail probabilities can depend strongly on extrapolation choices. To quantify the remaining freedom within the declared empirical representation, Equation (44) removes the curvature objective and minimises or maximises each event probability over $\mathcal F_J$. The vector $\mathbf a$ contains exact event fractions within bins.

{{EQ:44}}

All maturities remain jointly constrained while one event is optimised. The seventy-two completed LPs provide conditional feasible ranges. They fix the 240-bin support, point carry, selected observations and any stated interpolation weights. They are not confidence intervals, do not propagate carry or sampling uncertainty, and are not asserted to be sharp over every possible distribution. Their independent physical-price residual limit is $2\times10^{-6}$ points, separately reported from the QP counting tolerance.

## 8.6 Fixed expiries and a common elapsed horizon

A fixed expiry is eighteen days closer in September than in August and another fifteen minutes closer in the late snapshot. Each fit also uses its own inferred forward. Figure 30 therefore combines changing observations with changing time to settlement, and a fixed normalised threshold need not represent the same physical index level.

{{FIG:30}}

For a complementary comparison, Equation (45) explicitly assumes a linear mixture between adjacent normalised maturity distributions bracketing sixty elapsed days. It does not extrapolate or invent a sixty-day discount factor or forward.

{{EQ:45}}

The mixture preserves non-negativity, unit mass and unit normalised mean. Normalised call values mix linearly and remain between their ordered endpoints. This mathematical preservation does not turn the interpolated slice into an observed sixty-day distribution. Its events concern the assumed normalised variable.

{{FIG:31}}

{{TABLE:35}}

Equation (46) provides a descriptive distance between two histograms on the same normalised bins. Integrating each constant bin-height difference gives the sum of absolute mass differences. Neither fitted density is treated as truth.

{{EQ:46}}

The common-sixty-day August-to-September distance is 0.048225 using all pairs and 0.051226 for the common-contract control. Between the two September snapshots it is 0.018170 and 0.017322, respectively. These are distances between conditional fitted distributions, not recovery errors or measures of statistical significance.

{{TABLE:36}}

{{FIG:32}}

The selected probability below 0.8 is 1.3073% in August and 1.3889% in standard September. Their conditional feasible ranges, approximately 0.9822–1.7321% and 1.1862–1.6391%, overlap. The standard September probability above 1.8 is approximately 0.0002990%, yet its feasible upper bound is approximately 0.0157987%. A near-zero selected value therefore does not establish a near-zero compatible event range.

The intervals do not support a statistically established date change or a particular market-event explanation. They expose the dependence of individual tail estimates on the selected solution within the stated family.

The dated explorer retains shared scales, exact histogram slices and the separately labelled sixty-day mixture. Playback steps through the three observations rather than manufacturing observations between the two dates. The all-pair risk ranges are hidden when the common-contract control is selected because its quote family and carry differ.

{{FIG:33}}

# 9 Development challenges and lessons learned

## 9.1 Purpose of the development record

The development process forms part of the evidence for the final method. This chapter records observed setbacks, approaches tested, outcomes and remaining limitations across all ten notebooks. Deliberately invalid fixtures and designed stress tests are distinguished from unexpected implementation failures. The full, continuously maintained record remains in `research/development_reflection.md`; the following account consolidates its substantive lessons into the research argument.

## 9.2 Notebook 1: a smaller numerical step was not always better

The first setback was tiny negative curvature in the far left tail of the clean benchmark. Nearly linear call values made second differences vulnerable to cancellation. The response was to inspect the location and size of the problem, restrict the lower evaluation boundary and check retained mass, mean, convergence and repricing. Negative values were not clipped away. Driscoll and Braun's account of truncation and roundoff [7] explained why refinement alone could not guarantee improvement.

The intentional noise experiment then produced much larger negative estimates. Its lesson differed from the cancellation case: raw differentiation amplified inconsistencies already present in the perturbed quotes. This motivated the constrained estimator. In presentation, the explanation of Figure 4 was moved below its own figure and caption, keeping the interpretation adjacent to the evidence; that placement is preserved in this paper and in the notebook.

## 9.3 Notebook 2: retrieving prices did not establish usable observations

The candidate download looked substantial but lacked a verified complete observation instant and meaningful size interpretation. Treating an underlying last trade as an option quote timestamp would have supplied an unsupported shortcut. Instead, the raw payload and row-level exclusions were retained, provider documentation was reviewed and calibration remained blocked for that candidate. Later retrieval of the same array with a fuller timestamp did not itself settle the timestamp's meaning.

The useful outcome was a source audit rather than a forced empirical fit. Quote counts, roots and provisional spread screens could still be studied without overstating what they established. This separated access, metadata interpretation, contract matching and numerical suitability. A solver cannot recover information that was never established in its inputs.

## 9.4 Notebook 3: smoothing required an interpretable constrained object

Clipping negative derivatives would have hidden the problem while changing mass and moments. The replacement represented probabilities directly and priced them by exact uniform-bin integration. This gave an inspectable connection between the unknowns, probability constraints and price shape. Independent integration and small known-histogram checks verified the payoff map.

Smoothing introduced another choice rather than eliminating modelling judgement. A visually attractive density could be obtained at different penalties with different price and density errors. The lesson was to report imposed properties separately from measured accuracy, and to keep the known analytical density out of the fitting objective.

## 9.5 Notebooks 4–5: good slices did not guarantee a consistent surface

Independent maturities passed their own checks but violated normalised call ordering, predominantly beyond shared quote coverage. Joining the slices in a 3D display made the family visible but did not enforce a valid relationship between them. The remedy was a joint programme, supported by an independent fit using the same solver so that solver changes were not confused with the effect of the new restrictions.

The first joint construction still missed violations between bin boundaries. The key improvement was to use the exact quadratic form of the within-bin gap: inspect endpoints and eligible interior stationary points, then add violating locations and resolve. A constructed counterexample showed that this was a necessary check, not merely a denser plotting grid. Five rounds resolved the baseline gap to the target tolerance.

The remaining tail bump was retained after the calendar checks passed. It taught a separate lesson: internal consistency constrains the admissible family, but does not establish that the selected member matches the true distribution. The subsequent work therefore examined support, resolution and risk integrals directly.

## 9.6 Notebook 6: fair sensitivity comparisons and a solver limitation

Changing the number of bins initially appeared to be a simple resolution experiment. However, the existing penalty changed strength with spacing. Deriving a grid-scaled roughness criterion and converting its coefficient made the comparisons interpretable. Nested support choices also preserved the baseline spacing, reducing avoidable confounding between support and resolution.

The two-component benchmark then exposed a numerical limitation that the simpler example had not. Raising OSQP's iteration allowance from 100,000 to 300,000 was insufficient. Objective scaling and explicit-residual attempts with that backend also failed the strict acceptance requirements. The eventual implementation used an equivalent residual formulation with Clarabel, verified against the earlier formulation on a smaller controlled case. This preserved the mathematical objective and tolerances while changing its numerical treatment.

Finally, every accepted fit could pass probability and calendar checks while giving biased far-tail estimates. The response was to include omitted benchmark mass, fixed-threshold event errors and variance rather than relying on central plots. The lesson was to distinguish numerical completion, structural validity and recovery accuracy throughout the reporting.

## 9.7 Notebook 7: repeated studies required more than additional runs

A coverage comparison could have mixed the effect of quote count with the effect of missing wings. The Sparse 41 and Central 41 patterns controlled that issue by using equal counts with different spans. Shared random draws paired comparable cases, while clean-input controls exposed errors present without noise.

Extending strikes made some clean calls so small that a fixed additive perturbation could create negative supplied prices. The price-dependent bounded amplitude in Equation (26) resolved that positivity problem without asserting full arbitrage consistency. The change and its variance were documented rather than describing the new amplitude as a standard deviation or a fitted market-noise model.

Scaling to 808 joint fits also required saved random states, complete case accounting and precise uncertainty language. Individual estimate variability, MCSE of an average and paired contrast precision were reported separately, following Morris and colleagues [16]. Completed cases could be reused only when their input and code fingerprints matched.

Numerical completion did not guarantee complete figure files. An export problem detected during artifact checks led to writing temporary PNG and SVG files, validating them and only then replacing their destinations. The lesson was that reproducibility includes the displayed evidence, not merely the numerical arrays.

## 9.8 Notebook 8: the selection target and the evaluation target diverged

The selected penalty improved some interior price predictions while worsening density recovery or extrapolation. Instead of changing the benchmark or selecting a more favourable evaluation region, the primary results were retained and a clearly labelled post-hoc inside/outside diagnostic located the discrepancy. Cawley and Talbot's distinction between selection and evaluation [17] provided the relevant framework.

Unequal fold sizes required pooling individual residuals rather than averaging fold means. The forward stress created a further interpretive risk: using each perturbed forward to redefine the event would move the threshold while claiming to measure sensitivity of the same probability. Re-expressing saved physical fits against the unchanged reference forward prevented that error. Separate uniform-distribution and integration checks verified the conversion.

The large positive-forward price errors were then investigated through the convex-payoff lower bound. This identified incompatible inputs without labelling them as solver failure. Repeated selection also expanded the audit requirements: each nonzero stress retained the exact selected parent fit, coefficient and input fingerprints.

## 9.9 Notebook 9: empirical access, inferred inputs and misleading visual agreement

Unavailable sample access and unsuitable timestamp metadata were genuine setbacks. The response was to complete and test the input process on a labelled fixture, then assess the subsequently supplied market files on their own documented terms. The eventual exchange-BBO profile did not silently relax or relabel the earlier external-curve and actual-size profile.

The supplied files contained two price families. Identifying the exchange market fields avoided fitting indicative marks as though they were observed bids and asks; recognising that the files represented two dates avoided treating three snapshots as three independent days. Indicative size entries were not converted into market depth.

Missing discount inputs were handled through an explicit quote-implied carry proxy, with feasible projections and rate-equivalent interpretation. This introduced a route for held-out information to affect predictions. Re-estimating both discount and forward inside each training fold addressed that dependency. The proxy remains an assumption-dependent estimate, not a substitute for independent rate evidence.

The weakest smoothing candidate won, and the subsequent lower grid improved the call score but left substantial put-spread misses. The primary result and post-hoc status were retained. Residual plots were also checked to ensure that a large discrepancy did not sit outside a favourable plotting range. A small fixture miss and the larger empirical misses both illustrated the same distinction between parity compatibility and the chosen density's price reproduction.

An intentionally invalid one-row fixture exposed an error in empty timestamp summaries. The adapter was changed to preserve the explicit rejection reason and unavailable extrema instead of crashing before reporting them. This corrected failure reporting without changing valid market results. The lesson was to verify rejected cases and presentation paths as well as successful calibrations.

## 9.10 Notebook 10: feasibility, finite precision and unresolved evidence

Improving the midpoint objective had not answered whether a density could satisfy both original spreads. The response separated an LP compatibility diagnostic from a hard-bound minimum-curvature estimator. The late snapshot's 120-bin failure could have been mistaken for incompatible market quotes; the feasible 240-bin representation demonstrated the importance of qualifying the result by its basis and fixed carry.

Equivalent mathematics behaved differently numerically. Physical-price rows and several objective scalings failed to reach strict status. Forward-scaled quote rows resolved the primary cases, while a further row multiplier resolved a control that had returned Solved but failed its physical-price postcheck. All unsuccessful attempts and original acceptance tolerances were retained.

One late holdout fold remains unresolved. Its LP is feasible, but the QP attempts do not meet the complete numerical rule. The reported validation coverage is therefore two of three folds. Preserving that distinction avoids both declaring an infeasible market and reporting a complete validation result that was never obtained.

Zero in-sample spread misses also did not identify the tails. Event-probability LPs quantified the remaining range within the declared family. Dated comparison introduced a further issue because fixed expiries move closer with time. The separately labelled sixty-day mixture and common-contract control made those assumptions visible, while avoiding a causal story unsupported by two dates.

The date-aware explorer required the same discipline. Shared scales support comparison; exact histogram slices expose the fitted representation; all-pair ranges disappear for common-contract refits because they no longer apply. The interactive view thus carries the scope of the calculation rather than presenting every displayed curve as equally observed.

A verification run initially inspected results while the batch was still being written and consequently saw an incomplete snapshot set and no final hash record. Waiting for completion resolved that reporting issue without changing the numerical routines. Subsequent checks covered the full batch and the browser behaviour, including offline operation and narrow-screen layouts. This reinforced the need to distinguish incomplete output from a failed scientific calculation.

## 9.11 Final assembly: retaining the evidence in a readable paper

The final assembly uses the author's engineering reports as references for typography, front matter, numbered sections, captions and author-led scholarly discussion. The research sequence follows the SPX investigation itself. Historical stage reports are integrated into one argument, with a dedicated conclusion and explicit distinction between preparation fixtures, empirical observations and subsequent diagnostics.

All forty-six equations, thirty-three figures and thirty-six research tables retain their established numbers. The symbols include units, and the front-matter lists provide page references to the finished layout. The long mathematical expressions are arranged across lines without changing their meaning. Wide scientific assets use landscape pages where necessary to preserve legibility. The original notebooks and interactive companions remain alongside the assembled document, so the paper's synthesis can be checked against the detailed record.

The first document conversion introduced duplicate image captions and empty portrait sections between adjacent landscape assets. These were removed by controlling caption generation and section boundaries. More significantly, visual inspection found that the PDF exporter mishandled empty cells in aligned native equations and omitted some lines. Single-column equation arrays preserved the complete expressions while keeping editable Word mathematics. The corrected equations were rendered and inspected again. This setback demonstrated why successful file creation and text extraction cannot replace visual verification of mathematical content.

# 10 Discussion and limitations

## 10.1 What the evidence establishes

The experiments show that a useful recovery workflow requires several distinct checks. Exact payoff integration and constrained masses address structural validity. Joint fitting and analytical interval minima address the implemented calendar restrictions. Independent residual checks address the finite-precision solution. Quote audits and original-spread tests address input interpretation and observed-price compatibility. Recovery errors, sensitivity studies and feasible event ranges address what remains uncertain about the distribution.

The synthetic results make these distinctions measurable. Clean finite differences converge, while perturbations destabilise them. Joint restrictions remove calendar violations with little change in price accuracy, but do not remove the tail mismatch. Changing resolution or coverage can materially change density error while barely changing price RMSE. Selecting smoothing by interior call prediction can improve that objective while worsening a separate density target. These findings follow from the reported experiments, rather than being general claims that one estimator always dominates another.

The empirical extension shows that hard original call/put restrictions are attainable for the three primary snapshots within the stated 240-bin family. It also shows why this success should not be overstated: the compatibility is in sample and imposed by construction, some held-out prices miss their spreads, and one validation fold remains unresolved. The reported event ranges reveal meaningful flexibility even after all primary quoted intervals are satisfied.

## 10.2 Limits of identification and probability interpretation

As Bahra emphasises [1], option-implied probabilities are risk-neutral. This paper does not estimate the change of measure required to interpret them as real-world forecasts. Market risk preferences, funding assumptions and dividend treatment are not independently identified by the density fit.

The histogram has finite support and a chosen resolution. Curvature selects one member of its feasible family but supplies no claim that the selected shape is the true terminal density. As Malz's discussion motivates [14], upper-tail integrals include extrapolated regions even when the threshold itself lies inside observed strike coverage. Conditional LP ranges improve transparency, but retain the same support, basis and point carry; they do not measure every source of uncertainty.

Synthetic truth is available only for the chosen benchmark families. The noise mechanism is deliberately simple, independent and bounded in the repeated studies. Its price-dependent amplitude is not a market microstructure calibration. Consequently, favourable recovery under those experiments is evidence within their design, not proof of general empirical reliability.

## 10.3 Limits of empirical and numerical validation

Two dates and three snapshots do not support a long historical conclusion, an event attribution or a tested forecasting strategy. The common sixty-day density is an assumed mixture of normalised maturity distributions. The common-contract control changes the inferred carry as well as sample composition. Neither comparison isolates a single causal effect.

The observed prices are documented exchange BBOs with an activity screen; actual depth and consolidated NBBO are not established. Quote-implied discounts and forwards are conditional point inputs. The selected finite grid and row-scaling retry rule followed inspected pilots, and the lower smoothing diagnostic followed the primary fit. These design decisions are disclosed so they cannot be mistaken for blind validation.

Strict numerical criteria strengthen the evidence but remain tolerance-based. Tiny signed masses and calendar residuals are retained. Feasibility LPs and QPs have different independent price-residual thresholds. The unresolved late fold demonstrates that LP compatibility and successful optimisation of the selected curvature criterion are separate outcomes. The accompanying case records make those differences reviewable.

# 11 Conclusions and future work

## 11.1 Conclusion

This project achieved its aim of developing and evaluating a reproducible route from European option prices to constrained risk-neutral terminal densities. The work progressed from a known analytical benchmark to a joint multi-maturity estimator, repeated recovery studies and an empirical SPXW application. The final method uses exact histogram payoff integration, explicit probability constraints and analytical checks of calendar gaps between the constraint locations.

The central research question can be answered conditionally. A numerically consistent density can be trusted to satisfy the restrictions that have been imposed and independently checked, within their stated tolerances. That evidence does not by itself establish accurate density recovery, identify extrapolated tails or justify a real-world probability forecast. The synthetic experiments demonstrate this directly: similar price errors can accompany different density errors, and valid calendar ordering can coexist with biased tail probabilities.

The empirical analysis resolved the original-spread problem for the three primary snapshots: all 5,518 retained option intervals were satisfied at the declared counting tolerance using the common 240-bin representation. It preserved the failed 120-bin late control, the incomplete late validation fold and the limitations of inferred carry. The feasible event ranges then showed why a single smooth density should not be presented as the only answer supported by the observed prices. In particular, a nearly zero selected upper-tail probability can coexist with a materially positive feasible upper bound.

The strongest outcome is therefore a method with an explicit account of what its evidence supports. It distinguishes valid inputs, a valid probability representation, numerical acceptance, price reproduction and distributional identification. The development record contributes to that outcome: setbacks led to interval-level checking, comparable smoothing across grids, training-only input inference, original-spread constraints and more qualified tail reporting. Unresolved issues remain visible rather than being removed from the final account.

## 11.2 Priorities for further work

The first priority is to resolve the failed late holdout fold using an independently verified numerical formulation or solver, retaining the same quotes and acceptance criteria. The comparison should establish whether a satisfactory optimum can be obtained without confusing numerical status with feasibility.

The second priority is broader empirical evidence. A predeclared sequence of dated observations, documented snapshot conventions and an independently observed discount/dividend input set would permit a stronger assessment of temporal stability. Selection and design choices should be fixed before an untouched evaluation period is examined, following the separation principle discussed by Cawley and Talbot [17].

The third priority is to broaden the uncertainty analysis. Carry, support and resolution should be varied alongside quote information, and event ranges compared across those declared families. Alternative density bases and tail treatments could determine which findings depend on the histogram representation. Such extensions should retain the distinction between conditional feasible ranges and statistical confidence intervals.

Finally, the common-horizon analysis could be extended through an explicitly estimated maturity model, checked against its economic restrictions and evaluated where observations permit. Until then, the interpolated sixty-day slice remains a useful, clearly labelled comparison convention. These extensions would build on the present work's main lesson: an interpretable result requires a transparent connection between the observations, assumptions, numerical method and claim being made.

# References

{{REFERENCES}}

# Appendix A Reproducibility and interactive companions

## A.1 Structure of the project package

The cumulative project contains all ten executed analytical notebooks, the underlying Python modules, archived inputs, numerical case records, tests, figure exports, methodological notes and the maintained development reflection. The final paper sources and build script are in `paper/`. The saved results support inspection of the reported evidence without requiring every simulation to be rerun.

The notebooks retain their original stage-specific context. Statements about what remained to be done at an earlier milestone describe that historical stage; the present paper supplies the completed synthesis. In particular, the original candidate quote audit is not reclassified as an accepted market calibration, and the preparation fixture is not relabelled as empirical data.

Input, code and result fingerprints link completed cases to their declared protocols. Random generator states and nested-strike memberships allow synthetic observations to be reconstructed. Each empirical case retains the selected rows, training and held-out membership where applicable, inferred carry, masses, solver attempts and independent diagnostics. Failed and blocked cases are part of this record.

## A.2 Interactive figures

Four offline HTML companions are supplied in `interactive/`: the independent synthetic maturity surface, the independent-versus-joint comparison, the first empirical surface and the dated empirical comparison. They can be opened in a browser after extracting the project package and do not require a live data connection. Their exact filenames are listed in the project's README.

The companions provide rotation, zoom, hover and exact maturity slices. The dated version additionally steps through the three observed snapshots, offers the common-contract control and labels the assumed sixty-day mixture separately. Visual joins between maturity rows and bin centres assist viewing; they do not introduce additional fitted observations. Static Figures 10, 14, 28 and 33 remain the paper's printable counterparts.

## A.3 Reproduction and software scope

The project README specifies its environment and entry points. The milestone builders regenerate the related analyses, figures and executed notebooks from the saved inputs. The final stage uses `build_milestone10_notebook.py`; rebuilding the paper is a separate operation and does not rerun the numerical experiments. This separation preserves the published numerical evidence while allowing document layout to be reproduced.

The recorded software includes OSQP 1.1.3, Clarabel 0.11.1, NumPy SeedSequence and PCG64, Python zoneinfo and the bundled Plotly.js 3.1.0. Software documentation supports the interfaces; the scholarly references support the mathematical relationships.

# Appendix B Attribution and reporting conventions

## B.1 Established relationships and project definitions

The valuation and density-extraction foundations are attributed to Bahra [1], Breeden and Litzenberger [6], Black and Scholes [8], and Aït-Sahalia and Lo [10]. Shape restrictions follow the discussion by Aït-Sahalia and Duarte [9]. Numerical differentiation follows Driscoll and Braun [7]; the convex-programme and regularisation framework follows Boyd and Vandenberghe [11]. Calendar ordering is used under the assumptions discussed by Gatheral and Jacquier [12]. Solver methodology is supported by Stellato and colleagues [13] and Goulart and Chen [15]. Malz [14] supports the discussion of tail extrapolation, Morris and colleagues [16] the simulation summaries, and Cawley and Talbot [17] the separation of selection from evaluation.

The bin representation, exact uniform-bin payoff coefficients, interval refinement, penalty conversions, experiment settings, empirical carry convention, finite-grid feasibility diagnostics, probability LPs and common-horizon mixture are explicitly project constructions or derivations. Cohen and colleagues [23] motivate attention to bid–ask compatibility, but their price-repair estimator is not implemented. Provider sources [2–5,18–22] support only the operational facts within their documented scope.

The full relationship-to-source map is retained in `research/references.md`. Where an original publication was not consulted in full, the bibliography identifies the consulted account. Author-led paraphrases are used throughout; no invented quotation is attributed to an author.

## B.2 Units and interpretation

Option prices, strikes and physical forwards are in index points, not dollars per contract. Normalised density coordinates are dimensionless. A probability displayed as a percentage is one hundred times its unit-interval value; an error of one percentage point is an absolute probability difference of 0.01. Density height in physical coordinates is per index point, and its integral gives probability.

RMSE against noisy fitting inputs, clean synthetic validation prices and empirical held-out midpoints describe different targets. Truth-based integrated density error is reserved for synthetic benchmarks. Distances between empirical fitted densities are descriptive comparisons. MCSE describes simulation-summary precision; sensitivity ranges and conditional feasible event ranges have their separately stated meanings. Values rounded to zero, especially far-tail probabilities, are not proofs of a zero-probability event.
