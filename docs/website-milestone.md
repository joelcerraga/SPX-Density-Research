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
| Local browser previews were blocked by the available browser environment. | Perform static checks before publication, then inspect the published GitHub Pages site. | Public-page inspection is recorded separately from local structural checks. |
| The available browser environment does not support WebGL. | Preserve the existing explorer code and provide saved static previews; check navigation and accessible controls where available. | Do not claim a fresh 3D rotation or zoom check. The research archive retains its original browser-validation records. |

## Validation scope

`python scripts/verify_site.py` checks generated-page consistency, all local page/asset/fragment links, image descriptions and dimensions, canonical URLs, social metadata, graph destinations and displayed primary result counts. With the release base commit available locally, it also verifies the archived research files and original cover against their recorded Git blob hashes.

Website verification does not rerun numerical experiments or establish new empirical findings. The retained research checks and browser records belong to their documented original handoffs.

Live deployment checks will be recorded after publication.
