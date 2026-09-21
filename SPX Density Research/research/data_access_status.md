# Market-data access decision record

**Current status through Notebook 10:** the first empirical case and three-snapshot comparison are complete using a separately documented exchange-BBO profile and quote-implied carry. The original candidate remains unapproved. The earlier access failures below are historical records, not a claim that the newly supplied dataset is unusable. See [marking_methodology.md](marking_methodology.md) and `data/raw/marking_prices/source_verification.json`.

## Status at the Milestone 3 handoff

No observation datetime has been approved for empirical calibration. The original page payload and its provenance remain unchanged in `data/raw/`.

During the preceding feed check, the public [Cboe SPX JSON endpoint](https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json) returned HTTP 200, 27,782 option records and the string `2026-09-19 17:58:02` under `timestamp`. A direct comparison reported the option-record array identical to the earlier stored page payload. Bid/ask size fields were still zero throughout. These observations are recorded from that check; this document is not a copy of the endpoint response or an independently reproducible capture of its metadata.

A date in the payload improves the available metadata but does not establish its timezone or whether it marks generation, collection or quote observation. The preceding underlying last-trade field is not a substitute. No undocumented interpretation is used to calculate an expiry horizon.

## Minimum evidence needed before the first market fit

- The source's documented full quote observation date, time and timezone.
- The interpretation of zero or unavailable size fields, with the resulting limitations stated.
- A chosen European contract set with a verified settlement convention and settlement datetime.
- Consistent bid/ask quotes at matched strikes, plus sufficient strike coverage.
- A documented discount factor and forward estimate, with parity and sensitivity checks.
- Terms permitting the intended research use and a separate decision on public redistribution.

The synthetic fitter accepts forward and discount inputs; it does not establish these data requirements automatically. Passing its numerical constraints must not be used to bypass the data decision.

## Reassessment on 21 September 2026: Notebook 9 preparation

Cboe's [Option EOD Summary product page](https://datashop.cboe.com/option-eod-summary) advertises a public sample and links its [v1.1 layout](https://datashop.cboe.com/documents/Option_EOD_Summary_Layout.pdf). The sample request at `https://datashop.cboe.com/download/sample/217` returned HTTP 403. The failed request is recorded in `data/raw/cboe_eod_sample/retrieval.json`; no ZIP contents were obtained or inspected. The documented product remains a possible input source, not an acquired dataset. Its early-close timing exception must be respected when interpreting the snapshot fields [18].

The primary [HistoricalData.net options documentation](https://historicaldata.net/options.html) describes its public July–December 2022 sample as last-standing quotes, not synchronised snapshots. It says per-option quote timestamps are available only from 6 August 2026. Consequently, the advertised sample does not meet this study's observation-time requirement and was not downloaded. This is a decision about suitability for the defined study, not a general judgment of the vendor [19].

WRDS's [OptionMetrics product description](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/optionmetrics/) identifies an institutional route to option and curve data. No institutional access, export or applicable source specification has been supplied here [20]. No paid access was initiated. These checks did not establish a usable empirical input; they are not an exhaustive claim that no suitable dataset exists.

The next input is an existing authorised SPX/SPXW quote export plus its observation, settlement and curve documentation. The [input guide](empirical_input_guide.md), empty templates and `run_market_calibration.py` make that next step concrete. The implementation records source evidence, tests metadata consistency, audits matched pairs, checks forward intervals and excludes unavailable discount information. Passing those software checks does not independently authenticate a source.

The only newly calibrated data are the explicitly synthetic fixtures in `data/fixtures/empirical/`. The original candidate remains unchanged, and **empirical calibration has not been performed**. Notebook 9 is in progress, with its preparation work validated.

## Supplied marking-price files: empirical access resolved for a limited case

The three supplied CSVs independently match Cboe's advertised downloads [21]. Their archived dates are 31 August and 18 September 2026; the latter has 15:00 and 15:15 CT snapshots. The first case uses actual exchange bid/ask columns for three reviewed SPXW maturities, with the source fields, dates, OSI identifiers and contract conventions checked. All 969 retained pairs admit the fitted parity inputs. Actual market depth remains unavailable and the discount is inferred, not sourced from an independent curve.

This acceptance is specific to the documented profile and its limitations. The original JSON and uninspected commercial sample are not reclassified. `results/marking_input_audit.json` retains exclusions; `results/marking_calibration.json` and the separately labelled range diagnostic retain numerical evidence. The observed spread misses, quote-derived inputs and extrapolated tails remain research limitations. No purchase, account creation or public release occurred.

## Notebook 10: comparison using the accepted files

The same three unchanged CSVs now support all-pair and common-contract comparisons at three expiries, paired-strike holdouts and assumed 60-day normalised mixtures. This adds no new data source or permission claim. The retained counts are 840, 969 and 950 matched pairs for August, standard September and late September respectively. Original-spread hard-bound fits are feasible on the common 240-bin representation, with conditional tail ranges and unresolved validation limits reported in [comparison_methodology.md](comparison_methodology.md). The original candidate remains an audit example. Two dates do not constitute a long historical sample.
