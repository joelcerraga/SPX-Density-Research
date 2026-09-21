"""Build the offline comparison without altering the Milestone 4 explorer."""
import hashlib
import json
from pathlib import Path

from build_surface_html import PLOTLY_SHA256

ROOT = Path(__file__).resolve().parent


def main():
    bundle = (ROOT / "interactive/vendor/plotly-3.1.0.min.js").read_bytes()
    if hashlib.sha256(bundle).hexdigest() != PLOTLY_SHA256:
        raise RuntimeError("Plotting dependency checksum mismatch.")
    data = json.loads((ROOT / "results/joint_surface.json").read_text())
    page = (ROOT / "interactive/joint_surface_template.html").read_text()
    for marker, value in {
        "__PLOTLY_BUNDLE__": bundle.decode().replace("</script", "<\\/script"),
        "__EXPERIMENT_DATA__": json.dumps(data, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c"),
        "__PLOTLY_LICENSE__": (ROOT / "interactive/vendor/PLOTLY-LICENSE.txt").read_text(),
    }.items():
        if page.count(marker) != 1:
            raise RuntimeError(f"Expected one template marker {marker}.")
        page = page.replace(marker, value)
    output = ROOT / "interactive/joint_density_surface.html"
    output.write_text(page)
    print(f"Built {output.name}: {output.stat().st_size:,} bytes, self-contained for offline viewing.")
    return output


if __name__ == "__main__":
    main()
