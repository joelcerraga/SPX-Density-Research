"""Documented quote bundles, bid–ask parity checks and conditional calibration.

Passing software checks establishes internal consistency, not source authenticity.
Market bundles additionally require an explicit, attributable source review.
See research/empirical_input_guide.md and Equations (34)–(37).
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from src.joint import fit_maturities
from src.repeated import EDGES
from src.selection import CANDIDATES, choose_penalty, fit_record, folds, pooled_score

QUOTE_FIELDS = ("quote_id", "snapshot_id", "observed_at", "root", "expiry",
                "settlement_at", "exercise", "settlement_style", "option_type",
                "strike", "bid", "ask", "bid_size", "ask_size")
DISCOUNT_FIELDS = ("snapshot_id", "root", "settlement_at", "discount",
                   "observed_at", "available_at", "source_reference")
EVIDENCE_FIELDS = ("quotes", "observation_time", "sizes", "settlement",
                   "discounts", "research_use")


def timestamp(value):
    """Require a complete ISO datetime with an explicit UTC offset."""
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("A full ISO datetime with an explicit UTC offset is required.")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("A timezone-naive datetime cannot establish a quote horizon.")
    return result.astimezone(timezone.utc)


def year_fraction(observed_at, settlement_at):
    seconds = (timestamp(settlement_at)-timestamp(observed_at)).total_seconds()
    if seconds <= 0:
        raise ValueError("Settlement must be after observation.")
    return seconds/(365*24*60*60)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _csv(path, fields):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError(f"Missing columns in {Path(path).name}: {sorted(set(fields)-set(reader.fieldnames or []))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"No observations in {Path(path).name}.")
    return rows


def read_bundle(directory):
    directory = Path(directory)
    manifest = json.loads((directory/"manifest.json").read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported or missing bundle schema version.")
    if manifest.get("data_kind") not in ("market", "synthetic_fixture"):
        raise ValueError("Explicit market or synthetic_fixture classification required.")
    expected = {"underlying": "SPX", "quote_units": "index_points", "settlement_type": "cash",
                "timestamp_semantics": "contemporaneous_nbbo_snapshot",
                "size_semantics": "positive_displayed_contracts",
                "calendar_model": "deterministic_carry_proportional_dividends"}
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"Unsupported or undocumented {key}; required declaration: {value}.")
    for name in EVIDENCE_FIELDS:
        value = manifest.get("source_evidence", {}).get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing source evidence for {name}.")
    if manifest["data_kind"] == "market":
        review = manifest.get("review", {})
        if review.get("decision") != "accepted_for_research" or any(
                not isinstance(review.get(k), str) or not review[k].strip()
                for k in ("reviewer", "reviewed_at", "notes")):
            raise ValueError("Market inputs require an attributable source review before calibration.")
        timestamp(review["reviewed_at"])
    for name in ("quotes.csv", "discounts.csv"):
        if manifest.get("input_sha256", {}).get(name) != sha256(directory/name):
            raise ValueError(f"Input checksum mismatch for {name}.")
    policy = manifest.get("screening", {})
    for key in ("max_relative_spread", "max_curve_age_seconds"):
        value = policy.get(key)
        if not isinstance(value, (int, float)) or not np.isfinite(value) or value <= 0:
            raise ValueError(f"An explicit positive finite screening value is required: {key}.")
    return manifest, _csv(directory/"quotes.csv", QUOTE_FIELDS), _csv(directory/"discounts.csv", DISCOUNT_FIELDS)


@dataclass(frozen=True)
class Pair:
    strike: float
    call: dict
    put: dict

    @property
    def call_mid(self):
        return (self.call["bid"]+self.call["ask"])/2


@dataclass(frozen=True)
class Group:
    snapshot_id: str
    root: str
    expiry: str
    observed_at: str
    settlement_at: str
    discount: float
    maturity: float
    curve_age_seconds: float
    pairs: tuple


def prepare_groups(manifest, rows, discount_rows):
    """Keep every input row's reasons; never silently resolve duplicate quotes."""
    audit, fatal = [], []
    def audit_report():
        return {"data_kind": manifest["data_kind"], "input_rows": len(rows),
            "retained_rows": sum(not r["reasons"] for r in audit),
            "excluded_rows": sum(bool(r["reasons"]) for r in audit),
            "reason_counts": dict(Counter(r for item in audit for r in item["reasons"])),
            "row_audit": audit, "fatal_errors": fatal, "metadata_checks_passed": not fatal,
            "source_authenticity": "Not established by software; supplied source evidence and review must be checked.",
            "review": manifest.get("review")}
    parsed = []
    for number, raw in enumerate(rows, 2):
        item = {"csv_row": number, "quote_id": raw.get("quote_id", ""), "reasons": []}
        audit.append(item)
        try:
            row = dict(raw)
            if any(not str(row.get(k, "")).strip() for k in QUOTE_FIELDS):
                raise ValueError("missing required field")
            row["observed_at"] = timestamp(row["observed_at"]).isoformat()
            row["settlement_at"] = timestamp(row["settlement_at"]).isoformat()
            datetime.strptime(row["expiry"], "%Y-%m-%d")
            year_fraction(row["observed_at"], row["settlement_at"])
            if (row["root"] not in ("SPX", "SPXW") or row["exercise"] != "European"
                    or row["settlement_style"] != {"SPX": "AM", "SPXW": "PM"}[row["root"]]
                    or row["option_type"] not in ("C", "P")):
                raise ValueError("unsupported contract declaration")
            for k in ("strike", "bid", "ask", "bid_size", "ask_size"):
                row[k] = float(row[k])
            if not np.isfinite(row["strike"]) or row["strike"] <= 0:
                raise ValueError("invalid strike")
            row["_audit"] = item
            parsed.append(row)
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            item["reasons"].append("invalid_metadata")
            fatal.append(f"CSV row {number}: {error}")
    if not parsed:
        fatal.append("No parseable quote rows.")
        return [], audit_report()
    # This first empirical workflow takes one synchronised snapshot and one class.
    for field in ("snapshot_id", "root", "observed_at"):
        if len({r[field] for r in parsed}) != 1:
            fatal.append(f"A calibration bundle must have exactly one {field}.")
    expiry_times = defaultdict(set)
    for r in parsed:
        expiry_times[r["expiry"]].add(r["settlement_at"])
    if any(len(v) != 1 for v in expiry_times.values()):
        fatal.append("Conflicting settlement datetimes for the same expiry.")
    keys = [(r["expiry"], r["settlement_at"], r["option_type"], r["strike"]) for r in parsed]
    duplicates, identifiers = Counter(keys), Counter(r["quote_id"] for r in parsed)
    usable = defaultdict(dict)
    for r, key in zip(parsed, keys):
        reasons = r["_audit"]["reasons"]
        if duplicates[key] > 1 or identifiers[r["quote_id"]] > 1:
            reasons.append("duplicate_quote")
        b, a = r["bid"], r["ask"]
        if not np.isfinite(b) or not np.isfinite(a):
            reasons.append("nonfinite_price")
        elif b <= 0 or a <= 0:
            reasons.append("nonpositive_price")
        elif b > a:
            reasons.append("crossed_quote")
        elif (a-b)/((a+b)/2) > manifest["screening"]["max_relative_spread"]:
            reasons.append("wide_spread")
        if any(not np.isfinite(r[k]) or r[k] <= 0 or not r[k].is_integer()
               for k in ("bid_size", "ask_size")):
            reasons.append("unusable_size")
        if not reasons:
            usable[(r["expiry"], r["settlement_at"], r["strike"])][r["option_type"]] = r
    paired = defaultdict(list)
    for (expiry, settlement, strike), sides in usable.items():
        if set(sides) != {"C", "P"}:
            for row in sides.values():
                row["_audit"]["reasons"].append("unmatched_pair")
        else:
            paired[(expiry, settlement)].append(Pair(strike, sides["C"], sides["P"]))
    dmap = {}
    for row in discount_rows:
        try:
            if any(row.get(k) is None or not str(row[k]).strip() for k in DISCOUNT_FIELDS):
                raise ValueError("missing required discount field")
            key = (row["snapshot_id"], row["root"], timestamp(row["settlement_at"]).isoformat())
            observed, available = timestamp(row["observed_at"]), timestamp(row["available_at"])
            value = float(row["discount"])
            if key in dmap or not np.isfinite(value) or value <= 0 or not row["source_reference"].strip():
                raise ValueError("duplicate/invalid discount or missing source")
            if available < observed:
                raise ValueError("discount availability precedes its observation")
            dmap[key] = (value, observed, available)
        except (ValueError, KeyError, TypeError) as error:
            fatal.append(f"Discount row: {error}")
    groups = []
    first = parsed[0]
    obs = timestamp(first["observed_at"])
    # Include entirely excluded expiries in the failure report, not only survivors.
    for expiry, settlement in sorted({(r["expiry"], r["settlement_at"]) for r in parsed}, key=lambda x:x[1]):
        pairs = tuple(sorted(paired.get((expiry, settlement), []), key=lambda p:p.strike))
        if len(pairs) < 7:
            fatal.append(f"{expiry}: {len(pairs)} usable pairs; at least seven required for this three-fold design.")
        key = (first["snapshot_id"], first["root"], settlement)
        if key not in dmap:
            fatal.append(f"{expiry}: missing matching discount.")
            continue
        discount, curve_time, availability = dmap[key]
        age = (obs-curve_time).total_seconds()
        if availability > obs or age < 0 or age > manifest["screening"]["max_curve_age_seconds"]:
            fatal.append(f"{expiry}: discount unavailable at observation or older than the declared limit.")
        groups.append(Group(first["snapshot_id"], first["root"], expiry, first["observed_at"], settlement,
                            discount, year_fraction(first["observed_at"], settlement), age, pairs))
    if len(groups) < 2 or len({g.settlement_at for g in groups}) != len(groups):
        fatal.append("At least two distinct settlement horizons are required for the joint fit.")
    return groups, audit_report()


def parity_interval(pairs, discount):
    """Conditional intersection; an empty interval is diagnosed, never repaired."""
    if not pairs or not np.isfinite(discount) or discount <= 0:
        raise ValueError("Pairs and a positive finite discount are required.")
    lower = np.array([p.strike+(p.call["bid"]-p.put["ask"])/discount for p in pairs])
    upper = np.array([p.strike+(p.call["ask"]-p.put["bid"])/discount for p in pairs])
    L, U = float(lower.max()), float(upper.min())
    feasible = bool(L <= U and L > 0)
    return {"lower": L, "upper": U, "feasible": feasible,
            "forward": (L+U)/2 if feasible else None,
            "minimum_uniform_relaxation": max(0., (L-U)/2),
            "lower_by_strike": lower.tolist(), "upper_by_strike": upper.tolist(),
            "lower_binding_strike": pairs[int(np.argmax(lower))].strike,
            "upper_binding_strike": pairs[int(np.argmin(upper))].strike,
            "interpretation": "Conditional bid–ask compatibility set, not a statistical confidence interval."}


def fit_pairs(groups, pairs_by_group, penalty, fitter=fit_maturities):
    forwards = [parity_interval(p, g.discount) for p,g in zip(pairs_by_group,groups)]
    if any(not f["feasible"] for f in forwards):
        raise ValueError("Empty/nonpositive parity intersection; calibration is blocked.")
    joint = fitter([np.array([p.strike for p in pairs]) for pairs in pairs_by_group],
                   [np.array([p.call_mid for p in pairs]) for pairs in pairs_by_group],
                   [f["forward"] for f in forwards], [g.discount for g in groups],
                   [g.maturity for g in groups], EDGES, penalty=penalty,
                   max_solver_iterations=200, residual_form=True, solver_backend="clarabel")
    return joint, forwards


def select_from_pairs(groups, candidates=CANDIDATES, fitter=fit_maturities):
    """All quote-dependent forward estimation is repeated inside each fold."""
    partition = [folds(len(g.pairs)) for g in groups]
    candidates_out = []
    for penalty in candidates:
        saved = []
        for fi in range(3):
            train = [tuple(g.pairs[i] for i in p[fi][0]) for g,p in zip(groups,partition)]
            joint, forwards = fit_pairs(groups, train, penalty, fitter)
            errors, members = [], []
            for g,p,fit,fwd in zip(groups,partition,joint.fits,forwards):
                tr, held = p[fi]
                residual = (fit.prices(np.array([g.pairs[i].strike for i in held]))
                            - np.array([g.pairs[i].call_mid for i in held]))/fwd["forward"]
                errors.extend(residual.tolist())
                members.append({"expiry": g.expiry, "train_indices": tr.tolist(),
                    "held_indices": held.tolist(), "forward_interval": fwd,
                    "normalised_residuals": residual.tolist()})
            saved.append({"fold": fi, "groups": members, "count": len(errors),
                          "squared_error_sum": float(np.dot(errors,errors)), **fit_record(joint)})
        score = pooled_score([f["squared_error_sum"] for f in saved], [f["count"] for f in saved])
        candidates_out.append({"penalty": float(penalty), "score": score, "folds": saved})
    selected = choose_penalty([(c["penalty"],c["score"]) for c in candidates_out])
    return {"selected_penalty": selected, "candidates": candidates_out,
            "boundary_selected": selected in (min(candidates),max(candidates)),
            "scope": "Interior strike interpolation; endpoints retained; paired calls/puts held out together; training-only parity forwards."}


def quote_residuals(group, fit):
    k = np.array([p.strike for p in group.pairs])
    calls = fit.prices(k)
    puts = calls-group.discount*(fit.forward-k)
    result = []
    for p,c,v in zip(group.pairs,calls,puts):
        for typ, row, value in (("C",p.call,c),("P",p.put,v)):
            distance = max(row["bid"]-value, value-row["ask"], 0.)
            result.append({"quote_id": row["quote_id"], "option_type": typ, "strike":p.strike,
                "bid":row["bid"], "ask":row["ask"], "fitted":float(value),
                "midpoint_residual":float(value-(row["bid"]+row["ask"])/2),
                "distance_outside_spread":float(distance)})
    return result


def calibrate(directory):
    manifest, rows, discounts = read_bundle(directory)
    groups, audit = prepare_groups(manifest, rows, discounts)
    result = {"data_kind":manifest["data_kind"], "status":"blocked", "audit":audit,
              "input_manifest":manifest,
              "bundle_manifest_sha256":sha256(Path(directory)/"manifest.json")}
    if audit["fatal_errors"]:
        return result, None, groups
    result["forward_intervals"] = [parity_interval(g.pairs,g.discount) for g in groups]
    if any(not f["feasible"] for f in result["forward_intervals"]):
        result["blocking_reason"] = "At least one maturity has an empty/nonpositive bid–ask parity intersection."
        return result, None, groups
    selection = select_from_pairs(groups)
    joint, _ = fit_pairs(groups, [g.pairs for g in groups], selection["selected_penalty"])
    marginals = []
    for g,fit in zip(groups,joint.fits):
        residuals = quote_residuals(g,fit)
        marginals.append({"expiry":g.expiry, "settlement_at":g.settlement_at,
            "maturity":g.maturity, "pair_count":len(g.pairs), "curve_age_seconds":g.curve_age_seconds,
            "forward":fit.forward, "discount":fit.discount, "edges":fit.edges.tolist(),
            "mass":fit.mass.tolist(), "quote_residuals":residuals,
            "outside_spread_count":sum(r["distance_outside_spread"]>1e-7 for r in residuals),
            "outside_spread_tolerance_points":1e-7,
            "maximum_spread_distance":max(r["distance_outside_spread"] for r in residuals)})
    result.update(status="synthetic_fixture_calibrated" if manifest["data_kind"]=="synthetic_fixture"
                  else "calibrated_subject_to_documented_source_review",
                  selection=selection, fit=fit_record(joint), marginals=marginals,
                  fit_count=3*len(CANDIDATES)+1,
                  limitations=["Source authenticity and permissions are not proved by these numerical checks.",
                    "Parity feasibility does not ensure a single arbitrage-consistent curve within every spread.",
                    "Call midpoints enter the objective; puts inform parity and separate residual diagnostics.",
                    "Discounts, finite support and the deterministic-carry calendar model remain input assumptions.",
                    "Cross-validation scores are selection criteria, not independent empirical performance estimates."])
    return result, joint, groups
