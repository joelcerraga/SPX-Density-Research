"""Bundle the dated, fully offline Notebook 10 explorer."""
import hashlib
import json
from pathlib import Path
from build_surface_html import PLOTLY_SHA256

ROOT=Path(__file__).resolve().parent


def main():
    bundle=(ROOT/'interactive/vendor/plotly-3.1.0.min.js').read_bytes()
    if hashlib.sha256(bundle).hexdigest()!=PLOTLY_SHA256:raise RuntimeError('Plotly checksum mismatch')
    report=json.loads((ROOT/'results/comparison_summary.json').read_text());data=[]
    for snapshot in report['snapshots']:
        item={k:snapshot[k] for k in ('id','label','observed_at','risk_ranges','holdout_summary')}
        for kind,key in [('full','primary_case'),('matched','matched_case')]:
            c=json.loads((ROOT/'results/comparison_cases'/(snapshot[key]+'.json')).read_text())
            if c['status']!='solved':raise RuntimeError('Explorer requires an accepted fit')
            item[kind]={'edges':c['edges_normalised'],'common':c['common_60_days'],
                'marginals':[{k:m[k] for k in ('expiry','elapsed_days','forward','discount','pair_count','mass','risk',
                    'normalised_strike_range','outside_spread_count')} for m in c['marginals']]}
        data.append(item)
    page=(ROOT/'interactive/dated_surface_template.html').read_text()
    for marker,value in {'__PLOTLY_BUNDLE__':bundle.decode().replace('</script','<\\/script'),
        '__DATED_DATA__':json.dumps(data,separators=(',',':'),allow_nan=False).replace('<','\\u003c'),
        '__PLOTLY_LICENSE__':(ROOT/'interactive/vendor/PLOTLY-LICENSE.txt').read_text()}.items():
        if page.count(marker)!=1:raise ValueError(f'Expected one {marker}')
        page=page.replace(marker,value)
    output=ROOT/'interactive/dated_density_surface.html';output.write_text(page)
    print('Built dated_density_surface.html; three observed snapshots, all scripts and data included.')
    return output


if __name__=='__main__':main()
