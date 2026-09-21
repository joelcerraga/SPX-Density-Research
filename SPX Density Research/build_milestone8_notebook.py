"""Execute or reuse the declared study and build the eighth explanatory notebook."""
import argparse
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
CODE=('from run_selection import main\n'
      'from build_selection_report import main as build_report\n'
      'result = main(resume=True, workers=4)\n'
      'build_report()\n')


def main(refresh_narrative=False):
    os.chdir(ROOT);sys.path.insert(0,str(ROOT))
    target=ROOT/'08_smoothing_and_forwards.ipynb'
    if refresh_narrative:
        old=json.loads(target.read_text())
        executed=next(c for c in old['cells'] if c['cell_type']=='code')
        if ''.join(executed['source'])!=CODE:raise ValueError('Execute the changed code cell normally.')
        from build_selection_report import main as build_report
        build_report()
    else:
        original=sys.stdout
        class Capture(io.StringIO):
            def write(self,text):
                original.write(text);original.flush();return super().write(text)
        stream=Capture()
        with contextlib.redirect_stdout(stream):exec(compile(CODE,'<notebook-8-cell>','exec'),{})
        executed={'cell_type':'code','id':'selection-runner','metadata':{},'source':CODE.splitlines(keepends=True),
                  'execution_count':1,'outputs':[{'output_type':'stream','name':'stdout','text':stream.getvalue()}]}
    source=(ROOT/'research/selection_methodology_template.md').read_text()
    for key,value in json.loads((ROOT/'results/selection_tables.json').read_text()).items():
        source=source.replace('{{'+key+'}}',value)
    if re.search(r'\{\{[A-Z_]+\}\}',source):raise ValueError('Unresolved methodology placeholder.')
    (ROOT/'research/selection_methodology.md').write_text(source)
    cells=[]
    def markdown(text):
        text=text.replace('](../','](')
        for name in ('development_reflection.md','project_roadmap.md','references.md'):
            text=text.replace(']('+name+')','](research/'+name+')')
        cells.append({'cell_type':'markdown','id':f'selection-{len(cells):02}','metadata':{},'source':text.splitlines(keepends=True)})
    markdown('# Notebook 8: smoothing selection and forward sensitivity\n\n'
             'This notebook selects smoothing from noisy held-out quotes and evaluates the complete rule separately. '
             'It then stresses supplied forwards while preserving physical risk thresholds. The executed cell verifies '
             'and reuses matching saved cases. A fresh run can take tens of minutes: use '
             '`python run_selection.py --fresh --workers 4` from the project folder, then rebuild this notebook. '
             'Run `python build_milestone8_notebook.py` to refresh computed text, tables and embedded figures together.\n')
    cells.append(executed)
    for part in re.split(r'(!\[[^\]]*\]\(\.\./figures/[^)]+\))',source):
        match=re.fullmatch(r'!\[([^\]]*)\]\(\.\./figures/([^)]+)\)',part)
        if not match:
            if part.strip():markdown(part)
        else:
            alt,name=match.groups();markdown(f'![{alt}](attachment:{name})\n')
            cells[-1]['attachments']={name:{'image/png':base64.b64encode((ROOT/'figures'/name).read_bytes()).decode()}}
    notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
              'language_info':{'name':'python','version':sys.version.split()[0]},
              'project_execution':{'method':'Python cell executed directly; matching cached cases verified and reused',
                                   'data_kind':'synthetic','historical_animation':False}},'nbformat':4,'nbformat_minor':5}
    target.write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
    print('Notebook 8 built with executed outputs, Tables 18–21 and embedded Figures 21–23.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-narrative',action='store_true')
    main(parser.parse_args().refresh_narrative)
