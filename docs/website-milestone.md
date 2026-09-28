# Website milestone — research landing page and graph gallery

Date: 28 September 2026.

## Goal

Create an SPX research landing page in the same white, navy and teal style as the Market-Neutral Trading Algorithm site, with a separate gallery for the four existing interactive graphs.

## Changes

- Replaced the root graph directory with a research overview, methods, empirical findings, graph previews, paper and code links, development record and Harvard references.
- Added `explorers/index.html`, separating synthetic benchmarks from market observations and explaining the axes and interpretation of the graphs.
- Added shared responsive CSS, keyboard-accessible navigation, social metadata, a favicon, sitemap and a root README.
- Reused the existing cover artwork and the saved scientific figures. The cover is explicitly described as conceptual; graph previews use research outputs.
- Added a deterministic, standard-library page builder and a focused static verifier. The numerical research pipeline is separate.

## Decisions, setbacks and mitigation

| Decision or setback | Response | Outcome or remaining limit |
| --- | --- | --- |
| The old homepage was a graph directory, without an overview of the research. | Build an overview and a dedicated gallery, with prominent links between them. | Visitors can read the findings before opening an explorer. |
| Existing papers and external links already target the original graph files. | Link to the original standalone explorers and leave the scientific archive byte-for-byte unchanged. | Existing graph URLs, embedded data and paper references remain valid. |
| Notebook 9 and Notebook 10 describe different empirical stages. | Label the first market surface by notebook and date; place the final primary-fit counts in a separate Notebook 10 findings section. | Earlier previews are not presented as the final empirical fit. |
| Zero primary spread violations could be mistaken for independent validation. | Place the imposed in-sample constraint, tolerance, held-out misses and unresolved fold alongside the result. | The presentation distinguishes price compatibility from density accuracy. |
| Maturity sweeps, observed dates and a 60-day mixture are different comparisons. | Name the comparison in each card and explain the assumed mixture in the gallery. | No synthetic maturity sweep is described as historical animation. |
| The synthetic and empirical explorers use different terminal-level units. | Check the archived plotting templates and describe index points separately from forward-normalised levels. | The gallery guidance follows the actual axes in each explorer. |
| A returning browser retained the stylesheet from the first deployment after a visual correction. | Add content-derived version queries to stylesheet and navigation-script URLs in the deterministic builder. | Updated asset contents receive new URLs; unchanged contents retain stable URLs. |
| Local browser previews were blocked by the available browser environment. | Perform static checks before publication, then inspect the published GitHub Pages site. | Public-page inspection is recorded separately from local structural checks. |
| The available browser environment does not support WebGL. | Preserve the existing explorer code and provide saved static previews; check navigation and accessible controls where available. | Do not claim a fresh 3D rotation or zoom check. The research archive retains its original browser-validation records. |

## Validation scope

`python scripts/verify_site.py` checks generated-page consistency, all local page/asset/fragment links, image descriptions and dimensions, canonical URLs, social metadata, graph destinations and displayed primary result counts. With the release base commit available locally, it also verifies the archived research files and original cover against their recorded Git blob hashes.

Website verification does not rerun numerical experiments or establish new empirical findings. The retained research checks and browser records belong to their documented original handoffs.

## Recorded website checks

- Generated both pages with `python scripts/build_site.py`; the build-consistency and static checks pass.
- Checked 47 local link occurrences and 12 image occurrences across the two pages. Image alternatives, dimensions, original graph destinations, canonical URLs and primary result counts passed.
- Verified 1,339 archived files, including the original cover, against baseline commit `6a0cd7c658b337f9ccc53eca2f423e4e77b2c325`; all remain byte-for-byte unchanged.
- `node --check assets/site.js` passes.
- GitHub Pages successfully deployed website commit `5ef228df5c2b18dae778f140762c3b351895fc74`.
- Inspected both public pages in the available 1,348-pixel desktop viewport: no horizontal overflow or broken images. Followed the landing-page button to the gallery and the dated-comparison card to its original explorer.
- In the dated explorer, selecting 31 August and the interpolated 60-day horizon updated the status, 2D comparison heading and probability table. Its 3D panel reported that this browser lacks WebGL; rotation and zoom were not revalidated.
- All four standalone graph URLs and the final PDF returned HTTP 200, with the expected HTML/PDF content types.
- Reviewed the responsive CSS breakpoints. A fresh mobile-browser rendering check was not available in this environment.

The final follow-up clarifies the empirical smoothing description and synthetic-axis units, aligns card metadata, and records these checks. A [landing-page screenshot](../assets/previews/landing-page.jpg) captures the published hero and overview statistics.
