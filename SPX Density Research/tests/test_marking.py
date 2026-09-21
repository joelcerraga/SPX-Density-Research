"""Independent carry, source-column, held-pair and saved-market-fit checks."""
import copy
import csv
from dataclasses import replace
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

from src.constrained import DensityFit
from src.empirical import Pair, sha256
from src.joint import continuous_calendar_check
from src.marking import audit_file, infer_carry, select_market
from src.repeated import EDGES
from src.robustness import histogram_risk

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/raw/marking_prices"


def pair(k,d=1.02,f=100.,shift=0.,width=.1):
    v=d*(f-k)
    c=30+max(v,0)+shift;p=30+max(-v,0)
    return Pair(k,{"bid":c-width,"ask":c+width},{"bid":p-width,"ask":p+width})


class MarkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups,cls.audit=audit_file(RAW/"eod_marking_prices_list.csv")
        cls.primary=json.loads((ROOT/"results/marking_calibration.json").read_text())
        cls.diagnostic=json.loads((ROOT/"results/marking_range_diagnostic.json").read_text())

    def test_exact_parity_recovers_discount_and_forward_including_negative_rates(self):
        pairs=tuple(pair(k) for k in (80.,90.,100.,110.,120.))
        c=infer_carry(pairs)
        self.assertAlmostEqual(c["discount"],1.02,places=12)
        self.assertAlmostEqual(c["forward"],100.,places=11)
        self.assertLessEqual(c["discount_feasible_interval"][0],1.02)
        self.assertGreaterEqual(c["discount_feasible_interval"][1],1.02)
        scaled=tuple(Pair(p.strike*1000,{k:v*1000 for k,v in p.call.items()},
                                      {k:v*1000 for k,v in p.put.items()}) for p in pairs)
        s=infer_carry(scaled)
        self.assertAlmostEqual(s["discount"],c["discount"],places=12)
        self.assertAlmostEqual(s["forward"],100000.,places=7)

    def test_incompatible_pair_bounds_stop_instead_of_silent_repair(self):
        pairs=[pair(80),pair(100,shift=10),pair(120)]
        with self.assertRaisesRegex(ValueError,"Carry set"):
            infer_carry(pairs)

    def test_constrained_solution_handles_a_wide_midpoint_outlier(self):
        pairs=[pair(k,d=.98) for k in (80.,90.,100.,110.,120.)]
        pairs[2]=pair(100,d=.98,shift=5,width=5)
        c=infer_carry(pairs)
        self.assertEqual(c["method"],"Constrained least squares, Clarabel")
        self.assertLessEqual(c["maximum_interval_violation_points"],1e-7)
        for p in pairs:
            v=c["discount"]*(c["forward"]-p.strike)
            self.assertGreaterEqual(v,p.call["bid"]-p.put["ask"]-1e-7)
            self.assertLessEqual(v,p.call["ask"]-p.put["bid"]+1e-7)

    def test_indicative_marks_and_sizes_cannot_become_market_observations(self):
        with (RAW/"eod_marking_prices_list.csv").open(newline="") as f:
            reader=csv.DictReader(f);fields=reader.fieldnames
            rows=[r for r in reader if r["call_osi_identifier"]==self.groups[0].pairs[0].call["osi"]]
        self.assertEqual(len(rows),1)
        for side in ("call","put"):
            for s in ("bid","ask"):
                rows[0][f"{side}_final_indicative_{s}"]="999999"
                rows[0][f"{side}_final_indicative_{s}_size"]="0"
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"eod_marking_prices_list.csv"
            def write():
                with p.open("w",newline="") as f:
                    writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows(rows)
            write();groups,audit=audit_file(p)
            self.assertEqual(audit["retained_pairs"],1)
            saved=groups[0].pairs[0].call
            self.assertEqual(saved["bid"],float(rows[0]["call_last_disseminated_market_bid"]))
            self.assertIsNone(saved["bid_size"])
            rows[0]["call_message_time"]="2026-09-18 15:58:59-04:00"
            write();_,audit=audit_file(p)
            self.assertIn("message_age_exceeds_limit",audit["row_audit"][0]["reasons"])
            rows[0]["call_osi_identifier"]="SPXW  261016P00001000"
            write();_,audit=audit_file(p)
            self.assertEqual(audit["metadata_failure_rows"],1)

    def test_whole_pair_holdout_cannot_change_training_discount_or_forward(self):
        captured=[]
        def fitter(k,y,f,d,t,edges,**kwargs):
            captured.append({"f":list(f),"d":list(d),"y":[v.copy() for v in y]})
            return SimpleNamespace(fits=[SimpleNamespace(prices=lambda x,v=float(a.mean()):np.full(len(x),v)) for a in y],
                weights=np.ones((len(k),1)),solver={},continuous_check={})
        select_market(self.groups,candidates=(1e-7,),fitter=fitter)
        original=copy.deepcopy(captured)
        pairs=list(self.groups[0].pairs);c=dict(pairs[1].call)
        c["bid"]+=.1;c["ask"]+=.1;pairs[1]=replace(pairs[1],call=c)
        changed=[replace(self.groups[0],pairs=tuple(pairs)),*self.groups[1:]]
        captured.clear();select_market(changed,candidates=(1e-7,),fitter=fitter)
        self.assertEqual(original[0]["d"],captured[0]["d"])
        self.assertEqual(original[0]["f"],captured[0]["f"])
        for a,b in zip(original[0]["y"],captured[0]["y"]):np.testing.assert_array_equal(a,b)
        self.assertNotEqual(infer_carry(pairs)["discount"],infer_carry(self.groups[0].pairs)["discount"])

    def test_saved_scores_reconstruct_from_training_only_carry_and_weights(self):
        for report in (self.primary,self.diagnostic):
            for c in report["selection"]["candidates"]:
                total=0.;count=0
                for fold in c["folds"]:
                    for g,s,w in zip(self.groups,fold["groups"],fold["weights"]):
                        train,held=s["train_indices"],s["held_indices"]
                        self.assertFalse(set(train)&set(held))
                        carry=infer_carry(tuple(g.pairs[i] for i in train))
                        for key in ("discount","forward"):
                            self.assertAlmostEqual(carry[key],s["carry"][key],places=10)
                        f,d=carry["forward"],carry["discount"]
                        fit=DensityFit(EDGES*f,np.array(w),d,f,c["penalty"],0,0.)
                        e=(fit.prices(np.array([g.pairs[i].strike for i in held]))
                            -np.array([g.pairs[i].call_mid for i in held]))/f
                        np.testing.assert_allclose(e,s["normalised_residuals"],rtol=0,atol=2e-14)
                        total+=float(e@e);count+=len(e)
                self.assertEqual(count,963)
                self.assertAlmostEqual(c["score"],total/count,places=18)

    def test_all_saved_market_fits_and_spread_distances_reconstruct(self):
        count=0
        for report in (self.primary,self.diagnostic):
            fits=report["full_sample_fits"]+[f for c in report["selection"]["candidates"] for f in c["folds"]]
            for f in fits:
                w=np.asarray(f["weights"]);count+=1
                np.testing.assert_allclose(w.sum(axis=1),1,rtol=0,atol=1e-8)
                np.testing.assert_allclose(w@((EDGES[:-1]+EDGES[1:])/2),1,rtol=0,atol=1e-8)
                self.assertGreaterEqual(w.min(),-1e-9)
                self.assertTrue(continuous_calendar_check(EDGES,w)[0]["passes"])
                self.assertTrue(all(h["status"]=="Solved" for h in f["solver"]["history"]))
            for f in report["full_sample_fits"]:
                for m in f["marginals"]:
                    fit=DensityFit(np.array(m["edges"]),np.array(m["mass"]),m["discount"],m["forward"],0,0,0.)
                    for key,v in histogram_risk(fit).items():self.assertAlmostEqual(v,m["risk"][key],places=12)
                    for r in m["quote_residuals"]:
                        v=fit.prices(np.array([r["strike"]]))[0]
                        if r["option_type"]=="P":v-=fit.discount*(fit.forward-r["strike"])
                        self.assertAlmostEqual(v,r["fitted"],places=8)
                        self.assertAlmostEqual(max(r["bid"]-v,v-r["ask"],0.),r["distance_outside_spread"],places=8)
        self.assertEqual(count,24)

    def test_archives_and_code_match_records_and_real_settlement_offsets(self):
        for v in json.loads((RAW/"source_verification.json").read_text()):
            self.assertEqual(sha256(RAW/v["filename"]),v["source_sha256"])
            self.assertEqual(v["source_sha256"],v["uploaded_sha256"])
        for n,h in self.primary["code_sha256"].items():self.assertEqual(sha256(ROOT/n),h,n)
        self.assertEqual(sha256(ROOT/"results/marking_calibration.json"),self.diagnostic["parent_sha256"])
        self.assertTrue(self.groups[0].settlement_at.endswith("-04:00"))
        self.assertTrue(self.groups[1].settlement_at.endswith("-05:00"))
        self.assertAlmostEqual(self.groups[1].maturity,(63+1/24)/365,places=14)
        self.assertEqual(self.audit["metadata_failure_rows"],0)


if __name__=="__main__":unittest.main()
