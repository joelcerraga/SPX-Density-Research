"""Reproduce candidate-snapshot diagnostics, not an empirical density estimate."""
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.quotes import audit

ROOT = Path(__file__).resolve().parent

def write_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    raw = ROOT/'data/raw/cboe_spx_candidate.json'
    provenance = json.loads((ROOT/'data/raw/provenance.json').read_text())
    if hashlib.sha256(raw.read_bytes()).hexdigest() != provenance['sha256']:
        raise ValueError('Snapshot hash differs from recorded provenance.')
    payload = json.loads(raw.read_text())
    rows, coverage, report = audit(payload, provenance)
    write_csv(ROOT/'data/processed/quote_audit.csv', rows)
    write_csv(ROOT/'results/expiry_coverage.csv', coverage)
    report['spread_threshold_sensitivity'] = {
        str(t): audit(payload, provenance, t)[2]['local_price_screen_pass']
        for t in (0.1, 0.25, 0.5)
    }
    (ROOT/'results/quote_audit.json').write_text(json.dumps(report, indent=2))
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    # First twelve expiries in each root, ranked by date; no maturity inferred.
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), constrained_layout=True)
    for ax, root in zip(axes, ('SPX', 'SPXW')):
        selected = [g for g in coverage if g['root']==root][:12]
        ax.bar([g['expiry'] for g in selected], [g['paired_strikes'] for g in selected], color='#217a91', label=root)
        ax.set_ylabel('Paired strikes passing price screen')
        ax.tick_params(axis='x', rotation=40)
        ax.legend(frameon=False)
    axes[1].set_xlabel('Contract expiry date')
    for ext in ('png', 'svg'):
        fig.savefig(ROOT/f'figures/figure_05_quote_coverage.{ext}', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    thresholds = list(report['spread_threshold_sensitivity'])
    ax.bar([f'{float(t):.0%}' for t in thresholds], list(report['spread_threshold_sensitivity'].values()), color='#217a91')
    ax.set_xlabel('Maximum bid–ask spread / midpoint')
    ax.set_ylabel('Option records passing local price screen')
    for ext in ('png', 'svg'):
        fig.savefig(ROOT/f'figures/figure_06_spread_sensitivity.{ext}', dpi=180)
    plt.close(fig)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
