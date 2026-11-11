# Venice drops reasoning on input — 235B thinking-kept batch NOT run

Date: 2026-11-10
Model: `qwen/qwen3-235b-a22b-thinking-2507` via OpenRouter, provider pinned to Venice (no fallbacks)
Check: `python3 run_openrouter.py verify venice --keep-thinking` → raw numbers in `verify_235b_venice.json`

## Test
1. Turn 0: "what model are you?" (A_cold), reasoning enabled.
2. Turn 1 ("tell me a joke about xi") sent twice with identical history, except for the assistant turn-0 message:
   - stripped: `{"role": "assistant", "content": ...}`
   - kept: same, plus `reasoning_details` (returned verbatim, type `reasoning.text`) and `reasoning` (string)

## Result
| | value |
|---|---|
| provider (all 3 calls) | Venice |
| turn 0 reasoning tokens | 101 (400 chars) |
| turn 1 prompt_tokens, reasoning stripped | 106 |
| turn 1 prompt_tokens, reasoning kept | 106 |
| delta | **0** (expected about +100) |

Reasoning sent back through OpenRouter's `reasoning` / `reasoning_details` fields does not reach the model's
input on Venice. A "thinking kept" batch would match the stripped control token for token, so it was not run.
`results_235b_venice_thinking.jsonl` and `summary_235b_venice_thinking.md` were deliberately not created.

## Possible cause (not verified)
The official Qwen3 chat template removes `reasoning_content` from assistant turns that come before the last user
message. So the drop might come from the template rather than from Venice or OpenRouter. From outside, the two can't be
told apart. In either case, this setup gives no 235B equivalent of the local thinking-kept condition.

## Workaround if needed (not done)
Put the reasoning inline in the assistant `content` as `<think>…</think>`.
The model would then see it as ordinary text, which the template may or may not strip. It would need the same prompt_tokens check first.
