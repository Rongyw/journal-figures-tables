---
name: journal-figures-tables
description: House style for every figure and table produced for papers, memos, proposals or slides — top-economics-journal (AER/QJE) look. Use whenever generating or restyling a chart, regression table, descriptive table or LaTeX float (matplotlib, pyfixest/statsmodels output, pandas tables, .tex tables, figure captions/notes), in any project.
---

# Journal-style figures and tables (AER / QJE look)

Every figure and table follows this style unless the user explicitly asks for another one.
Reference implementation: `assets/paper_output.py`. LaTeX typography: `assets/aer_preamble.tex`.
Template that compiles all floats: `assets/preview_template.tex`. Example of a finished table: `assets/example_table.tex`.

## Workflow
1. Put `paper_output.py` in the project's analysis package, or reuse the existing copy. In the AI-Electricity project it already
   lives at `data/03_code/analysis/paper_output.py`. Set `FIG`/`TAB` to the project's output folders.
2. Estimation scripts write results to **CSV first**. A separate `render_*()` function reads the CSV and writes the `.tex`.
   Restyling then never requires re-estimation.
3. Write every figure as **PDF (for LaTeX) + PNG (for preview)** through `savefig(fig, subdir, name)`, and every table as
   **`.tex` + `.csv`**.
4. Keep a `preview_*.tex` that `\input`s all tables and `\includegraphics` all figures. Compile it with pdflatex and
   **look at the rendered pages** (pdftoppm → PNG → Read) before reporting. Require 0 errors and no overfull floats.
5. File names: `tab_<n or design>_<short>.tex|csv`, `fig_<n or design>_<short>.pdf|png`, grouped in topic subfolders.

## Tables
Layout, from top to bottom:
- **Caption above the table**, in small caps and centered, rendered as `TABLE 2---Title in Title Case`
  (`\captionsetup` in `aer_preamble.tex`: `labelsep=aerdash, font={small,sc}`). Do not put a period at the end.
- **Double top rule**:
  `\specialrule{0.4pt}{0pt}{1.2pt}\specialrule{0.4pt}{0pt}{\belowrulesep}` (constant `TOPRULE`).
- **Column header block**:
  - grouped headers spanning columns, with `\cmidrule(lr){a-b}` under each non-empty group;
  - then the outcome / variable names;
  - then the column numbers `(1) (2) ...`.
  - The first (stub) column is left-aligned; data columns are centered.
- `\midrule` under the header.
- **Panels**: an italic title on its own row (`\multicolumn{k+1}{l}{\textit{Panel A. ...}}`), and
  `\addlinespace[6pt]` between panels. Do not draw a rule between panels.
- **Coefficient rows**: the estimate with stars in math mode (`$0.421^{*}$`). On the next row, the **standard error in
  brackets** `[0.230]`. Use 3 decimals by default.
- **Summary rows** (`\addlinespace` before them): mean of dependent variable, counts (treated, controls, clusters), observations with
  thousands separators.
- **Fixed-effect block** after a `\midrule`: rows such as `Utility fixed effects & Yes & Yes ...`.
- **Single bottom rule** (`\bottomrule`).
- **Notes** in `threeparttable` `tablenotes[flushleft]` at `\footnotesize`, starting with `\textit{Notes:}`. The notes state:
  - the dependent variable;
  - the sample and period;
  - the treatment definition;
  - the estimator;
  - the clustering;
  - and end with "Standard errors in brackets. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$."
- Wrap the table as `table[!htbp]` → `\small` → `adjustbox{max width=\textwidth}` **outside** `threeparttable` → `tabular`.
  Never put adjustbox inside threeparttable, which causes a "Missing \endgroup" error. Do not set a TPT minimum width, so that
  the notes match the table width.
- Packages: `booktabs, threeparttable, adjustbox, caption`.
- Do not use vertical rules, colored cells or bold numbers.
- Use `---` for an empty or not-applicable entry. Leave a cell blank when the estimate is not identified (Poisson separation:
  treat |b| > 8 as not identified), and say so in the notes.
- Descriptive tables use the same frame (`latex_frame(df, ..., group_col=...)`): a header row of column names, italic panel
  groups and notes.
- Escape LaTeX in any text that comes from data (`tex_escape`).
- When writing `.tex` from Python, use raw strings or `\\` so that `\t` in `\textit` does not become a tab. Patch files with
  small Python scripts or the Edit tool, not shell heredocs with backslashes.

## Figures
- Use `set_style()`:
  - serif font (Times New Roman → Times → DejaVu Serif), `mathtext.fontset='stix'`;
  - font size 10 (ticks 9, legend 8);
  - remove the top and right spines; axis line width 0.6; line width 1.2;
  - legend without frame;
  - `savefig.bbox='tight'`, 300 dpi.
- **Greyscale palette** (`GREYS = #000000, #5a5a5a, #9a9a9a, #c8c8c8`). Distinguish series by line style (`-`, `--`, `:`),
  marker or hatch, never by color alone, so that figures print in black and white.
- Panel titles go **at the top left**: `ax.set_title('A. Event: tariff approval', loc='left')`. Do not put a suptitle or
  title inside the figure; the caption carries the title.
- Event studies use `event_plot()`:
  - black points with 95% CI caps;
  - the reference period (−1) drawn as an open marker at zero;
  - a horizontal zero line in light grey;
  - a dashed vertical line at −0.5.
  - The x label is "Quarters relative to event"; the y label states the units ("Coefficient (log points)").
- Policy dates are dashed vertical lines in grey `0.4`. Axis labels carry units ("GW", "MWh (2017 = 100)"). Use a log scale only
  when it is labelled.
- Sizes: one-panel 4.5×3.2 in; two-panel 9×3.4 in; multi-panel grids share a legend placed below them.
- In LaTeX:
  - `figure[!htbp]`, caption **above** the graphic, in the same small-caps style (`FIGURE 1---Title`);
  - then `\includegraphics[width=\textwidth]{...pdf}`;
  - then a `minipage` with `\footnotesize \textit{Notes:}` giving the estimator, fixed effects, CI level, clustering, reference
    period, sample and sources.

## Slides (beamer)
Reuse the same PDFs. Tables on slides are simplified booktabs tables (estimate, p-value, one-line reading). Do not paste the full
regression tables onto slides.

## Checklist before reporting
- [ ] CSV and `.tex` (or PDF and PNG) both written.
- [ ] The caption is in Title Case, with no trailing period, and the label is set.
- [ ] Double top rule, rule under the header, italic panels, bracketed SEs, FE block, single bottom rule.
- [ ] The notes define the dependent variable, sample, treatment, estimator and clustering, and include the star legend.
- [ ] Greyscale, readable in black and white; panel letters at the top left.
- [ ] The preview compiles; pages were looked at; no overfull boxes.
