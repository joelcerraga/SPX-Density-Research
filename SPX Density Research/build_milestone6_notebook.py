"""Execute the study, generate its result text, and embed Figures 15–17."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def results_commentary(report):
    normal = report["benchmarks"]["lognormal"]["cases"]
    mix = report["benchmarks"]["mixture"]["cases"]
    coarse, fine = normal["coarse"], normal["fine"]
    narrow, wide = mix["narrow"]["marginals"][-1], mix["wide"]["marginals"][-1]
    rmse = [c["pooled_withheld_price_rmse"] for c in mix.values()]
    l1 = [c["mean_full_density_l1"] for c in mix.values()]
    return (f'For the single-lognormal benchmark, changing from 80 to 160 bins changes pooled withheld-price RMSE '
            f'from {coarse["pooled_withheld_price_rmse"]:.6f} to {fine["pooled_withheld_price_rmse"]:.6f} index points, '
            f'while mean full-domain density error changes from {coarse["mean_full_density_l1"]:.6f} '
            f'to {fine["mean_full_density_l1"]:.6f}. This illustrates the different sensitivity of the two metrics; '
            'two grid alternatives do not establish a general convergence rate.\n\n'
            f'Across the mixture cases, pooled price RMSE ranges from {min(rmse):.6f} to {max(rmse):.6f} '
            f'index points and mean full-domain density error from {min(l1):.6f} to {max(l1):.6f}. '
            f'At 365 days, the known mixture probability outside the narrow support is '
            f'{100*narrow["density_error"]["outside_support_probability"]:.4f}%, compared with '
            f'{100*wide["density_error"]["outside_support_probability"]:.4f}% outside the wide support. '
            'Both supports contain every supplied strike. The difference therefore concerns unobserved terminal outcomes, '
            'not deletion of quoted options. A wider support permits more possible outcomes but does not by itself establish '
            'that the estimated allocation of their probability is accurate.')


def numerical_commentary(report):
    cases=[c for b in report["benchmarks"].values() for c in b["cases"].values()]
    marginals=[m for c in cases for m in c["marginals"]]
    gap=min(c["calendar"]["minimum_gap"] for c in cases)
    mass=max(abs(m["mass"]-1) for m in marginals)
    mean=max(abs(m["risk"]["normalised_mean"]-1) for m in marginals)
    minimum=min(m["minimum_bin_mass"] for m in marginals)
    integration=max(c["maximum_quadrature_error_estimate"] for c in cases)
    iterations=max(h["iterations"] for c in cases for h in c["solver"]["history"])
    bindings=max(h["maximum_residual_equation_error"] for c in cases for h in c["solver"]["history"])
    duality=max(h["scaled_duality_gap"] for c in cases for h in c["solver"]["history"])
    return (f'All {report["case_count"]} joint fits pass the interval-level calendar check at $10^{{-8}}$, '
            f'with a worst minimum gap of approximately {gap:.3e}. Across the {report["marginal_count"]} marginal distributions, '
            f'the largest mass and normalised-mean residuals are {mass:.3e} and {mean:.3e}; '
            f'the smallest raw bin mass is {minimum:.3e}. Signed numerical residuals are retained without clipping or renormalisation.\n\n'
            f'Every accepted solver round reports `Solved`; the largest iteration count in a round is {iterations:,}. '
            f'The maximum mismatch in the added residual-variable equations is {bindings:.3e}. '
            f'The largest absolute primal–dual objective gap on the scaled problem is {duality:.3e}. '
            f'The largest density-integration error estimate is {integration:.3e}, below the requested '
            '$2\\times10^{-7}$ threshold. These estimates are convergence diagnostics, not rigorous integration bounds. '
            'The full solver and integration records remain in `results/robustness_validation.json`.')


def tail_commentary(report):
    parts=[]
    for key,label in [("lognormal","single-lognormal"),("mixture","mixture")]:
        rows=[c["marginals"][-1] for c in report["benchmarks"][key]["cases"].values()]
        values=[100*r["risk"]["above_1_8_forward"] for r in rows]
        known=100*rows[0]["known_risk"]["above_1_8_forward"]
        moderate=max(100*abs(r["risk"][f]-r["known_risk"][f]) for r in rows
                     for f in ["below_0_8_forward","above_1_2_forward"])
        parts.append(f'For the {label} benchmark at 365 days, the known probability above $1.8F$ is '
                     f'{known:.4f}%, while fitted values range from {min(values):.4f}% to {max(values):.4f}%. '
                     f'The largest absolute error across the two moderate-threshold probabilities is '
                     f'{moderate:.4f} percentage points within these seven settings.')
    parts.append('The far-tail estimates therefore require particular caution even though every fitted family passes the '
                 'calendar check. For the mixture, every fitted normalised variance in Table 13 is below the known value, '
                 'despite the overestimated probability above $1.8F$. A single tail-event probability does not determine '
                 'variance: where probability is allocated farther into the tail also matters.')
    return "\n\n".join(parts)


def main(refresh_narrative=False):
    os.chdir(ROOT)
    sys.path.insert(0,str(ROOT))
    code = "from run_robustness import main\nresult = main()\n"
    if refresh_narrative:
        existing=json.loads((ROOT/"06_density_robustness.ipynb").read_text())
        executed_cell=next(c for c in existing["cells"] if c["cell_type"]=="code")
        if "".join(executed_cell["source"]) != code:
            raise ValueError("The runner cell changed; rebuild the numerical study instead.")
        report=json.loads((ROOT/"results/robustness_validation.json").read_text())
    else:
        original_stdout=sys.stdout
        class Capture(io.StringIO):
            def write(self,text):
                original_stdout.write(text)
                original_stdout.flush()
                return super().write(text)
        stream=Capture()
        namespace={}
        with contextlib.redirect_stdout(stream):
            exec(compile(code,"<notebook-6-cell>","exec"),namespace)
        report=namespace["result"]
        executed_cell={"cell_type":"code","id":"robustness-runner","metadata":{},"source":code.splitlines(keepends=True),
                       "execution_count":1,"outputs":[{"output_type":"stream","name":"stdout","text":stream.getvalue()}]}
    replacements=json.loads((ROOT/"results/robustness_tables.json").read_text())
    replacements.update(RESULTS_COMMENTARY=results_commentary(report),NUMERICAL_COMMENTARY=numerical_commentary(report),
                        TAIL_COMMENTARY=tail_commentary(report))
    source=(ROOT/"research/robustness_methodology_template.md").read_text()
    for key,value in replacements.items(): source=source.replace("{{"+key+"}}",value)
    if re.search(r"\{\{[A-Z_]+\}\}",source): raise ValueError("Unresolved methodology placeholder.")
    (ROOT/"research/robustness_methodology.md").write_text(source)
    cells=[]
    def markdown(text):
        text=text.replace("](development_reflection.md)","](research/development_reflection.md)")
        cells.append({"cell_type":"markdown","id":f"robustness-{len(cells):02}","metadata":{},"source":text.splitlines(keepends=True)})
    markdown("# Notebook 6: how stable are the recovered densities?\n\n"
             "This notebook compares support, resolution and smoothing choices on two synthetic benchmarks. "
             "The code cell reruns all 14 joint fits and can take several minutes. "
             "Rerun `build_milestone6_notebook.py` to refresh the generated text, tables and embedded figures together. "
             "The first five notebooks and both earlier interactive companions are unchanged.\n")
    before,after=source.split("Table 12. Recovery accuracy",1)
    markdown(before)
    cells.append(executed_cell)
    for part in re.split(r"(!\[[^\]]*\]\(\.\./figures/[^)]+\))","Table 12. Recovery accuracy"+after):
        match=re.fullmatch(r"!\[([^\]]*)\]\(\.\./figures/([^)]+)\)",part)
        if not match:
            if part.strip(): markdown(part)
            continue
        alt,name=match.groups();markdown(f"![{alt}](attachment:{name})\n")
        cells[-1]["attachments"]={name:{"image/png":base64.b64encode((ROOT/"figures"/name).read_bytes()).decode()}}
    notebook={"cells":cells,"metadata":{
        "kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python","version":sys.version.split()[0]},
        "project_execution":{"method":"Python runner executed directly; figure PNGs embedded as Markdown attachments",
                             "data_kind":"synthetic","historical_animation":False}},"nbformat":4,"nbformat_minor":5}
    (ROOT/"06_density_robustness.ipynb").write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+"\n")
    print("Notebook 6 narrative refreshed from the saved run; numerical results and execution output retained."
          if refresh_narrative else "Notebook 6 built with executed calculations, generated tables and embedded Figures 15–17.")


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-narrative",action="store_true",help="Refresh prose and embedded figures from existing results without refitting.")
    main(parser.parse_args().refresh_narrative)
