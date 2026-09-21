"""Build a self-contained offline explorer from saved experiment output."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLOTLY_SHA256 = "122e3be346d66616944d0b83eaaf7242581508c3c1cfa0995a17af0d83eff770"


def main():
    vendor = ROOT / "interactive/vendor/plotly-3.1.0.min.js"
    if hashlib.sha256(vendor.read_bytes()).hexdigest() != PLOTLY_SHA256:
        raise RuntimeError("Plotly bundle checksum differs from the reviewed version.")
    data = json.loads((ROOT / "results/maturity_surface.json").read_text())
    template = (ROOT / "interactive/surface_template.html").read_text()
    replacements = {
        "__PLOTLY_BUNDLE__": vendor.read_text().replace("</script", "<\\/script"),
        "__EXPERIMENT_DATA__": json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c"),
        "__PLOTLY_LICENSE__": (ROOT / "interactive/vendor/PLOTLY-LICENSE.txt").read_text(),
    }
    for marker, value in replacements.items():
        if template.count(marker) != 1:
            raise RuntimeError(f"Expected exactly one template marker: {marker}")
        template = template.replace(marker, value)
    output = ROOT / "interactive/density_surface.html"
    output.write_text(template)
    print(f"Built {output.name}: {output.stat().st_size:,} bytes; no external scripts or data required.")
    return output


if __name__ == "__main__":
    main()
