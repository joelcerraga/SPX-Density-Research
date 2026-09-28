#!/usr/bin/env python3
"""Verify the website without rerunning or changing the scientific project."""

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import struct
import subprocess
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

import build_site

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "6a0cd7c658b337f9ccc53eca2f423e4e77b2c325"
PAGES = [ROOT / "index.html", ROOT / "explorers/index.html"]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.links = []
        self.images = []
        self.ids = []
        self.meta = {}
        self.canonical = None
        self.h1_count = 0
        self.language = None
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "html":
            self.language = attrs.get("lang")
        if tag == "h1":
            self.h1_count += 1
        if tag == "meta":
            self.meta[attrs.get("name") or attrs.get("property")] = attrs.get("content")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "img":
            self.images.append(attrs)
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def resolve_local(page, url):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return None, None
    require(" " not in url, f"Unencoded space in URL: {url}")
    target = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
    require(target.is_relative_to(ROOT), f"Link leaves the project: {url}")
    if target.is_dir():
        target /= "index.html"
    return target, unquote(parsed.fragment)


def verify_pages():
    parsed = {p: Page(p) for p in PAGES}
    links = 0
    images = 0
    for path, page in parsed.items():
        relative = path.relative_to(ROOT)
        require(page.language == "en-GB", f"Page language: {relative}")
        require(page.h1_count == 1, f"Expected one main heading: {relative}")
        require(len(page.ids) == len(set(page.ids)), f"Duplicate IDs: {relative}")
        require({"main", "site-nav"}.issubset(page.ids), f"Missing navigation targets: {relative}")
        canonical = build_site.BASE + ("explorers/" if path.parent.name == "explorers" else "")
        require(page.canonical == canonical, f"Canonical URL: {relative}")
        require(page.meta.get("og:url") == canonical, f"Social URL: {relative}")
        require(page.meta.get("og:image") == build_site.BASE + build_site.COVER, f"Social image: {relative}")
        require(page.meta.get("twitter:card") == "summary_large_image", f"Social card: {relative}")
        require(bool(page.meta.get("description")), f"Missing description: {relative}")
        for url in page.links:
            target, fragment = resolve_local(path, url)
            if target is None:
                continue
            require(target.is_file(), f"Missing target from {relative}: {url}")
            if fragment:
                target_page = parsed.get(target) or Page(target)
                require(fragment in target_page.ids, f"Missing fragment: {url}")
            links += 1
        for img in page.images:
            require("alt" in img, f"Image missing alternative text: {relative}")
            require(img.get("width") and img.get("height"), f"Image missing dimensions: {relative}")
            target, _ = resolve_local(path, img["src"])
            if target and target.suffix == ".png":
                raw = target.read_bytes()[:24]
                require(raw[:8] == b"\x89PNG\r\n\x1a\n", f"Invalid PNG: {target.name}")
                size = struct.unpack(">II", raw[16:24])
                require(size == (int(img["width"]), int(img["height"])), f"Wrong preview dimensions: {target.name}")
            images += 1
        expected = {ROOT / build_site.ARCHIVE / "interactive" / item["file"] for item in build_site.EXPLORERS}
        destinations = {resolve_local(path, url)[0] for url in page.links}
        require(expected.issubset(destinations), f"Not all original graph URLs are linked: {relative}")
    metrics = json.loads((ROOT / build_site.ARCHIVE / "results/comparison_display_metrics.json").read_text())
    html = PAGES[0].read_text()
    for value in (metrics["primary_spread_quote_count"], metrics["primary_outside_count"]):
        require(f"<strong>{value:,}</strong>" in html, "Displayed count differs from retained results")
    require("held-out" in html.lower() and "unresolved" in html.lower(), "Missing final validation qualifications")
    require(PAGES[0].read_text() == build_site.landing(), "Landing page needs rebuilding")
    require(PAGES[1].read_text() == build_site.gallery(), "Gallery needs rebuilding")
    sitemap = ET.parse(ROOT / "sitemap.xml")
    urls = [node.text for node in sitemap.findall(".//{*}loc")]
    require(urls == [build_site.BASE, build_site.BASE + "explorers/"], "Sitemap destinations")
    require((ROOT / ".nojekyll").exists(), "Static Pages marker missing")
    return {"pages": len(PAGES), "local_link_occurrences": links, "image_occurrences": images}


def verify_archive():
    if not (ROOT / ".git").exists():
        return {"status": "not checked", "reason": "Git history is unavailable in this downloaded copy"}
    result = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", BASELINE, "--", build_site.ARCHIVE, build_site.COVER],
        cwd=ROOT, capture_output=True, check=True,
    )
    checked = 0
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, expected = metadata.split()
        require(kind == b"blob", f"Unexpected archived entry: {name!r}")
        path = ROOT / name.decode()
        require(path.is_file(), f"Archived file removed: {path.relative_to(ROOT)}")
        content = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        require(actual == expected.decode(), f"Archived file changed: {path.relative_to(ROOT)}")
        checked += 1
    require(checked > 1000, "Archive baseline was incomplete")
    return {"status": "byte-for-byte unchanged", "files_checked": checked, "baseline_commit": BASELINE}


if __name__ == "__main__":
    report = {"website": verify_pages(), "archive": verify_archive()}
    print(json.dumps(report, indent=2))
