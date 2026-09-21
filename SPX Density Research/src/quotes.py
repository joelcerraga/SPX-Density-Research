"""Audit a Cboe page snapshot; never infer quote observation time from trades."""
import math
import re
from collections import Counter, defaultdict
from datetime import datetime

SYMBOL = re.compile(r'^(SPXW|SPX)(\d{6})([CP])(\d{8})$')

def number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def audit(payload, provenance, max_relative_spread=0.25):
    """Return all rows with reasons; spread threshold is a research choice."""
    if not 0 < max_relative_spread < 2:
        raise ValueError('Relative-spread threshold must lie between 0 and 2.')
    options = payload['data']['options']
    counts = Counter(str(q.get('option', '')) for q in options)
    rows = []
    for q in options:
        symbol = str(q.get('option', ''))
        match = SYMBOL.fullmatch(symbol)
        reasons, warnings = [], []
        row = dict(symbol=symbol, root='', expiry='', option_type='', strike=None)
        if match:
            root, expiry, kind, strike = match.groups()
            try:
                expiry = datetime.strptime(expiry, '%y%m%d').date().isoformat()
                row.update(root=root, expiry=expiry, option_type=kind, strike=int(strike)/1000)
                if row['strike'] <= 0:
                    reasons.append('nonpositive_strike')
            except ValueError:
                reasons.append('invalid_expiry')
        else:
            reasons.append('invalid_symbol')
        if counts[symbol] > 1:
            reasons.append('duplicate_symbol')
        bid, ask = number(q.get('bid')), number(q.get('ask'))
        mid = spread = relative = None
        if bid is None or ask is None:
            reasons.append('missing_or_nonfinite_price')
        elif bid < 0 or ask <= 0:
            reasons.append('invalid_price')
        elif ask < bid:
            reasons.append('crossed_market')
        else:
            mid, spread = (ask+bid)/2, ask-bid
            relative = spread/mid
            if bid == 0:
                reasons.append('zero_bid')
            if relative > max_relative_spread:
                reasons.append('wide_spread')
        for field in ('bid_size', 'ask_size'):
            size = number(q.get(field))
            if size is None or size <= 0:
                warnings.append('unconfirmed_'+field)
        row.update(bid=bid, ask=ask, midpoint=mid, spread=spread,
                   relative_spread=relative, local_price_screen_pass=not reasons,
                   exclusion_reasons=';'.join(reasons), warnings=';'.join(warnings))
        rows.append(row)
    groups = defaultdict(list)
    for row in rows:
        if row['root'] and row['expiry']:
            groups[(row['root'], row['expiry'])].append(row)
    coverage = []
    for (root, expiry), items in sorted(groups.items()):
        passing = [r for r in items if r['local_price_screen_pass']]
        calls = {r['strike'] for r in passing if r['option_type']=='C'}
        puts = {r['strike'] for r in passing if r['option_type']=='P'}
        strikes = calls | puts
        coverage.append(dict(root=root, expiry=expiry, raw_rows=len(items),
                             price_screen_pass=len(passing), paired_strikes=len(calls & puts),
                             minimum_strike=min(strikes) if strikes else None,
                             maximum_strike=max(strikes) if strikes else None))
    reasons = Counter(reason for r in rows for reason in r['exclusion_reasons'].split(';') if reason)
    warnings = Counter(reason for r in rows for reason in r['warnings'].split(';') if reason)
    summary = dict(raw_rows=len(rows), local_price_screen_pass=sum(r['local_price_screen_pass'] for r in rows),
                   relative_spread_threshold=max_relative_spread, exclusion_counts=dict(reasons),
                   warning_counts=dict(warnings), root_expiry_groups=len(coverage),
                   quote_timestamp_raw=payload.get('timestamp'),
                   density_estimation_ready=False,
                   blocking_checks=['Full quote observation datetime and timezone must be verified',
                                    'Settlement datetime and contract convention must be verified',
                                    'Discount factor and forward must be established',
                                    'Quote sizes, price shape and strike coverage require review'])
    return rows, coverage, summary
