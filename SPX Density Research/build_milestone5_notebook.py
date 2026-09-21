"""Build Notebook 5, execute its runner and embed the numbered figures."""
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
    cells = []

    def markdown(text):
        cells.append({"cell_type": "markdown", "id": f"joint-{len(cells):02}",
                      "metadata": {}, "source": text.splitlines(keepends=True)})

    markdown("# Notebook 5: fitting the maturities together\n\n"
             "This controlled experiment reuses the saved synthetic inputs from Notebook 4. "
             "The executable cell rebuilds the independent control, joint fit, Figures 12–14 and offline explorer. "
             "Open `interactive/joint_density_surface.html` to explore the comparison. "
             "The first four notebooks are unchanged. Rerun this builder after changing the experiment to refresh the embedded figures.\n")
    source = (ROOT / "research/joint_methodology.md").read_text()
    source = source.replace("(../interactive/", "(interactive/")
    marker = "Table 9. Calendar consistency and recovery accuracy"
    before, after = source.split(marker, 1)
    markdown(before)
    code = ("from run_joint import main\nfrom build_joint_html import main as build_explorer\n"
            "result = main()\nexplorer = build_explorer()\n")
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        exec(compile(code, "<notebook-5-cell>", "exec"), {})
    cells.append({"cell_type": "code", "id": "joint-runner", "metadata": {},
                  "source": code.splitlines(keepends=True), "execution_count": 1,
                  "outputs": [{"output_type": "stream", "name": "stdout", "text": stream.getvalue()}]})
    for part in re.split(r"(!\[[^\]]*\]\(\.\./figures/[^)]+\))", marker + after):
        match = re.fullmatch(r"!\[([^\]]*)\]\(\.\./figures/([^)]+)\)", part)
        if not match:
            if part.strip():
                markdown(part)
            continue
        alt, name = match.groups()
        markdown(f"![{alt}](attachment:{name})\n")
        cells[-1]["attachments"] = {name: {"image/png": base64.b64encode((ROOT / "figures" / name).read_bytes()).decode()}}
    notebook = {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": sys.version.split()[0]},
        "project_execution": {"method": "Python runner executed directly; figures embedded as Markdown attachments",
                              "data_kind": "synthetic", "historical_animation": False}},
        "nbformat": 4, "nbformat_minor": 5}
    (ROOT / "05_joint_density.ipynb").write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
    print("Notebook 5 built with executed calculations and embedded Figures 12–14.")


if __name__ == "__main__":
    main()
