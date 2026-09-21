"""Embed verified Plotly and empirical results in an offline scientific explorer."""
import hashlib
import json
from pathlib import Path

from build_surface_html import PLOTLY_SHA256

ROOT=Path(__file__).resolve().parent


def main():
    bundle=(ROOT/"interactive/vendor/plotly-3.1.0.min.js").read_bytes()
    if hashlib.sha256(bundle).hexdigest()!=PLOTLY_SHA256:raise RuntimeError("Plotly checksum mismatch")
    fits=[]
    for filename,role in (("marking_calibration.json","Primary"),("marking_range_diagnostic.json","Post-hoc")):
        report=json.loads((ROOT/"results"/filename).read_text())
        for f in report["full_sample_fits"]:
            fits.append({"penalty":f["penalty"],"role":role,"marginals":[
                {k:m[k] for k in ("expiry","elapsed_days","forward","discount","pair_count","edges","mass",
                    "normalised_strike_range","risk","outside_spread_count","call_midpoint_rmse","put_midpoint_rmse")}
                for m in f["marginals"]]})
    page=(ROOT/"interactive/empirical_surface_template.html").read_text()
    replacements={"__PLOTLY_BUNDLE__":bundle.decode().replace("</script","<\\/script"),
        "__EMPIRICAL_DATA__":json.dumps(fits,separators=(",",":"),allow_nan=False).replace("<","\\u003c"),
        "__PLOTLY_LICENSE__":(ROOT/"interactive/vendor/PLOTLY-LICENSE.txt").read_text()}
    for marker,value in replacements.items():
        if page.count(marker)!=1:raise ValueError(f"Expected one {marker}")
        page=page.replace(marker,value)
    output=ROOT/"interactive/empirical_density_surface.html";output.write_text(page)
    print(f"Built {output.name}; all scripts and fitted data included for offline use.")
    return output


if __name__=="__main__":main()
