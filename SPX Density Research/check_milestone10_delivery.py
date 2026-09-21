"""Check the completed Notebook 10 artifacts without rerunning the calculations."""
import base64
import hashlib
import io
import json
from pathlib import Path
import re
from PIL import Image

ROOT=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    nb=json.loads((ROOT/'10_empirical_comparison.ipynb').read_text());cells=nb['cells']
    assert nb['nbformat']==4 and nb['nbformat_minor']==5
    ids=[c['id'] for c in cells];assert len(ids)==len(set(ids))
    code=[c for c in cells if c['cell_type']=='code'];assert len(code)==1 and code[0]['execution_count']==1
    assert code[0]['outputs'] and all(o['output_type']!='error' for o in code[0]['outputs'])
    assert 'Completed:' in ''.join(code[0]['outputs'][0]['text'])
    attachments=[]
    for i,c in enumerate(cells):
        if 'attachments' not in c:continue
        for name,types in c['attachments'].items():
            raw=base64.b64decode(types['image/png']);assert raw==(ROOT/'figures'/name).read_bytes()
            Image.open(io.BytesIO(raw)).verify();num=int(re.search(r'figure_(\d+)',name).group(1))
            assert ''.join(cells[i+1]['source']).strip().startswith(f'Figure {num}.')
            assert (ROOT/'figures'/name.replace('.png','.svg')).stat().st_size>1000
            attachments.append(num)
    assert attachments==list(range(29,34))
    source=(ROOT/'research/comparison_methodology.md').read_text()
    template=(ROOT/'research/comparison_methodology_template.md').read_text()
    for key,val in json.loads((ROOT/'results/comparison_report_tables.json').read_text()).items():template=template.replace('{{'+key+'}}',val)
    assert source==template and not re.search(r'\{\{[A-Z_]+\}\}',source)
    equations=list(map(int,re.findall(r'\\tag\{(\d+)\}',source)))
    tables=list(map(int,re.findall(r'^Table (\d+)\.',source,re.M)))
    figures=list(map(int,re.findall(r'^Figure (\d+)\.',source,re.M)))
    assert equations==list(range(41,47));assert tables==list(range(31,37));assert figures==attachments
    registers=(ROOT/'research/paper_registers.md').read_text();counts={}
    for kind,n in [('figures',33),('tables',36),('equations',46)]:
        part=registers.split('## List of '+kind)[1].split('\n## ')[0]
        actual=list(map(int,re.findall(r'^\| (\d+) \|',part,re.M)));assert actual==list(range(1,n+1));counts[kind]=n
    refs=(ROOT/'research/references.md').read_text()
    assert list(map(int,re.findall(r'^\[(\d+)\]',refs,re.M)))==list(range(1,24))
    assert 'Bank of England' in refs and '[23]' in source
    docs=['research/comparison_methodology.md','research/development_reflection.md','research/references.md',
          'research/paper_registers.md','research/project_roadmap.md','research/empirical_input_guide.md','research/data_access_status.md','README.md']
    texts=[(ROOT/name,(ROOT/name).read_text()) for name in docs]
    texts.extend((ROOT/'10_empirical_comparison.ipynb',''.join(c['source'])) for c in cells if c['cell_type']=='markdown')
    for path,text in texts:
        for target in re.findall(r'\]\(([^\s)]+)\)',text):
            if ':' in target or target.startswith('#'):continue
            assert (path.parent/target.split('#')[0]).exists(),(path,target)
    preserved=json.loads((ROOT/'results/milestone10_preserved_sha256.json').read_text())
    assert len(preserved)==12
    for name,h in preserved.items():assert digest(ROOT/name)==h,name
    first=json.loads((ROOT/'01_synthetic_density.ipynb').read_text())['cells']
    figure_index=next(i for i,c in enumerate(first) if c['cell_type']=='code' and 'figure_04_noise_sensitivity.png' in ''.join(c['source']))
    assert ''.join(first[figure_index+1]['source']).startswith('Figure 4.')
    assert ''.join(first[figure_index+2]['source']).startswith('Figure 4 introduces')
    verification=json.loads((ROOT/'data/raw/marking_prices/source_verification.json').read_text())
    for v in verification:assert digest(ROOT/'data/raw/marking_prices'/v['filename'])==v['uploaded_sha256']
    numerical=json.loads((ROOT/'results/comparison_summary.json').read_text())
    assert numerical['case_accounting']['solved_qp_cases']==16 and len(numerical['case_accounting']['blocked_cases'])==2
    assert numerical['case_accounting']['risk_extreme_lp_count']==72
    for name,h in numerical['code_sha256'].items():assert digest(ROOT/name)==h
    assert digest(ROOT/'results/comparison_protocol.json')==numerical['protocol_sha256']
    browser=json.loads((ROOT/'results/comparison_browser_checks.json').read_text())
    assert browser['offline'] and not browser['javascript_errors'] and not browser['external_requests']
    tests=(ROOT/'results/comparison_tests.log').read_text();assert 'Ran 84 tests' in tests and tests.strip().endswith('OK')
    files=['10_empirical_comparison.ipynb','interactive/dated_density_surface.html','src/comparison.py','run_comparison.py',
        'build_comparison_report.py','build_comparison_html.py','build_milestone10_notebook.py','tests/test_comparison.py',
        'tests/check_comparison.cjs','check_milestone10_delivery.py',*docs]
    output={'notebook':'10_empirical_comparison.ipynb','code_cells_executed':1,'notebook_structure_checked':True,
        'formal_nbformat_schema_validation':False,'embedded_figures_verified':len(attachments),'captions_below_figures':True,
        'equation_numbers':equations,'figure_numbers':figures,'table_numbers':tables,'register_counts':counts,'reference_count':23,
        'new_notebook_and_updated_document_links_resolve':True,'templates_match_rendered_markdown':True,
        'nine_previous_notebooks_and_three_explorers_unchanged':True,'figure_4_caption_then_explanation_preserved':True,
        'uploaded_csv_bytes_preserved':True,'tests_passed':84,'test_log':'comparison_tests.log',
        'numerical_summary':'comparison_summary.json','unaccepted_cases_explicit':numerical['case_accounting']['blocked_cases'],
        'browser_checks':'comparison_browser_checks.json','browser_check_count':len(browser['checks']),
        'file_sha256':{name:digest(ROOT/name) for name in files}}
    (ROOT/'results/milestone10_delivery_checks.json').write_text(json.dumps(output,indent=2)+'\n')
    print('Verified: executed notebook, five embedded figures, captions, 46-equation/33-figure/36-table registers, 23 references, links, 84 tests, browser checks and preserved artifacts.')
    return output


if __name__=='__main__':main()
