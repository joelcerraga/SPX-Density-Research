"""Timing, pairing, conditional forward inference and retained fit evidence."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

from src.constrained import DensityFit
from src.empirical import (Pair, calibrate, parity_interval, prepare_groups,
    read_bundle, select_from_pairs, sha256, timestamp, year_fraction)
from src.joint import continuous_calendar_check
from src.repeated import EDGES
from src.selection import folds

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"data/fixtures/empirical"


class EmpiricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.rows,cls.discounts=read_bundle(FIXTURE)
        cls.groups,cls.audit=prepare_groups(cls.manifest,cls.rows,cls.discounts)
        cls.report=json.loads((ROOT/"results/empirical_preparation.json").read_text())

    def test_offsets_and_elapsed_time_include_dst(self):
        self.assertEqual(timestamp("2026-01-15T15:45:00-05:00"),timestamp("2026-01-15T20:45:00Z"))
        expected=(60*24*60*60-45*60)/(365*24*60*60)
        self.assertEqual(year_fraction("2026-01-15T15:45:00-05:00","2026-03-16T16:00:00-04:00"),expected)
        for bad in ("2026-01-15","15:45:00","2026-01-15T15:45:00"):
            with self.assertRaises(ValueError):timestamp(bad)
        with self.assertRaises(ValueError):
            year_fraction("2026-01-15T20:45:00Z","2026-01-15T20:45:00Z")

    def test_input_checksums_and_blank_market_review_block_before_fit(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)
            for name in ("quotes.csv","discounts.csv","manifest.json"):
                (target/name).write_bytes((FIXTURE/name).read_bytes())
            (target/"quotes.csv").write_bytes((target/"quotes.csv").read_bytes()+b"\n")
            with self.assertRaisesRegex(ValueError,"checksum"):
                calibrate(target)
            (target/"quotes.csv").write_bytes((FIXTURE/"quotes.csv").read_bytes())
            manifest=copy.deepcopy(self.manifest);manifest["data_kind"]="market"
            (target/"manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,"source review"):
                calibrate(target)

    def test_snapshot_settlement_and_curve_availability_failures(self):
        for field,value in (("observed_at","2026-01-15T20:46:00Z"),
                            ("settlement_at","2026-03-16T09:30:00-04:00"),
                            ("root","SPY"),("exercise","American")):
            rows=copy.deepcopy(self.rows);rows[0][field]=value
            _,audit=prepare_groups(self.manifest,rows,self.discounts)
            self.assertTrue(audit["fatal_errors"],field)
        discount=copy.deepcopy(self.discounts)
        discount[0]["available_at"]="2026-01-15T20:46:00Z"
        _,audit=prepare_groups(self.manifest,self.rows,discount)
        self.assertTrue(any("unavailable" in e for e in audit["fatal_errors"]))
        # Negative interest rates can give D > 1; do not reject them by fiat.
        discount=copy.deepcopy(self.discounts);discount[0]["discount"]="1.01"
        _,audit=prepare_groups(self.manifest,self.rows,discount)
        self.assertFalse(audit["fatal_errors"])
        discount=copy.deepcopy(self.discounts);discount[0]["source_reference"]=None
        _,audit=prepare_groups(self.manifest,self.rows,discount)
        self.assertTrue(any("missing required discount field" in e for e in audit["fatal_errors"]))
        rows=copy.deepcopy(self.rows)
        for r in rows:r["observed_at"]=""
        groups,audit=prepare_groups(self.manifest,rows,self.discounts)
        self.assertEqual(groups,[])
        self.assertEqual(audit["excluded_rows"],len(rows))
        self.assertEqual(len(audit["row_audit"]),len(rows))

    def test_duplicate_sides_and_unmatched_counterparts_are_not_averaged(self):
        rows=copy.deepcopy(self.rows);rows.append(copy.deepcopy(rows[0]))
        rows[-1]["quote_id"]="duplicate-other-id"
        _,audit=prepare_groups(self.manifest,rows,self.discounts)
        self.assertEqual(audit["reason_counts"],{"duplicate_quote":2,"unmatched_pair":1})
        self.assertEqual(audit["excluded_rows"],3)
        self.assertEqual(audit["retained_rows"],280)

    def test_row_screens_keep_explicit_reasons(self):
        cases=[("bid","0","nonpositive_price"),("bid","nan","nonfinite_price"),
               ("ask","0.01","crossed_quote"),("bid_size","0","unusable_size"),
               ("ask_size","1.5","unusable_size")]
        for field,value,reason in cases:
            rows=copy.deepcopy(self.rows);rows[0][field]=value
            _,audit=prepare_groups(self.manifest,rows,self.discounts)
            self.assertIn(reason,audit["row_audit"][0]["reasons"])
            self.assertIn("unmatched_pair",audit["row_audit"][1]["reasons"])

    def test_parity_endpoints_use_opposite_quote_sides_and_discount(self):
        pairs=[Pair(100.,{"bid":12.,"ask":14.},{"bid":7.,"ask":8.}),
               Pair(105.,{"bid":9.,"ask":11.},{"bid":9.,"ask":10.})]
        result=parity_interval(pairs,.5)
        # [108,114] intersect [103,109] = [108,109].
        self.assertEqual((result["lower"],result["upper"],result["forward"]),(108.,109.,108.5))
        self.assertTrue(result["feasible"])
        broken=[replace(pairs[0],call={"bid":16.,"ask":18.}),pairs[1]]
        result=parity_interval(broken,.5)
        self.assertEqual((result["lower"],result["upper"]),(116.,109.))
        self.assertEqual(result["minimum_uniform_relaxation"],3.5)
        self.assertFalse(result["feasible"]);self.assertIsNone(result["forward"])

    def test_held_pair_does_not_change_its_training_forward_or_prediction(self):
        captured=[]
        def fitter(k,y,f,d,t,edges,**kwargs):
            captured.append({"k":[v.copy() for v in k],"y":[v.copy() for v in y],"f":list(f)})
            return SimpleNamespace(fits=[SimpleNamespace(prices=lambda x,v=float(a.mean()):np.full(len(x),v)) for a in y],
                                   weights=np.ones((len(k),1)),solver={},continuous_check={})
        select_from_pairs(self.groups,candidates=(1e-6,),fitter=fitter)
        original=copy.deepcopy(captured)
        pairs=list(self.groups[0].pairs);held=pairs[1]
        changed=dict(held.call);changed["bid"]+=.2;changed["ask"]+=.2
        pairs[1]=replace(held,call=changed)
        changed_groups=[replace(self.groups[0],pairs=tuple(pairs)),*self.groups[1:]]
        captured.clear()
        select_from_pairs(changed_groups,candidates=(1e-6,),fitter=fitter)
        # Index 1 belongs to fold 0's holdout, including both option types.
        self.assertIn(1,folds(len(pairs))[0][1])
        self.assertEqual(original[0]["f"],captured[0]["f"])
        for a,b in zip(original[0]["y"],captured[0]["y"]):np.testing.assert_array_equal(a,b)
        self.assertNotEqual(parity_interval(self.groups[0].pairs,self.groups[0].discount)["forward"],
                            parity_interval(changed_groups[0].pairs,self.groups[0].discount)["forward"])

    def test_saved_scores_reconstruct_with_training_only_forwards(self):
        r=self.report
        for candidate in r["selection"]["candidates"]:
            total=0.;count=0
            for saved in candidate["folds"]:
                for g,saved_g,w in zip(self.groups,saved["groups"],saved["weights"]):
                    train,held=saved_g["train_indices"],saved_g["held_indices"]
                    self.assertFalse(set(train)&set(held))
                    interval=parity_interval(tuple(g.pairs[i] for i in train),g.discount)
                    self.assertEqual(interval["forward"],saved_g["forward_interval"]["forward"])
                    f=interval["forward"]
                    fit=DensityFit(EDGES*f,np.asarray(w),g.discount,f,candidate["penalty"],0,0.)
                    residual=(fit.prices(np.array([g.pairs[i].strike for i in held]))
                              -np.array([g.pairs[i].call_mid for i in held]))/f
                    np.testing.assert_allclose(residual,saved_g["normalised_residuals"],rtol=0,atol=2e-14)
                    total+=float(residual@residual);count+=len(residual)
            self.assertEqual(count,sum(len(g.pairs)-2 for g in self.groups))
            self.assertAlmostEqual(candidate["score"],total/count,places=18)

    def test_all_ten_joint_fits_pass_independent_constraints(self):
        r=self.report
        fits=[r["fit"]]+[f for c in r["selection"]["candidates"] for f in c["folds"]]
        self.assertEqual(len(fits),10)
        for fit in fits:
            w=np.array(fit["weights"])
            np.testing.assert_allclose(w.sum(axis=1),1,rtol=0,atol=1e-8)
            np.testing.assert_allclose(w@((EDGES[1:]+EDGES[:-1])/2),1,rtol=0,atol=1e-8)
            self.assertGreaterEqual(w.min(),-1e-9)
            check,_=continuous_calendar_check(EDGES,w)
            self.assertTrue(check["passes"])
            self.assertTrue(all(h["status"]=="Solved" for h in fit["solver"]["history"]))
        for g,m in zip(self.groups,r["marginals"]):
            fit=DensityFit(np.array(m["edges"]),np.array(m["mass"]),g.discount,m["forward"],0,0,0.)
            for row in m["quote_residuals"]:
                c=fit.prices(np.array([row["strike"]]))[0]
                v=c if row["option_type"]=="C" else c-g.discount*(fit.forward-row["strike"])
                self.assertAlmostEqual(v,row["fitted"],places=8)
                gap=max(row["bid"]-v,v-row["ask"],0.)
                self.assertAlmostEqual(gap,row["distance_outside_spread"],places=8)

    def test_saved_source_and_fixture_hashes_match(self):
        for name,digest in self.report["code_sha256"].items():self.assertEqual(sha256(ROOT/name),digest,name)
        for name,digest in self.report["fixture_sha256"].items():self.assertEqual(sha256(FIXTURE/name),digest,name)
        self.assertEqual(self.report["data_kind"],"synthetic_fixture")
        self.assertEqual(self.report["actual_market_calibration"]["status"],"not_performed")

    def test_eight_earlier_notebooks_and_both_explorers_remain_unchanged(self):
        hashes=json.loads((ROOT/"results/milestone9_preserved_sha256.json").read_text())
        self.assertEqual(len(hashes),10)
        for name,digest in hashes.items():self.assertEqual(sha256(ROOT/name),digest,name)


if __name__=="__main__":unittest.main()
