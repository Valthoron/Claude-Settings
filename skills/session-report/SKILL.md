---
name: session-report
description: Produce a PDF report of a working session using Typst for the document and Graphviz for flowcharts and diagrams. Use whenever the user asks for a session summary, session report, work log, handover document, or design write-up as a PDF, or asks to document what was done in a session as a shareable file. Also use when a report already produced by this skill needs to be regenerated or amended.
---

# Session report

Builds a PDF from a Typst source file, with diagrams rendered separately by Graphviz and embedded as PDF images.

## Requirements

- `typst` 0.14.0 or newer (PDF images are used; earlier versions cannot embed them)
- `dot` from Graphviz

Check with `typst --version` and `dot -V` before the first build in a repository. If either is missing, say so and stop.

## Layout

Create everything under `report/`, relative to the repository root unless the user names another location:

```
report/
  report.typ
  diagrams/
    <name>.dot
    <name>.pdf
  report.pdf
```

Generated `.pdf` files under `diagrams/` are build output. Add `report/diagrams/*.pdf` and `report/report.pdf` to `.gitignore` only if the repository already ignores build output; otherwise ask.

## Build

One diagram at a time:

```
dot -Tpdf report/diagrams/<name>.dot -o report/diagrams/<name>.pdf
```

Then the document:

```
typst compile report/report.typ report/report.pdf
```

Compile after writing, and report the compiler's own errors verbatim rather than paraphrasing them. Do not open the PDF.

## Diagrams

Write one `.dot` file per diagram. Graphviz does the layout; never hand-place nodes.

```dot
digraph <name> {
  rankdir=TB;
  bgcolor="transparent";
  node [shape=box, style=rounded, fontname="Helvetica", fontsize=10];
  edge [fontname="Helvetica", fontsize=9];

  start [label="Start", shape=ellipse];
  check [label="Valid?", shape=diamond];

  start -> check;
  check -> start [label="no"];
}
```

Conventions:

- `rankdir=LR` for pipelines and data flow, `rankdir=TB` for control flow and decision trees.
- `bgcolor="transparent"` always, so the diagram sits on the page fill.
- Fonts are resolved by Graphviz, not Typst. Helvetica is safe on both Windows and macOS.
- Use `subgraph cluster_<name>` for grouping only when the grouping carries meaning.
- A diagram earns its place by showing structure that prose cannot. Do not draw a flowchart of a linear three-step process.
- Wide graphs overflow the text block. If a diagram exceeds roughly 12 nodes across, split it or switch to `rankdir=LR` on a landscape page (`#page(flipped: true)[...]`).

## Document

`report.typ` starts from this preamble:

```typst
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "Libertinus Serif", size: 10pt, lang: "en")
#set heading(numbering: "1.1")
#show raw: set text(font: "DejaVu Sans Mono", size: 9pt)
#show link: set text(fill: blue.darken(20%))

#let diagram(name, caption) = figure(
  image("diagrams/" + name + ".pdf", width: 90%),
  caption: caption,
)
```

Both fonts ship inside the Typst binary, so the document renders identically on any machine.

Title block, then content:

```typst
#align(center)[
  #text(size: 17pt, weight: "bold")[<title>]
  #v(0.3em)
  <date>
]

= Summary

...

#diagram("build-pipeline", [Build pipeline after the change.])
```

Useful pieces:

- Code: fenced blocks with a language tag; Typst highlights them.
- Tables: `#table(columns: (auto, 1fr), stroke: 0.5pt, ...)`.
- Callouts: `#block(fill: luma(240), inset: 8pt, radius: 3pt)[...]`.
- Contents page: `#outline()` after the title block, for reports past roughly six pages.

## Content

Structure follows the session, not a fixed template. Sections that usually apply, in this order:

1. What was asked for.
2. What changed — the substance, not a file-by-file diff.
3. Decisions and why, including options rejected and the reason.
4. Known problems, unfinished work, and anything left broken.
5. How to verify or run it.

Rules:

- Write what happened. No narration of the process ("first I ..., then I ..."), no self-assessment, no "successfully" or "comprehensive".
- Say plainly what is unfinished or broken. It belongs in the report, not in a follow-up remark.
- Quote identifiers exactly as they appear in the code.
- Do not pad. A short session produces a short report.

## Amending an existing report

Edit `report.typ` in place and recompile. Do not regenerate the file wholesale for a small change, and do not leave notes in the source about what was revised.
