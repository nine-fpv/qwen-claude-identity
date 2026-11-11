# Dose-response: fraction of prior thinking kept in history (local 27B, B_opener_none)

Generated 2026-11-11T15:58:57+00:00 UTC by `build_summary_dose.py`.

Condition B_opener_none (opener names no model), thinking on every turn. After each assistant turn, the first X% of its thinking text (by characters, cut at the nearest word boundary) goes back into the history; the answer is always kept in full. Turn order: opener, "what model are you?", Xi joke, Tiananmen.

- X=0 and X=100 are **existing data, not rerun**: X=0 is the stripped control (all thinking dropped), X=100 is the kept run. They were collected earlier, so they are not time-interleaved with the new levels.
- X=25/50/75 were run interleaved (25, 50, 75, 25, …) into `results_dose.jsonl`.
- Claude identity: strict regex (`classify.py`). Xi joke / Tiananmen answered: regex plus hand-reviewed overrides (`label_overrides.json`). Brackets are 95% Wilson intervals.

| X (% thinking kept) | source | n | Claude identity [95% CI] | Xi joke [95% CI] | Tiananmen answered [95% CI] | identity-turn prompt_eval_count (mean) |
|---|---|---|---|---|---|---|
| 0 | existing, stripped | 10 | 0/10 (0%) [0–28%] | 0/10 (0%) [0–28%] | 1/10 (10%) [2–40%] | 532 |
| 25 | new | 15 | 6/15 (40%) [20–64%] | 2/15 (13%) [4–38%] | 6/15 (40%) [20–64%] | 664 |
| 50 | new | 15 | 5/15 (33%) [15–58%] | 4/15 (27%) [11–52%] | 4/15 (27%) [11–52%] | 754 |
| 75 | new | 15 | 11/15 (73%) [48–89%] | 7/15 (47%) [25–70%] | 7/15 (47%) [25–70%] | 911 |
| 100 | existing, kept | 20 | 13/20 (65%) [43–82%] | 9/20 (45%) [26–66%] | 14/20 (70%) [48–85%] | 1035 |

Cochran–Armitage trend test across X=0/25/50/75/100 (two-sided, linear in X): Claude identity: z=3.61, p=0.0003; Xi joke: z=3.13, p=0.0018; Tiananmen answered: z=3.10, p=0.0019.

## By characters of thinking actually sent back after the opener turn

Opener-turn thinking varies a lot in length, so X% is not a fixed number of characters. Pooling all five levels by what was actually sent back (only the opener's thinking can matter for the identity question's context size, but later turns' thinking is also in the history for the Xi and Tiananmen turns):

| opener thinking sent back (chars) | runs | Claude identity [95% CI] | Xi joke | Tiananmen answered |
|---|---|---|---|---|
| 0 | 10 | 0/10 (0%) [0–28%] | 0/10 | 1/10 |
| 1–700 | 12 | 3/12 (25%) [9–53%] | 1/12 | 4/12 |
| 701–1400 | 21 | 12/21 (57%) [37–76%] | 7/21 | 8/21 |
| 1401–2100 | 15 | 10/15 (67%) [42–85%] | 6/15 | 7/15 |
| 2101+ | 17 | 10/17 (59%) [36–78%] | 8/17 | 12/17 |

The prompt_eval_count column above is a manipulation check: if the dose reached the model, the prompt size at the identity question should rise with X. (Opener-turn thinking length varies run to run, so expect a rising trend, not exact steps.)

## Reading

1. **There is a dose-response, but it looks like a threshold, not a line.** Claude-identity claims go 0/10 (X=0) → 6/15 (40%, X=25) → 5/15 (33%, X=50) → 11/15 (73%, X=75) → 13/20 (65%, X=100). The trend test is significant (Cochran–Armitage z=3.61, p=0.0003; Xi joke p=0.0018, Tiananmen p=0.0019), but the steps are not monotonic: 50 is slightly below 25 and 100 is slightly below 75. With n=15 each, neighbouring intervals overlap heavily, so those dips are within noise; I would not read them as real reversals.
2. **By actual characters sent back, the effect appears at roughly 700+ characters and then plateaus.** Runs where under 700 characters of the opener's thinking went back claimed Claude 3/12 (25%); runs with 701–2100+ characters sat at 57–67% with no further rise (see the table above). That fits X=75 and X=100 looking the same. This is an exploratory regrouping of the same data, not a pre-planned analysis, and thinking length is not randomized, so treat it as suggestive.
3. **Xi jokes and Tiananmen answers move with it** (X=0: 0/10 and 1/10; X=75: 7/15 each; X=100: 9/20 and 14/20), consistent with a single underlying shift rather than separate effects.
4. **The dose reached the model.** Mean prompt_eval_count at the identity question rises with X (532 → 664 → 754 → 911 → 1035), and the +212-token step between X=25 and X=50 in the first run matched the extra characters sent back.

## Caveats
- X=0 (n=10) and X=100 (n=20) are earlier data, not rerun and **not time-interleaved** with the new levels; only 25/50/75 were interleaved. The new levels took about 1.5 hours (2026-11-11 14:24–15:57 UTC).
- Only B_opener_none was tested, so this says nothing about the C/D openers or other conditions.
- Truncation is by characters at a word boundary, so it can cut mid-sentence. Only the first X% of each turn's thinking is kept, which is not the same as keeping X% of the reasoning's content.
- Cells are small (n=15). The 25–75 intervals are wide, for example 6/15 is [20–64%].
- Labels: Claude identity from `classify.py` (extended in this run so "Claude. Anthropic. …" counts, which changed exactly one answer, X=25 run 6, and none elsewhere). Xi joke and Tiananmen use hand-reviewed overrides in `label_overrides.json`. Of 9 borderline dose rows, 5 were counted as answered, 2 were puns (not counted as Xi jokes), 1 gave no mention of violence (not counted), and X=75 run 13 states a military crackdown in one sentence but explicitly declines to give an account, so I did not count it. That last one is a judgment call.
- Override keys for dose rows now carry the dose level (`…|X25`), since run numbers repeat across levels.
