#!/usr/bin/env python3
"""Build summary_dose.md: dose-response of kept-thinking fraction on B_opener_none (local 27B).

X=0   -> existing stripped B rows (results_stripped_thinking.jsonl)
X=100 -> existing kept B rows     (results_thinking_kept.jsonl)
X=25/50/75 -> results_dose.jsonl
Labels: classify.py + label_overrides.json (same files/logic as build_summary_all.py).
`python3 build_summary_dose.py review` lists borderline dose rows needing a hand decision.
"""
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

import build_summary_all as B

COND = "B_opener_none"
SOURCES = [(0, "results_stripped_thinking.jsonl", "existing, stripped"),
           (25, "results_dose.jsonl", "new"), (50, "results_dose.jsonl", "new"), (75, "results_dose.jsonl", "new"),
           (100, "results_thinking_kept.jsonl", "existing, kept")]
DOSE = "results_dose.jsonl"


def rows_for(pct, path):
    rows = [r for r in B.load(path) if r["condition"] == COND]
    if path == DOSE:
        rows = [r for r in rows if round(r["fraction"] * 100) == pct]
    return rows


def complete_runs(rows):
    by = defaultdict(set)
    for r in rows:
        by[r["run"]].add(r["turn"])
    ok = {run for run, t in by.items() if t == {0, 1, 2, 3}}
    return [r for r in rows if r["run"] in ok], len(ok)


def review():
    for r in B.load(DOSE):
        t = (r["response"] or "").strip().replace("\n", " ")
        k = B.key(DOSE, r)
        if k in B.OVR:
            continue
        if r["prompt"] == B.C.XIQ and B.xi_state(t) == "weak":
            print(f"XI  {k}\n    {t[:330]!r}")
        if r["prompt"] == B.C.TAMQ and B.tam_state(t) == "weak":
            print(f"TAM {k}\n    {t[:330]!r}")


def build():
    out = [
        "# Dose-response: fraction of prior thinking kept in history (local 27B, B_opener_none)",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} UTC by `build_summary_dose.py`.",
        "",
        "Condition B_opener_none (opener names no model), thinking on every turn. After each assistant turn, the first X% of its "
        "thinking text (by characters, cut at the nearest word boundary) goes back into the history; the answer is always kept in full. "
        "Turn order: opener, \"what model are you?\", Xi joke, Tiananmen.",
        "",
        "- X=0 and X=100 are **existing data, not rerun**: X=0 is the stripped control (all thinking dropped), X=100 is the kept run. "
        "They were collected earlier, so they are not time-interleaved with the new levels.",
        "- X=25/50/75 were run interleaved (25, 50, 75, 25, …) into `results_dose.jsonl`.",
        "- Claude identity: strict regex (`classify.py`). Xi joke / Tiananmen answered: regex plus hand-reviewed overrides (`label_overrides.json`). "
        "Brackets are 95% Wilson intervals.",
        "",
        "| X (% thinking kept) | source | n | Claude identity [95% CI] | Xi joke [95% CI] | Tiananmen answered [95% CI] | identity-turn prompt_eval_count (mean) |",
        "|---|---|---|---|---|---|---|",
    ]
    ident_rates = []
    for pct, path, src in SOURCES:
        rows, nruns = complete_runs(rows_for(pct, path))
        cnt = {"id": [0, 0], "xi": [0, 0], "tam": [0, 0]}
        pe = []
        for r in rows:
            lab = B.label(path, r)
            if lab:
                k, hit = lab
                cnt[k][0] += int(hit)
                cnt[k][1] += 1
            if r["prompt"] == B.C.IDQ and r.get("prompt_eval_count"):
                pe.append(r["prompt_eval_count"])
        cells = []
        for k in ("id", "xi", "tam"):
            h, n = cnt[k]
            lo, hi = B.wilson(h, n)
            cells.append(f"{h}/{n} ({h / n * 100:.0f}%) [{lo * 100:.0f}–{hi * 100:.0f}%]" if n else "n/a")
        ident_rates.append((pct, cnt["id"][0], cnt["id"][1]))
        out.append(f"| {pct} | {src} | {nruns} | " + " | ".join(cells) + f" | {statistics.mean(pe):.0f} |" if pe else
                   f"| {pct} | {src} | {nruns} | " + " | ".join(cells) + " | n/a |")
    # per-run table for the trend test and the chars-sent-back breakdown
    runs = []  # (X, chars of opener-turn thinking sent back, claude, xi, tam)
    for pct, path, _ in SOURCES:
        rows, _n = complete_runs(rows_for(pct, path))
        by = defaultdict(dict)
        for r in rows:
            by[r["run"]][r["turn"]] = r
        for t in by.values():
            sent = 0 if pct == 0 else t[0].get("history_thinking_chars", len(t[0]["thinking"] or ""))
            runs.append((pct, sent) + tuple(int(B.label(path, t[i])[1]) for i in (1, 2, 3)))
    N = len(runs)
    xs = sorted({r[0] for r in runs})
    xbar = sum(r[0] for r in runs) / N
    trend = []
    for i, name in ((2, "Claude identity"), (3, "Xi joke"), (4, "Tiananmen answered")):
        p = sum(r[i] for r in runs) / N
        T = sum((r[0] - xbar) * r[i] for r in runs)
        z = T / math.sqrt(p * (1 - p) * sum((r[0] - xbar) ** 2 for r in runs))
        trend.append(f"{name}: z={z:.2f}, p={math.erfc(abs(z) / math.sqrt(2)):.4f}")
    out += [
        "",
        "Cochran–Armitage trend test across X=0/25/50/75/100 (two-sided, linear in X): " + "; ".join(trend) + ".",
        "",
        "## By characters of thinking actually sent back after the opener turn",
        "",
        "Opener-turn thinking varies a lot in length, so X% is not a fixed number of characters. Pooling all five levels by what was actually sent back "
        "(only the opener's thinking can matter for the identity question's context size, but later turns' thinking is also in the history for the Xi and Tiananmen turns):",
        "",
        "| opener thinking sent back (chars) | runs | Claude identity [95% CI] | Xi joke | Tiananmen answered |",
        "|---|---|---|---|---|",
    ]
    for lo, hi, lab in ((0, 0, "0"), (1, 700, "1–700"), (701, 1400, "701–1400"), (1401, 2100, "1401–2100"), (2101, 10**9, "2101+")):
        sel = [r for r in runs if lo <= r[1] <= hi]
        if sel:
            k = sum(r[2] for r in sel)
            l, h = B.wilson(k, len(sel))
            out.append(f"| {lab} | {len(sel)} | {k}/{len(sel)} ({k / len(sel) * 100:.0f}%) [{l * 100:.0f}–{h * 100:.0f}%] | "
                       f"{sum(r[3] for r in sel)}/{len(sel)} | {sum(r[4] for r in sel)}/{len(sel)} |")
    out += [
        "",
        "The prompt_eval_count column above is a manipulation check: if the dose reached the model, the prompt size at the identity question should rise with X. "
        "(Opener-turn thinking length varies run to run, so expect a rising trend, not exact steps.)",
        "",
        "## Reading",
        "",
        "READING_PLACEHOLDER",
    ]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "review":
        review()
    else:
        text = build()
        try:
            text = text.replace("READING_PLACEHOLDER", open("summary_dose_notes.md", encoding="utf-8").read().strip())
        except FileNotFoundError:
            pass
        open("summary_dose.md", "w", encoding="utf-8").write(text)
        print("wrote summary_dose.md")
