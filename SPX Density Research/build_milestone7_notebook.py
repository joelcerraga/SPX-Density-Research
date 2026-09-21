"""Execute/reuse validated cases, then build the seventh explanatory notebook."""
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
CODE=('from run_repeated import main\n'
      'from build_repeated_report import main as build_report\n'
      'result = main(resume=True, workers=4)\n'
      'build_report()\n')


def main(refresh_narrative=False):
    os.chdir(ROOT);sys.path.insert(0,str(ROOT))
    target=ROOT/'07_noise_and_coverage.ipynb'
    if refresh_narrative:
        old=json.loads(target.read_text())
        executed=next(c for c in old['cells'] if c['cell_type']=='code')
        if ''.join(executed['source'])!=CODE:
            raise ValueError('Code cell changed; execute the builder normally.')
        from build_repeated_report import main as build_report
        build_report()
    else:
        original=sys.stdout
        class Capture(io.StringIO):
            def write(self,text):
                original.write(text);original.flush();return super().write(text)
        stream=Capture()
        with contextlib.redirect_stdout(stream):exec(compile(CODE,'<notebook-7-cell>','exec'),{})
        executed={'cell_type':'code','id':'repeated-runner','metadata':{},'source':CODE.splitlines(keepends=True),
                  'execution_count':1,'outputs':[{'output_type':'stream','name':'stdout','text':stream.getvalue()}]}
    source=(ROOT/'research/repeated_methodology_template.md').read_text()
    for key,value in json.loads((ROOT/'results/repeated_tables.json').read_text()).items():
        source=source.replace('{{'+key+'}}',value)
    if re.search(r'\{\{[A-Z_]+\}\}',source):raise ValueError('Unresolved methodology placeholder.')
    (ROOT/'research/repeated_methodology.md').write_text(source)
    cells=[]
    def markdown(text):
        text=text.replace('](development_reflection.md)','](research/development_reflection.md)')
        cells.append({'cell_type':'markdown','id':f'repeated-{len(cells):02}','metadata':{},'source':text.splitlines(keepends=True)})
    markdown('# Notebook 7: repeated quote errors and strike coverage\n\n'
             'This notebook compares 50 paired noise realisations per scenario, plus clean-input controls. '
             'The executed cell checks and reuses matching saved cases; missing cases are fitted. '
             'To recompute every fit, use `python run_repeated.py --fresh --workers 4` from the project folder. '
             'A full run can take several minutes. Run `build_milestone7_notebook.py` to update numerical text, tables and embedded figures together.\n')
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
              'project_execution':{'method':'Python cell executed directly; matching case cache verified and reused when available',
                                   'data_kind':'synthetic','historical_animation':False}},'nbformat':4,'nbformat_minor':5}
    target.write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
    print('Notebook 7 built with executed outputs, generated tables and embedded Figures 18–20.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-narrative',action='store_true')
    main(parser.parse_args().refresh_narrative)
