#!/usr/bin/env python3
"""Build the public research pages using only the Python standard library.

The archived scientific outputs are read, linked and never rewritten here.
Run from any directory: python scripts/build_site.py
"""

from html import escape
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "SPX Density Research"
BASE = "https://joelcerraga.github.io/SPX-Density-Research/"
REPO = "https://github.com/joelcerraga/SPX-Density-Research"
PAPER = f"{ARCHIVE}/paper/SPX-Option-Implied-Density-Final-Paper.pdf"
COVER = "SPX-Landing-Page-Thumbnail-White.jpg"

EXPLORERS = [
    {
        "title": "Synthetic maturity surface",
        "file": "density_surface.html",
        "figure": "figure_10_maturity_surface.png",
        "size": (1890, 1224),
        "tag": "Synthetic benchmark",
        "meta": "01 / Notebook 4 · Eight maturities",
        "description": "Compare estimated densities with a known analytical benchmark. Move through maturities from 30 to 365 days and inspect the linked histogram slices.",
        "alt": "Saved synthetic density surface across eight maturities, from Figure 10",
    },
    {
        "title": "Joint maturity calibration",
        "file": "joint_density_surface.html",
        "figure": "figure_14_joint_maturity_surface.png",
        "size": (1890, 1224),
        "tag": "Calendar consistency",
        "meta": "02 / Notebook 5 · Eight maturities",
        "description": "Compare independent fits with a family of densities calibrated together. See how calendar constraints change consistency across maturities.",
        "alt": "Saved jointly calibrated synthetic density surface, from Figure 14",
    },
    {
        "title": "First empirical surface",
        "file": "empirical_density_surface.html",
        "figure": "figure_28_market_density_surface.png",
        "size": (1835, 1224),
        "tag": "Market observations",
        "meta": "03 / Notebook 9 · 18 September 2026",
        "description": "Explore the first SPXW market case across three expiries. Compare fitted density slices and smoothing choices from the original empirical experiment.",
        "alt": "Saved first empirical SPXW density surface for 18 September 2026, from Figure 28",
    },
    {
        "title": "Dated density comparisons",
        "file": "dated_density_surface.html",
        "figure": "figure_33_dated_density_surfaces.png",
        "size": (2592, 882),
        "tag": "Final empirical study",
        "meta": "04 / Notebook 10 · Three observed snapshots",
        "description": "Compare 31 August and two 18 September observations. Inspect a fixed expiry or an assumed 60-day mixture, with conditional probability ranges.",
        "alt": "Three saved empirical density surfaces for the dated comparison, from Figure 33",
    },
]


def local(path, prefix=""):
    url = prefix + quote(path, safe="/#")
    if path == PAPER:
        # A new author-supplied PDF must not reuse a reader's cached old version.
        version = hashlib.sha256((ROOT / PAPER).read_bytes()).hexdigest()[:12]
        url += f"?v={version}"
    return url


def share_image_url():
    version = hashlib.sha256((ROOT / COVER).read_bytes()).hexdigest()[:12]
    return f"{BASE}{COVER}?v={version}"


def github(path, directory=False):
    return f"{REPO}/{'tree' if directory else 'blob'}/main/{quote(path, safe='/')}"


def shell(title, description, body, *, gallery=False):
    prefix = "../" if gallery else ""
    canonical = BASE + ("explorers/" if gallery else "")
    overview = "" if gallery else ' aria-current="page"'
    graphs = ' aria-current="page"' if gallery else ""
    css_version = hashlib.sha256((ROOT / "assets/site.css").read_bytes()).hexdigest()[:12]
    js_version = hashlib.sha256((ROOT / "assets/site.js").read_bytes()).hexdigest()[:12]
    share_image = share_image_url()
    return f'''<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{escape(title)} | Joel Cerraga</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="author" content="Joel Cerraga">
  <meta name="theme-color" content="#102b3e">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="SPX Density Research">
  <meta property="og:title" content="{escape(title, quote=True)}">
  <meta property="og:description" content="{escape(description, quote=True)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{share_image}">
  <meta property="og:image:secure_url" content="{share_image}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1774">
  <meta property="og:image:height" content="887">
  <meta property="og:image:alt" content="SPX Density Explorer by Joel Cerraga, with conceptual teal surface artwork on white">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title, quote=True)}">
  <meta name="twitter:description" content="{escape(description, quote=True)}">
  <meta name="twitter:image" content="{share_image}">
  <meta name="twitter:image:alt" content="SPX Density Explorer by Joel Cerraga, with conceptual teal surface artwork on white">
  <link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg">
  <link rel="stylesheet" href="{prefix}assets/site.css?v={css_version}">
  <script src="{prefix}assets/site.js?v={js_version}" defer></script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap nav-inner">
    <a class="brand" href="{prefix}index.html"><img class="brand-mark" src="{prefix}assets/favicon.svg" width="34" height="34" alt=""><span>SPX Density Research<small>Joel Cerraga</small></span></a>
    <button class="nav-toggle" type="button" aria-controls="site-nav" aria-expanded="false">Menu</button>
    <nav class="nav-links" id="site-nav" aria-label="Main navigation">
      <a href="{prefix}index.html"{overview}>Overview</a>
      <a href="{prefix}explorers/"{graphs}>Interactive graphs</a>
      <a href="{local(PAPER, prefix)}">Paper ↗</a>
      <a href="{REPO}">GitHub ↗</a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <p>Joel Cerraga · Quantitative research · 2026</p>
    <div class="footer-links">
      <a href="{prefix}explorers/">Interactive graphs</a>
      <a href="{local(PAPER, prefix)}">Final paper</a>
      <a href="{REPO}">Source &amp; reproduction</a>
    </div>
  </div>
</footer>
</body>
</html>
'''


def cards(items, prefix=""):
    html = []
    for item in items:
        width, height = item["size"]
        html.append(f'''<a class="graph-card" href="{local(f'{ARCHIVE}/interactive/{item["file"]}', prefix)}">
  <div class="card-image">
    <img src="{local(f'{ARCHIVE}/figures/{item["figure"]}', prefix)}" width="{width}" height="{height}" alt="{escape(item['alt'])}" loading="lazy">
    <span class="card-tag">{item['tag']}</span>
  </div>
  <div class="card-body">
    <p class="card-meta">{item['meta']}</p>
    <h3>{item['title']}</h3>
    <p>{item['description']}</p>
    <div class="card-bottom"><span>Open explorer</span><span aria-hidden="true">↗</span></div>
  </div>
</a>''')
    return '<div class="card-grid">\n' + "\n".join(html) + "\n</div>"


BAHRA = '''<p>Bahra, B. (1997) <em>Implied risk-neutral probability density functions from option prices: theory and application</em>. Bank of England Working Paper No. 66. Available at: <a href="https://www.bankofengland.co.uk/working-paper/1997/implied-risk-neutral-probability-density-functions-from-option-prices">https://www.bankofengland.co.uk/working-paper/1997/implied-risk-neutral-probability-density-functions-from-option-prices</a> (Accessed: 28 September 2026).</p>'''


def references(full=True):
    entries = BAHRA
    if full:
        entries = '''<p>Aït-Sahalia, Y. and Duarte, J. (2003) ‘Nonparametric option pricing under shape restrictions’, <em>Journal of Econometrics</em>, 116(1–2), pp. 9–47. doi: <a href="https://doi.org/10.1016/S0304-4076(03)00102-7">10.1016/S0304-4076(03)00102-7</a>.</p>''' + BAHRA + '''<p>Breeden, D.T. and Litzenberger, R.H. (1978) ‘Prices of State-Contingent Claims Implicit in Option Prices’, <em>The Journal of Business</em>, 51(4), pp. 621–651. doi: <a href="https://doi.org/10.1086/260618">10.1086/260618</a>.</p>'''
    return f'<div class="wrap section"><section class="references" aria-label="References"><h2>References</h2>{entries}</section></div>'


def landing():
    metrics = json.loads((ROOT / ARCHIVE / "results/comparison_display_metrics.json").read_text())
    quote_count = f"{metrics['primary_spread_quote_count']:,}"
    outside_count = metrics["primary_outside_count"]
    body = f'''
<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">Option prices · Constrained inference</p>
      <h1>SPX Option-Implied<br><span>Density Research</span></h1>
      <p class="lede">Recovering risk-neutral distributions from option prices, from analytical benchmarks to empirical comparisons and interactive 3D surfaces.</p>
      <div class="button-row"><a class="button" href="explorers/">Explore the graphs <span aria-hidden="true">↗</span></a><a class="button secondary" href="{local(PAPER)}">Read the paper</a></div>
      <p class="hero-note">Research by Joel Cerraga · Ten completed analytical notebooks</p>
    </div>
    <figure class="hero-visual">
      <img src="{local(f'{ARCHIVE}/figures/figure_28_market_density_surface.png')}" width="1835" height="1224" alt="First empirical SPXW density surface across three expiries, saved as Figure 28 in Notebook 9" fetchpriority="high">
      <figcaption class="visual-label"><span>FIRST EMPIRICAL SURFACE / NOTEBOOK 9</span><span>18 SEP 2026</span></figcaption>
    </figure>
  </div>
</section>
<div class="wrap"><div class="stat-strip">
  <div class="stat"><strong>10</strong><span>completed analytical notebooks</span></div>
  <div class="stat"><strong>4</strong><span>interactive density explorers</span></div>
  <div class="stat"><strong>3</strong><span>observed snapshots on two dates</span></div>
  <div class="stat"><strong>{quote_count}</strong><span>option prices in the primary fits</span></div>
</div></div>
<section class="section" id="method">
  <div class="wrap question-grid">
    <div>
      <p class="eyebrow">The research question</p>
      <h2>What distribution is implied by option prices?</h2>
      <p>Breeden and Litzenberger (1978), in <em>Prices of State-Contingent Claims Implicit in Option Prices</em>, relate the curvature of call prices across strikes to state-contingent prices. This study uses that relationship as its starting point, then asks how much the recovered density depends on the data and constraints.</p>
      <p>As Bahra (1997) explains in <em>Implied risk-neutral probability density functions from option prices</em>, the resulting distribution is risk-neutral: it describes valuation under the pricing assumptions, rather than the actual frequency of future outcomes.</p>
    </div>
    <div class="method-list">
      <div class="method-item"><span class="method-num">01</span><div><h3>Establish a known benchmark</h3><p>Start with analytical option prices and a known density. Test finite-difference recovery, grid refinement and repricing before introducing noisy observations.</p></div></div>
      <div class="method-item"><span class="method-num">02</span><div><h3>Constrain the inferred distribution</h3><p>Estimate nonnegative bin probabilities with unit mass and the required forward mean. Fit maturities together and check calendar consistency throughout each strike interval.</p></div></div>
      <div class="method-item"><span class="method-num">03</span><div><h3>Challenge the fit</h3><p>Vary support, resolution, smoothing and inferred carry. Compare original price spreads, held-out contracts and conditional tail ranges across the observed snapshots.</p></div></div>
    </div>
  </div>
  <div class="wrap"><p class="method-context">As Aït-Sahalia and Duarte (2003) show in <em>Nonparametric option pricing under shape restrictions</em>, economic restrictions on the pricing function matter for density estimation. Here those restrictions are implemented through a constrained histogram model with exact bin-payoff integration.</p></div>
</section>
<section class="section tinted" id="findings">
  <div class="wrap question-grid">
    <div>
      <p class="eyebrow">Final empirical study / Notebook 10</p>
      <h2>A compatible price fit. A density that remains uncertain.</h2>
      <p>The three primary 240-bin fits accommodate the retained call and put spreads. That compatibility is imposed during fitting; it does not independently demonstrate that the estimated density is accurate.</p>
      <p>Held-out checks still contain spread misses, one late-snapshot validation fold remains numerically unresolved, and feasible tail probabilities can differ substantially from the chosen smooth estimate.</p>
      <p><a class="text-link" href="{github(f'{ARCHIVE}/research/comparison_methodology.md')}">Read the final methodology <span aria-hidden="true">↗</span></a></p>
    </div>
    <div class="result-box">
      <h3>Original option-price intervals</h3>
      <p class="muted small">Three primary 240-bin fits · 31 August and 18 September 2026</p>
      <div class="result-numbers">
        <div class="result-number"><strong>{quote_count}</strong><span>retained option prices</span></div>
        <div class="result-number"><strong>{outside_count}</strong><span>outside their original spreads</span></div>
      </div>
      <p class="result-note">In-sample result at a counting tolerance of 10<sup>−7</sup> index points. Conditional probability ranges describe compatible densities under fixed assumptions; they are not confidence intervals.</p>
      <a class="text-link" href="{local(f'{ARCHIVE}/interactive/dated_density_surface.html')}">Inspect the dated explorer <span aria-hidden="true">↗</span></a>
    </div>
  </div>
</section>
<section class="section" id="graphs">
  <div class="wrap">
    <div class="section-heading"><div><p class="eyebrow">Interactive research</p><h2>Four views of the density.</h2></div><p>Start with known synthetic distributions, then explore the observed market cases.</p></div>
    {cards(EXPLORERS)}
    <div class="section-end"><p class="graph-hint">Previews are the saved research figures. Each explorer includes its own controls, interpretation and limitations.</p><a class="text-link" href="explorers/">Visit the graph gallery <span aria-hidden="true">↗</span></a></div>
  </div>
</section>
<section class="section tinted" id="resources">
  <div class="wrap">
    <div class="section-heading"><div><p class="eyebrow">Read. Inspect. Reproduce.</p><h2>The complete research record.</h2></div></div>
    <div class="resource-grid">
      <article class="resource"><h3>The final paper</h3><p>The derivations, numbered figures and equations, empirical results, development lessons and conclusion in one report.</p><a href="{local(PAPER)}">Open the PDF ↗</a></article>
      <article class="resource"><h3>Code and notebooks</h3><p>Ten analytical notebooks, Python experiment runners, numerical checks and saved figures, tables and result files.</p><a href="{github(ARCHIVE, directory=True)}">Browse the research files ↗</a></article>
      <article class="resource"><h3>Decisions and setbacks</h3><p>How data limitations, unstable derivatives and numerical failures shaped the study, including the unresolved cases.</p><a href="{github(f'{ARCHIVE}/research/development_reflection.md')}">Read the development record ↗</a></article>
    </div>
    <div class="callout scope-note"><p><strong>Scope of the evidence.</strong> The final comparison contains three SPXW snapshots on two dates, with three expiries per snapshot. Carry is inferred from matched calls and puts; executable market depth is unavailable. The 60-day comparison assumes a mixture of normalised marginal distributions. These observations do not establish forecasting accuracy or a trading advantage.</p></div>
  </div>
</section>
{references()}
'''
    return shell("SPX Option-Implied Density Research", "Joel Cerraga's research into SPX option-implied risk-neutral densities. Explore the final paper, ten analytical notebooks, empirical findings and four interactive 3D graphs.", body)


def gallery():
    prefix = "../"
    body = f'''
<section class="page-intro">
  <div class="wrap">
    <div class="breadcrumb"><a href="../index.html">Research overview</a><span aria-hidden="true">/</span>Interactive graphs</div>
    <div class="catalog-intro">
      <div><p class="eyebrow">The interactive companion</p><h1>Explore the<br><span class="teal">density surfaces.</span></h1><p class="lede">Four ways to inspect the research, from known synthetic densities to comparisons across observed SPXW snapshots.</p><div class="tag-row"><span class="tag">4 explorers</span><span class="tag">Linked 3D and 2D views</span><span class="tag">Self-contained HTML</span></div></div>
      <figure class="cover-figure"><img src="../{COVER}" width="1774" height="887" alt="Conceptual cover artwork for SPX Density Explorer, by Joel Cerraga"><figcaption>Conceptual cover artwork. The previews below are saved research figures.</figcaption></figure>
    </div>
  </div>
</section>
<section class="section gallery-section" id="synthetic">
  <div class="wrap">
    <div class="section-heading"><div><p class="eyebrow">01–02 / Controlled experiments</p><h2>Begin with a known distribution.</h2></div><p>These explorers sweep across maturities at one synthetic valuation setup.</p></div>
    {cards(EXPLORERS[:2], prefix)}
    <p class="graph-hint">“Joint” means that the marginal densities are calibrated together across maturities. It does not mean that a joint distribution of future price paths has been estimated.</p>
  </div>
</section>
<section class="section tinted" id="empirical">
  <div class="wrap">
    <div class="section-heading"><div><p class="eyebrow">03–04 / Market observations</p><h2>Then examine the empirical cases.</h2></div><p>The first market surface and the final comparison retain their separate research contexts.</p></div>
    {cards(EXPLORERS[2:], prefix)}
    <p class="graph-hint">The dated explorer plays only the three observed snapshots. The common 60-day view uses an assumed mixture across maturities, with no invented observation dates.</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="read-grid">
      <div><p class="eyebrow">How to read the graphs</p><h2>Look at the slices as well as the surface.</h2><p>Drag to rotate, scroll to zoom and hover for values. Use each explorer’s maturity or observation controls to update its linked slice.</p><ul><li><strong>Terminal level:</strong> the synthetic explorers use index points. The empirical explorers divide by each expiry’s inferred forward; a value of 1 is at that forward.</li><li><strong>Density height:</strong> probability is an area under the density over a range, rather than the height at one point.</li><li><strong>Surface joins:</strong> connecting facets aid viewing. They do not establish fitted densities at every intermediate maturity.</li></ul></div>
      <div><p class="eyebrow">How to interpret the evidence</p><h2>Keep the pricing measure in view.</h2><p>As Bahra (1997) explains in <em>Implied risk-neutral probability density functions from option prices</em>, these densities are inferred under a risk-neutral pricing measure. Their probabilities are not direct forecasts of actual market outcomes.</p><p>The final explorer’s feasible ranges hold the bin support, inferred carry and selected quotes fixed. Read them alongside the retained held-out errors and unresolved numerical fold.</p><div class="detail-links"><a href="{local(PAPER, prefix)}">Read the paper ↗</a><a href="{github(f'{ARCHIVE}/research/comparison_methodology.md')}">Final methodology ↗</a></div></div>
    </div>
    <div class="callout scope-note"><p><strong>Viewing the explorers.</strong> Each opens as a standalone page with its plotting code and data included, so a downloaded copy also works offline. The 3D panels need a browser with WebGL support. Static previews and the final paper remain available above.</p></div>
  </div>
</section>
{references(full=False)}
'''
    return shell("SPX Density Explorer | Interactive Graphs", "Explore four interactive SPX density graphs: synthetic maturity surfaces, joint calibration, the first empirical surface and comparisons across three observed snapshots.", body, gallery=True)


def build():
    pages = {"index.html": landing(), "explorers/index.html": gallery()}
    for name, html in pages.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{BASE}</loc></url>
  <url><loc>{BASE}explorers/</loc></url>
</urlset>
''', encoding="utf-8")
    print("Built index.html, explorers/index.html and sitemap.xml.")


if __name__ == "__main__":
    build()
