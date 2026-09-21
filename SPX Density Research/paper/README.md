# Final paper

Open `SPX-Option-Implied-Density-Final-Paper.pdf` to read the finished paper, or use the `.docx` version for editing. Both include the title page, abstract, contents, figure/table/equation lists, abbreviations, mathematical symbols with units, integrated research chapters, development reflection, discussion, conclusion and references.

The author's power systems logbook and final-year project report guided typography and document conventions. The chapter sequence follows the SPX investigation. The engineering reports are not financial research sources and are not redistributed in this package.

## Sources and traceability

- `manuscript.md`: integrated narrative and numbered asset markers.
- `assets.json`: the 46 equations, 33 figure paths, 36 research tables and source registers captured from the completed research notes. Numerical table values and figure files are retained.
- `build_paper.py`: produces editable native Word mathematics, numbered headings, captions, internal navigation and the laid-out Word document. Some long expressions are broken across lines without changing their meaning.
- `navigation.json` and `page_map.json`: stable navigation targets and the verified printed page references.
- `verify_paper.py` and `verification.json`: rendered-PDF reconciliation, completeness checks and preservation of earlier files.
- `preserved_inputs_sha256.json`: hashes of the ten notebooks and eight HTML files, including the four viewer templates.

The full development record remains at `../research/development_reflection.md`; Chapter 9 provides the paper's consolidated account. The archived numerical cases retain failures and post-hoc labels. Building the paper does not recompute the experiments.

## Rebuilding the document

Install Python 3.11 or later with `python-docx`, `Pillow` and `PyMuPDF`, plus Pandoc 3.1 or later and a Word-compatible PDF exporter such as LibreOffice. From the extracted project root, run:

```bash
python paper/build_paper.py
```

The builder writes the Word document and intermediate `draft.docx` and `expanded.md` files. Export the finished Word document to PDF with the same fonts and page settings, then reconcile the navigation:

```bash
python paper/verify_paper.py path/to/exported-paper.pdf --update-pages
python paper/build_paper.py
```

Export once more and run the verifier without `--update-pages`. If it reports any navigation changes, repeat the pagination pass. The contents and numbered lists use stable internal links and materialised page values so they remain populated without a Word field refresh. They must be regenerated after edits that change pagination. Main headings use native Word numbering.

Visually inspect the exported pages as well: the verifier cannot replace inspection of mathematical expressions, figures and tables. In the supplied build, single-column native equation arrays avoid an exporter defect with empty alignment cells. No native equation is substituted with a screenshot.

## Interactive companions

Open these files directly in a browser after extracting the cumulative package:

- `../interactive/density_surface.html`
- `../interactive/joint_density_surface.html`
- `../interactive/empirical_density_surface.html`
- `../interactive/dated_density_surface.html`

They include their scripts and data for offline viewing. The paper's static figures remain suitable for printing. Surface joins and the assumed sixty-day mixture retain their stated interpretation; they are not additional market observations.
