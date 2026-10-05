"""Shared output helpers: journal-style figures (AER/QJE look) and booktabs LaTeX regression tables.

Tables: `latex_table(columns, ...)` writes a self-contained `table` environment (booktabs + threeparttable) with
coefficients, standard errors in parentheses, significance stars, fixed-effect indicator rows and summary rows.
Required LaTeX packages: booktabs, threeparttable, adjustbox (shrinks a table only if it exceeds the text width).
Figures: `set_style()` then `savefig(fig, name)` writes both PDF (for LaTeX) and PNG (for preview).
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

# Portable copy (journal-figures-tables skill). Point FIG/TAB at the project's output folders, e.g. via env vars.
import os  # noqa: E402
FIG = Path(os.environ.get('PAPER_FIG_DIR', 'Results/figures'))
TAB = Path(os.environ.get('PAPER_TAB_DIR', 'Results/tables'))
GREYS = ['#000000', '#5a5a5a', '#9a9a9a', '#c8c8c8']


def set_style() -> None:
    plt.rcParams.update({
        'font.family': 'serif', 'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'], 'mathtext.fontset': 'stix',
        'font.size': 10, 'axes.titlesize': 10, 'axes.labelsize': 10, 'xtick.labelsize': 9, 'ytick.labelsize': 9,
        'legend.fontsize': 8, 'legend.frameon': False, 'axes.spines.top': False, 'axes.spines.right': False,
        'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'lines.linewidth': 1.2,
        'figure.dpi': 150, 'savefig.bbox': 'tight', 'savefig.dpi': 300,
    })


def savefig(fig, subdir: str, name: str) -> Path:
    out = FIG / subdir
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f'{name}.pdf')
    fig.savefig(out / f'{name}.png')
    plt.close(fig)
    return out / f'{name}.pdf'


def event_plot(ax, rel, est, lo, hi, ref: int = -1, xlabel: str = 'Quarters relative to event', ylabel: str = '') -> None:
    """Point estimates with 95% CI bars; reference period drawn as an open marker at zero."""
    ax.axhline(0, color='0.6', lw=0.6)
    ax.axvline(ref + 0.5, color='0.6', lw=0.6, ls='--')
    ax.errorbar(rel, est, yerr=[[e - l for e, l in zip(est, lo)], [h - e for e, h in zip(est, hi)]],
                fmt='o', color='black', ms=3.5, capsize=2, elinewidth=0.8)
    ax.plot([ref], [0], marker='o', mfc='white', mec='black', ms=3.5)
    ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)


def stars(p: float) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return ''
    return '^{***}' if p < 0.01 else '^{**}' if p < 0.05 else '^{*}' if p < 0.1 else ''


def fmt(x: float, d: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ''
    return f'{x:,.{d}f}'


def from_pyfixest(fit, keep: list[str] | None = None) -> dict:
    t = fit.tidy()
    out = {}
    for term, r in t.iterrows():
        if keep is None or term in keep:
            out[term] = (r['Estimate'], r['Std. Error'], r['Pr(>|t|)'])
    return out


def latex_table(columns: list[dict], rows: list[tuple[str, str]], path: Path, caption: str, label: str,
                notes: str, col_groups: list[tuple[str, int]] | None = None, fe_rows: list[str] | None = None,
                stat_rows: list[tuple[str, str, int]] | None = None, digits: int = 3, dep_var_row: str | None = None) -> Path:
    """columns: list of {'coefs': {term: (b, se, p)}, 'fe': {name: bool}, 'stats': {key: value}, 'dep': str}.
    rows: [(term, label)]; fe_rows: names; stat_rows: [(key, label, decimals)]."""
    k = len(columns)
    lines = [r'\begin{table}[!htbp]\centering', rf'\caption{{{caption}}}', rf'\label{{{label}}}', r'\small',
             r'\begin{adjustbox}{max width=\textwidth}', r'\begin{threeparttable}', rf'\begin{{tabular}}{{l*{{{k}}}{{c}}}}', r'\toprule']
    if col_groups:
        lines.append(' & ' + ' & '.join(rf'\multicolumn{{{n}}}{{c}}{{{g}}}' for g, n in col_groups) + r' \\')
        start = 2
        cm = []
        for g, n in col_groups:
            cm.append(rf'\cmidrule(lr){{{start}-{start + n - 1}}}')
            start += n
        lines.append(''.join(cm))
    if dep_var_row:
        lines.append(' & ' + ' & '.join(c.get('dep', '') for c in columns) + r' \\')
    lines.append(' & ' + ' & '.join(f'({i + 1})' for i in range(k)) + r' \\')
    lines.append(r'\midrule')
    for term, lab in rows:
        b = [c['coefs'].get(term) for c in columns]
        if all(x is None for x in b):
            continue
        lines.append(lab + ' & ' + ' & '.join(f'${fmt(x[0], digits)}{stars(x[2])}$' if x else '' for x in b) + r' \\')
        lines.append(' & ' + ' & '.join(f'$({fmt(x[1], digits)})$' if x else '' for x in b) + r' \\[2pt]')
    if fe_rows:
        lines.append(r'\midrule')
        for fe in fe_rows:
            lines.append(fe + ' & ' + ' & '.join(('Yes' if c.get('fe', {}).get(fe) else 'No') if fe in c.get('fe', {}) else ''
                                                for c in columns) + r' \\')
    if stat_rows:
        lines.append(r'\midrule')
        for key, lab, d in stat_rows:
            vals = []
            for c in columns:
                v = c.get('stats', {}).get(key)
                vals.append('' if v is None else (f'{v:,.{d}f}' if isinstance(v, (int, float)) else str(v)))
            lines.append(lab + ' & ' + ' & '.join(vals) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}', r'\begin{tablenotes}[flushleft]\footnotesize',
              rf'\item \textit{{Notes:}} {notes} $^{{*}}p<0.10$, $^{{**}}p<0.05$, $^{{***}}p<0.01$.',
              r'\end{tablenotes}', r'\end{threeparttable}', r'\end{adjustbox}', r'\end{table}']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


# AER/QJE look: double rule under the caption, single rules below the column header and at the bottom, italic panel
# titles, standard errors in brackets. Caption typography (small caps, "TABLE 2---Title") comes from
# Results/latex/aer_preamble.tex.
TOPRULE = r'\specialrule{0.4pt}{0pt}{1.2pt}\specialrule{0.4pt}{0pt}{\belowrulesep}'
STARS_NOTE = r'$^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.'


def _head(caption: str, label: str, colfmt: str) -> list[str]:
    return [r'\begin{table}[!htbp]\centering', rf'\caption{{{caption}}}', rf'\label{{{label}}}', r'\small',
            r'\begin{adjustbox}{max width=\textwidth}', r'\begin{threeparttable}', rf'\begin{{tabular}}{{{colfmt}}}', TOPRULE]


def _tail(notes: str) -> list[str]:
    return [r'\bottomrule', r'\end{tabular}', r'\begin{tablenotes}[flushleft]\footnotesize', rf'\item \textit{{Notes:}} {notes}',
            r'\end{tablenotes}', r'\end{threeparttable}', r'\end{adjustbox}', r'\end{table}']


def aer_table(path: Path, caption: str, label: str, k: int, panels: list[dict], notes: str,
              header_rows: list[list[tuple[str, int]]] | None = None, numbers: bool = True, fe_rows: list[tuple] | None = None,
              digits: int = 3, stub: str = '', stars_note: bool = True) -> Path:
    """Regression table with panels.
    header_rows: rows of (text, span) covering the k data columns; a \\cmidrule is drawn under every non-empty group that
                 is not in the last header row. numbers: add the (1)...(k) row.
    panels: [{'title': 'Panel A. ...' or None, 'rows': [...]}], each row one of
        ('coef', label, [cell]*k)  cell = (b, se, p) | str | None  (tuples print estimate + bracketed SE line)
        ('stat', label, [str]*k)
        ('space',)
    fe_rows: [(label, [str]*k)] printed after the panels, separated by a rule."""
    lines = _head(caption, label, 'l' + 'c' * k)
    hdr = header_rows or []
    for hi, row in enumerate(hdr):
        cells, cm, col = [], [], 2
        for text, span in row:
            cells.append(rf'\multicolumn{{{span}}}{{c}}{{{text}}}' if span > 1 else text)
            if text and hi < len(hdr) - 1:
                cm.append(rf'\cmidrule(lr){{{col}-{col + span - 1}}}')
            col += span
        lines.append((stub if hi == len(hdr) - 1 and not numbers else '') + ' & ' + ' & '.join(cells) + r' \\')
        if cm:
            lines.append(''.join(cm))
    if numbers:
        lines.append(stub + ' & ' + ' & '.join(f'({i + 1})' for i in range(k)) + r' \\')
    lines.append(r'\midrule')
    for pi, pnl in enumerate(panels):
        if pi:
            lines.append(r'\addlinespace[6pt]')
        if pnl.get('title'):
            lines.append(rf'\multicolumn{{{k + 1}}}{{l}}{{\textit{{{pnl["title"]}}}}} \\')
        prev = None
        for row in pnl['rows']:
            if row[0] == 'space':
                lines.append(r'\addlinespace')
                continue
            kind, lab, cells = row
            if kind == 'stat' and prev == 'coef':
                lines.append(r'\addlinespace')
            if kind == 'coef':
                top, bot = [], []
                for c in cells:
                    if isinstance(c, tuple) and not any(isinstance(v, float) and math.isnan(v) for v in c[:2]):
                        top.append(f'${fmt(c[0], digits)}{stars(c[2])}$')
                        bot.append(f'[{fmt(c[1], digits)}]')
                    else:
                        top.append('' if c is None or isinstance(c, tuple) else str(c))
                        bot.append('')
                lines.append(lab + ' & ' + ' & '.join(top) + r' \\')
                lines.append(' & ' + ' & '.join(bot) + r' \\')
            else:
                lines.append(lab + ' & ' + ' & '.join(str(c) for c in cells) + r' \\')
            prev = kind
    if fe_rows:
        lines.append(r'\midrule')
        for lab, cells in fe_rows:
            lines.append(lab + ' & ' + ' & '.join(cells) + r' \\')
    lines += _tail(notes + (' Standard errors in brackets. ' + STARS_NOTE if stars_note else ''))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def latex_frame(df: pd.DataFrame, path: Path, caption: str, label: str, notes: str, colfmt: str | None = None,
                group_col: str | None = None) -> Path:
    """Descriptive table from a DataFrame (strings already formatted). Optional panel grouping rows (italic titles)."""
    cols = [c for c in df.columns if c != group_col]
    colfmt = colfmt or ('l' + 'c' * (len(cols) - 1))
    lines = _head(caption, label, colfmt) + [' & '.join(cols) + r' \\', r'\midrule']
    if group_col:
        for gi, (g, sub) in enumerate(df.groupby(group_col, sort=False)):
            if gi:
                lines.append(r'\addlinespace[6pt]')
            lines.append(rf'\multicolumn{{{len(cols)}}}{{l}}{{\textit{{{g}}}}} \\')
            for _, r in sub.iterrows():
                lines.append(' & '.join(str(r[c]) for c in cols) + r' \\')
    else:
        for _, r in df.iterrows():
            lines.append(' & '.join(str(r[c]) for c in cols) + r' \\')
    lines += _tail(notes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def tex_escape(s: str) -> str:
    return (str(s).replace('\\', r'\textbackslash{}').replace('&', r'\&').replace('%', r'\%').replace('$', r'\$')
            .replace('#', r'\#').replace('_', r'\_').replace('{', r'\{').replace('}', r'\}'))
