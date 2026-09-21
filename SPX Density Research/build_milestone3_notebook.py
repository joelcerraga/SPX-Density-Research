"""Build the walkthrough from one methodology source; execute its runner cell.

Figures are embedded as Markdown attachments from verified PNGs so their captions
remain separate. Notebook cell execution uses Python, not an assumed local kernel.
"""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def main():
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    cells=[]

    def markdown(text):
        cells.append({'cell_type':'markdown','id':f'constrained-{len(cells):02}',
                      'metadata':{},'source':text.splitlines(keepends=True)})

    markdown('# Notebook 3: constrained density recovery\n\n'
             'This walkthrough is synthetic. Open it from the extracted project folder. '
             'The executable cell regenerates the figures and results; rerun this builder '
             'to refresh the embedded figure attachments after changing the experiment. '
             'Paper references and numerical assumptions appear alongside the derivation.\n')
    source=(ROOT/'research/constrained_methodology.md').read_text()
    # Add one executable cell before the results table, preserving the prose order.
    marker='Table 5. Baseline constrained-fit diagnostics'
    before,after=source.split(marker,1)
    markdown(before)
    code='from run_constrained import main\nresult = main()\n'
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):
        exec(compile(code, '<notebook-3-cell>', 'exec'), {})
    cells.append({'cell_type':'code','id':'constrained-runner','metadata':{},
                  'source':code.splitlines(keepends=True),'execution_count':1,
                  'outputs':[{'output_type':'stream','name':'stdout','text':stream.getvalue()}]})
    remaining=marker+after
    parts=re.split(r'(!\[[^\]]*\]\(\.\./figures/[^)]+\))',remaining)
    for part in parts:
        match=re.fullmatch(r'!\[([^\]]*)\]\(\.\./figures/([^)]+)\)',part)
        if not match:
            if part.strip():markdown(part)
            continue
        alt,name=match.groups()
        markdown(f'![{alt}](attachment:{name})\n')
        cells[-1]['attachments']={name:{'image/png':base64.b64encode((ROOT/'figures'/name).read_bytes()).decode()}}
    notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                    'language_info':{'name':'python','version':sys.version.split()[0]},
                    'project_execution':{'method':'runner code executed with Python; figures embedded as Markdown attachments',
                                         'data_kind':'synthetic'}},
              'nbformat':4,'nbformat_minor':5}
    (ROOT/'03_constrained_density.ipynb').write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n')
    print(stream.getvalue())
    print('Third notebook rebuilt with executed calculation and embedded figures.')


if __name__=='__main__':
    main()
