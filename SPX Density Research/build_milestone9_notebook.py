"""Execute the synthetic acceptance exercise and first empirical case together."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
PREPARATION_CODE=("from run_empirical_preparation import main as prepare_fixture\n"
    "from build_empirical_report import main as build_fixture_report\n"
    "fixture_result = prepare_fixture()\nfixture_tables = build_fixture_report()\n")
MARKET_CODE=("from run_marking_calibration import main as calibrate_market\n"
    "from run_marking_diagnostic import main as diagnose_range\n"
    "from build_marking_report import main as build_market_report\n"
    "from build_marking_html import main as build_market_explorer\n"
    "market_result = calibrate_market()\nrange_diagnostic = diagnose_range()\n"
    "market_tables = build_market_report()\nexplorer_path = build_market_explorer()\n")


def main():
    os.chdir(ROOT);sys.path.insert(0,str(ROOT));cells=[]
    def markdown(text):
        text=text.replace("](../","](")
        text=re.sub(r'\]\(([a-z_]+\.md)\)',r'](research/\1)',text)
        cells.append({"cell_type":"markdown","id":f"empirical-{len(cells):02}","metadata":{},"source":text.splitlines(keepends=True)})
    def execute(code,count):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):exec(compile(code,f"<notebook-9-cell-{count}>","exec"),{})
        print(stream.getvalue(),end="")
        cells.append({"cell_type":"code","id":f"empirical-runner-{count}","metadata":{},
            "source":code.splitlines(keepends=True),"execution_count":count,
            "outputs":[{"output_type":"stream","name":"stdout","text":stream.getvalue().splitlines(keepends=True)}]})
    def narrative(template,tables,output):
        source=(ROOT/"research"/template).read_text()
        for key,value in json.loads((ROOT/"results"/tables).read_text()).items():source=source.replace("{{"+key+"}}",value)
        if re.search(r"\{\{[A-Z_]+\}\}",source):raise ValueError("Unresolved narrative placeholder")
        (ROOT/"research"/output).write_text(source)
        for part in re.split(r"(!\[[^\]]*\]\(\.\./figures/[^)]+\))",source):
            match=re.fullmatch(r"!\[([^\]]*)\]\(\.\./figures/([^)]+)\)",part)
            if match:
                alt,name=match.groups();markdown(f"![{alt}](attachment:{name})\n")
                cells[-1]["attachments"]={name:{"image/png":base64.b64encode((ROOT/"figures"/name).read_bytes()).decode()}}
            elif part.strip():markdown(part)
    markdown("# Notebook 9: empirical preparation and first SPX calibration\n\n"
        "**Part A is a synthetic acceptance exercise. Part B fits actual exchange bid–ask observations from "
        "18 September 2026 using quote-implied discount and forward inputs.** The first market case is complete, "
        "with spread misses and tail sensitivity reported explicitly. The original filename is retained for continuity.\n\n"
        "Run `python build_milestone9_notebook.py` from the extracted project folder to recompute both parts, "
        "update figures and prose, and rebuild the offline 3D companion from archived inputs. "
        "No network access is needed. Earlier notebooks remain preserved.\n")
    execute(PREPARATION_CODE,1)
    narrative("empirical_methodology_template.md","empirical_preparation_tables.json","empirical_methodology.md")
    markdown("# Part B: observed SPXW quotes\n\nThe following cell runs the primary empirical protocol, "
        "then the explicitly labelled post-hoc range diagnostic. The narrative below records their distinct roles.\n")
    execute(MARKET_CODE,2)
    narrative("marking_methodology_template.md","marking_report_tables.json","marking_methodology.md")
    notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python","version":sys.version.split()[0]},
        "project_execution":{"method":"Two Python code cells executed directly; all fixture and empirical fits recomputed",
            "data_kind":"synthetic_fixture_and_market_exchange_bbo","empirical_calibration_completed":True,
            "empirical_observation_date":"2026-09-18","historical_animation":False}},"nbformat":4,"nbformat_minor":5}
    (ROOT/"09_empirical_preparation.ipynb").write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+"\n")
    print("Notebook 9 built: Figures 24–28, Tables 22–30 and Equations (34)–(40).")


if __name__=="__main__":main()
