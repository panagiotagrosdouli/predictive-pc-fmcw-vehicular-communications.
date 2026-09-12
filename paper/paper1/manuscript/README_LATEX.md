# Paper 1 LaTeX manuscript

Canonical LaTeX entry point: `main.tex`.

## Build

From `paper/paper1/manuscript/`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

or, when `latexmk` is installed:

```bash
latexmk -pdf main.tex
```

The document uses the standard IEEE `IEEEtran` conference class and BibTeX bibliography `references.bib`.

## Submission metadata

Before external submission, replace the deliberately non-invented placeholders in `main.tex`:

- `Author Name`
- affiliation
- city/country
- email address

Do not change frozen Paper-1 numerical results, holdout seeds, statistical procedures, or claim boundary without regenerating and re-auditing the publication evidence package.

## Scientific source of truth

The LaTeX manuscript is a typeset representation of `PAPER1_FINAL_DRAFT.md` and the frozen Paper-1 package. Publication-facing numerical claims remain traceable to:

- `configs/paper1_final_protocol.json`
- `artifacts/paper1_final/primary_statistics.json`
- `artifacts/paper1_final/publication_manifest.json`
- `paper/paper1/PAPER1_COMPLETION_AUDIT.md`

Paper 2 / WOMD / learned-GRU evidence is intentionally excluded.
