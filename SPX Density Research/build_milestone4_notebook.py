"""Build Notebook 4 from its methodology, with executed Python runner output.

No Jupyter kernel is assumed by this build script; figure PNGs are embedded.
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
    cells = []

    def markdown(text):
        cells.append({"cell_type": "markdown", "id": f"surface-{len(cells):02}",
                      "metadata": {}, "source": text.splitlines(keepends=True)})

    markdown("# Notebook 4: multi-maturity densities and dynamic 3D graphs\n\n"
             "This experiment is synthetic. The executable cell rebuilds the data, figures and offline explorer. "
             "Open `interactive/density_surface.html` in a browser for rotation, zoom, hover and maturity selection. "
             "The first three notebooks are unchanged. Rerun this builder after changing the experiment to refresh the embedded figures.\n")
    source = (ROOT / "research/surface_methodology.md").read_text()
    source = source.replace("(../interactive/", "(interactive/")
    marker = "Table 7. Synthetic validation by expiry horizon."
    before, after = source.split(marker, 1)
    markdown(before)
    code = ("from run_surface import main\nfrom build_surface_html import main as build_explorer\n"
            "result = main()\nexplorer = build_explorer()\n")
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        exec(compile(code, "<notebook-4-cell>", "exec"), {})
    cells.append({"cell_type": "code", "id": "surface-runner", "metadata": {},
                  "source": code.splitlines(keepends=True), "execution_count": 1,
                  "outputs": [{"output_type": "stream", "name": "stdout", "text": stream.getvalue()}]})
    parts = re.split(r"(!\[[^\]]*\]\(\.\./figures/[^)]+\))", marker + after)
    for part in parts:
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
    (ROOT / "04_density_surface.ipynb").write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
    print("Notebook 4 built with executed calculations and embedded Figures 10–11.")


if __name__ == "__main__":
    main()
