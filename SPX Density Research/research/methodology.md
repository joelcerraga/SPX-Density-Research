# Recovering an option-implied probability density
## Milestone 1: a controlled synthetic benchmark
Joel Cerraga | Quant research project | Development version 0.1

**Status:** synthetic validation completed; empirical SPX analysis has not yet begun. All inputs are illustrative, not observed market values.

The preliminary objective is to establish whether numerical differentiation of European call prices recovers a known terminal distribution. This allows numerical errors to be assessed before introducing discrete, noisy market quotes. The notebook accompanies `research/methodology.md`.

### 1. What are we recovering?
A call pays $\max(S_T-K,0)$ at expiry. Here, $S_T$ is the terminal index level, $K$ is the strike and $T$ is time to expiry in years. A density is not the probability of a single exact outcome: integrating it over an interval gives that interval's probability.

As Bahra (1997) explains in his Bank of England working paper [1], a European call can be valued by discounting its expected payoff under the risk-neutral distribution. Under deterministic interest rates and a continuous density, this gives Equation (1):
$$C(K,T)=e^{-rT}\int_K^\infty(s-K)f_Q(s;T)\,ds.\tag{1}$$
Following the option-price differentiation approach discussed by Bahra [1], differentiating Equation (1) once with respect to strike gives Equation (2):
$$\frac{\partial C}{\partial K}=-e^{-rT}\int_K^\infty f_Q(s;T)\,ds.\tag{2}$$
The boundary term vanishes because the payoff is zero at $s=K$. Breeden and Litzenberger (1978) established the extraction relationship [6]; following its derivation in Bahra [1], differentiating Equation (2) again gives Equation (3):
$$f_Q(K;T)=e^{rT}\frac{\partial^2C}{\partial K^2}.\tag{3}$$
As Bahra [1] emphasises, the recovered probabilities are risk-neutral pricing probabilities, rather than direct real-world forecasts. Differentiation is across strikes at a fixed maturity and observation date.

### 2. Controlled experiment
Black and Scholes (1973) derive option valuation from a no-arbitrage argument [8]. As Bahra [1] explains, the corresponding constant-volatility benchmark has a lognormal terminal distribution. We use this model as a known answer. The continuous-dividend adjustment used in the code is consistent with the spot–forward relationship set out by Aït-Sahalia and Lo (1998), Equation (16) [10]. This is an implementation check, not a claim that SPX returns follow this model. Spot = 6,000; annual continuously compounded rate = 4%; dividend yield = 1.5%; annual volatility = 20%; maturity = 0.5 years.

### 3. Price the calls and recover the density
As Driscoll and Braun explain in *Fundamentals of Numerical Computation*, §5.4 [7], a second derivative can be approximated using a three-point centred difference. For equally spaced strikes separated by $h$, applying their Equation (5.4.9) to Equation (3) gives Equation (4):
$$\widehat f_Q(K_i)=e^{rT}\frac{C(K_i+h)-2C(K_i)+C(K_i-h)}{h^2}.\tag{4}$$
The Taylor-expansion argument described by Driscoll and Braun, §5.5 [7], gives a truncation error of order $h^2$ for Equation (4), provided the price function is sufficiently smooth. We exclude grid endpoints, where a centred stencil is unavailable. No clipping of negative values or renormalisation is performed.

As shown in Figure 2, the density is concentrated near the initial index level and has a longer right tail in index-level coordinates. This shape follows from the assumed lognormal model; it is not an empirical finding about current markets. Bahra’s Mathematical appendix identifies the forward with the risk-neutral mean [1]; it should not be confused with the mode.

### 4. Convergence and failure modes
The grid is refined from 80 to 5 index points. The integrated absolute error measures total disagreement between recovered and analytical densities. Figure 3 compares the observed error with the second-order convergence expected from Equation (4).

Figure 4 introduces independent zero-mean quote perturbations with a standard deviation of 0.05 index points and seed 42. These errors need not preserve arbitrage constraints. Applying Equation (4) amplifies their effect through division by the squared strike spacing. This is an algebraic consequence of the stencil in Driscoll and Braun [7], rather than a calibrated model of market noise. The stress test deliberately shows the consequence of applying raw differences to inconsistent quotes; it is not a fitted market-noise model.

### 5. Interpretation and next stage
This experiment validates the clean-data implementation within the tested settings. It does not validate a method for real quotes. Finite support leaves unobserved tail mass; here the range is broad enough for the stated tolerances. As Driscoll and Braun discuss in §5.5 [7], reducing the step size can eventually increase roundoff error through subtractive cancellation.

The next stage will assess accessible SPX quotes, document timestamp and settlement conventions, and choose a shape-constrained fitting method. Aït-Sahalia and Duarte (2003) show why monotonicity and convexity restrictions matter when estimating option-price curves [9]. This motivates our planned constrained fit; their particular estimator has not yet been implemented. Quote cleaning, forward consistency and tail treatment remain separate requirements. Clipping negative densities cannot substitute for addressing inconsistent input prices.

### Table 1. Measured baseline validation

| Metric | Result |
|---|---:|
| mass | 0.9999999985 |
| minimum_density | 3.649747692e-12 |
| negative_density_count | 0 |
| integrated_absolute_error | 2.914825705e-06 |
| first_moment | 6075.470692 |
| theoretical_forward | 6075.470709 |
| forward_relative_error | 2.895368748e-09 |
| max_repricing_error_index_points | 1.099256224e-05 |

### Figure register

![Research plot](../figures/figure_01_call_prices.png)

Figure 1. Synthetic European call prices across strikes for a six-month expiry, using an illustrative initial index level of 6,000 and constant annual volatility of 20%.

![Research plot](../figures/figure_02_density_recovery.png)

Figure 2. Analytical lognormal density and density recovered from synthetic call-price curvature. The dashed vertical line identifies the theoretical forward of 6,075.47. The recovered and analytical curves nearly coincide.

![Research plot](../figures/figure_03_convergence.png)

Figure 3. Integrated absolute density error against strike spacing. The measured error follows approximately second-order convergence over the tested grid spacings.

![Research plot](../figures/figure_04_noise_sensitivity.png)

Figure 4. Density recovered after adding independent, zero-mean quote noise with a standard deviation of 0.05 index points (seed 42). Negative estimates demonstrate the sensitivity of raw second differences to quote errors.

### Numerical boundary decision

An initial grid starting at 1,000 index points produced tiny negative second differences in the far left tail due to subtraction of nearly linear call prices. The validated grid therefore spans 2,500 to 14,000 with spacing 5; its density is evaluated on interior points from 2,505 to 13,995. This choice reduces cancellation while retaining essentially all benchmark mass. No negative values were clipped. This model-specific boundary choice must not be transferred automatically to market data.


### References

[1] B. Bahra (1997), “Implied risk-neutral probability density functions from option prices: theory and application,” Bank of England, Working Paper No. 66. Sections 2.1–2.2 and Mathematical appendix. [Full paper](https://www.bankofengland.co.uk/-/media/boe/files/working-paper/1997/implied-risk-neutral-probability-density-functions-from-option-prices.pdf).

[6] D. T. Breeden and R. H. Litzenberger (1978), “Prices of State-Contingent Claims Implicit in Option Prices,” *The Journal of Business*, vol. 51, no. 4, pp. 621–651. [doi:10.1086/260618](https://doi.org/10.1086/260618). Original attribution; the derivation was consulted through Bahra [1] and Aït-Sahalia and Lo [10].

[7] T. A. Driscoll and R. J. Braun, *Fundamentals of Numerical Computation*, author-maintained online textbook, §§5.4–5.5. [Finite differences, especially Equation (5.4.9)](https://fncbook.com/finitediffs/); [Convergence and roundoff](https://fncbook.com/fd-converge/). Accessed 19 September 2026.

[8] F. Black and M. Scholes (1973), “The Pricing of Options and Corporate Liabilities,” *Journal of Political Economy*, vol. 81, no. 3, pp. 637–654. [doi:10.1086/260062](https://doi.org/10.1086/260062). Publisher abstract and metadata consulted; the lognormal implementation is supported by [1] and [10].

[9] Y. Aït-Sahalia and J. Duarte (2003), “Nonparametric option pricing under shape restrictions,” *Journal of Econometrics*, vol. 116, nos. 1–2, pp. 9–47. Section 2. [doi:10.1016/S0304-4076(03)00102-7](https://doi.org/10.1016/S0304-4076(03)00102-7); [author-hosted paper](https://www.princeton.edu/~yacine/cnvx.pdf).

[10] Y. Aït-Sahalia and A. W. Lo (1998), “Nonparametric Estimation of State-Price Densities Implicit in Financial Asset Prices,” *The Journal of Finance*, vol. 53, no. 2, pp. 499–547. Sections I and III.A, especially Equations (16)–(17). [Author-hosted paper](https://www.princeton.edu/~yacine/aslo.pdf).
