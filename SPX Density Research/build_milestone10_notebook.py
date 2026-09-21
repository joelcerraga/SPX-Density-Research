"""Execute Notebook 10 and embed its calculated narrative and scientific figures."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
CODE=('from run_comparison import main as compare_observations\n'
      'from build_comparison_report import main as build_comparison_report\n'
      'from build_comparison_html import main as build_dated_explorer\n'
      'comparison_result = compare_observations()\n'
      'comparison_tables = build_comparison_report()\n'
      'explorer_path = build_dated_explorer()\n')


def main():
    os.chdir(ROOT);sys.path.insert(0,str(ROOT));cells=[]
    def markdown(text):
        text=text.replace('](../','](')
        text=re.sub(r'\]\(([a-z_]+\.md)\)',r'](research/\1)',text)
        cells.append({'cell_type':'markdown','id':f'comparison-{len(cells):02}','metadata':{},'source':text.splitlines(keepends=True)})
    markdown('# Notebook 10: empirical validation and dated comparisons\n\n'
        '**Two dates, three observed snapshots.** This notebook fits original call and put spreads, retains '
        'numerical and held-out limitations, and compares fixed expiries with an explicitly interpolated 60-day horizon. '
        'The 240-bin design follows disclosed feasibility pilots; no blind temporal evaluation is claimed.\n\n'
        'Run `python build_milestone10_notebook.py` in the extracted project folder to recompute all new results '
        'from the archived inputs. The nine previous notebooks and three earlier explorers remain unchanged.\n')
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):exec(compile(CODE,'<notebook-10-cell-1>','exec'),{})
    print(stream.getvalue(),end='')
    cells.append({'cell_type':'code','id':'comparison-runner-1','metadata':{},'source':CODE.splitlines(keepends=True),
        'execution_count':1,'outputs':[{'output_type':'stream','name':'stdout','text':stream.getvalue().splitlines(keepends=True)}]})
    source=(ROOT/'research/comparison_methodology_template.md').read_text()
    for key,value in json.loads((ROOT/'results/comparison_report_tables.json').read_text()).items():source=source.replace('{{'+key+'}}',value)
    if re.search(r'\{\{[A-Z_]+\}\}',source):raise RuntimeError('Unresolved report placeholder')
    (ROOT/'research/comparison_methodology.md').write_text(source)
    for part in re.split(r'(!\[[^\]]*\]\(\.\./figures/[^)]+\))',source):
        match=re.fullmatch(r'!\[([^\]]*)\]\(\.\./figures/([^)]+)\)',part)
        if match:
            alt,name=match.groups();markdown(f'![{alt}](attachment:{name})\n')
            cells[-1]['attachments']={name:{'image/png':base64.b64encode((ROOT/'figures'/name).read_bytes()).decode()}}
        elif part.strip():markdown(part)
    notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':sys.version.split()[0]},
        'project_execution':{'method':'Python code cell executed directly; all Notebook 10 cases, bounds and outputs recomputed',
            'data_kind':'market_exchange_bbo','observation_dates':['2026-08-31','2026-09-18'],'snapshot_count':3,
            'historical_interaction':'Discrete observed-snapshot playback; no interpolated observation dates',
            'known_density_truth':False,'unaccepted_cases_reported':True}},'nbformat':4,'nbformat_minor':5}
    (ROOT/'10_empirical_comparison.ipynb').write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
    print('Notebook 10 built: Figures 29–33, Tables 31–36 and Equations (41)–(46).')


if __name__=='__main__':main()
