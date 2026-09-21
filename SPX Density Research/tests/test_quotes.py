import unittest
from src.quotes import audit

class QuoteAuditTests(unittest.TestCase):
    def test_defects_and_pairing(self):
        def q(k, kind='C', **kw):
            return dict(option=f'SPXW261016{kind}{k:08d}', bid=10, ask=11, bid_size=1, ask_size=1, **kw)
        rows=[q(6000000),q(6000000,'P'),q(6100000),q(6200000),q(6300000),q(6400000),q(6400000)]
        rows[2]['bid']=12
        rows[3]['ask']=float('nan')
        rows[4]['bid']=0
        audited, coverage, summary=audit({'data':{'options':rows}}, {})
        self.assertEqual(summary['local_price_screen_pass'],2)
        self.assertEqual(coverage[0]['paired_strikes'],1)
        self.assertEqual(summary['exclusion_counts']['duplicate_symbol'],2)
        self.assertIn('crossed_market',audited[2]['exclusion_reasons'])
        self.assertIn('missing_or_nonfinite_price',audited[3]['exclusion_reasons'])
        self.assertIn('zero_bid',audited[4]['exclusion_reasons'])
        self.assertFalse(summary['density_estimation_ready'])

    def test_invalid_expiry_and_threshold(self):
        rows=[dict(option='SPX269932C06000000',bid=10,ask=11)]
        audited,_,_=audit({'data':{'options':rows}}, {})
        self.assertIn('invalid_expiry',audited[0]['exclusion_reasons'])
        with self.assertRaises(ValueError):audit({'data':{'options':rows}}, {}, 0)

if __name__=='__main__':unittest.main()
