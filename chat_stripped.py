#!/usr/bin/env python3
"""Manual chat with local Qwen: thinking ON each turn, but earlier thinking is NOT sent back.
Matches the batch 'stripped' condition. Commands: /clear (back to loaded state), /save FILE, /bye. --load FILE starts from a saved history. Stdlib only."""
import json, sys, urllib.request

args = sys.argv[1:]
LOAD = None
if "--load" in args:
    i = args.index("--load"); LOAD = args[i + 1]; del args[i:i + 2]
MODEL = args[0] if args else "qwen3.8:27b-mlx"
URL = "http://localhost:11434/api/chat"
DIM, RST = "\033[2m", "\033[0m"
history = json.load(open(LOAD)) if LOAD else []
start = list(history)
for m in history:
    print(f"{'>>> ' if m['role'] == 'user' else ''}{m['content'].strip()}\n")

def chat(msgs):
    body = json.dumps({"model": MODEL, "messages": msgs, "think": True, "stream": False}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)

print(f"model: {MODEL} | thinking on, stripped from history | /clear resets, /bye quits")
while True:
    try:
        lines = [input(">>> ")]
    except (EOFError, KeyboardInterrupt):
        break
    # paste multi-line text: end a line with a backslash to keep typing
    while lines[-1].endswith("\\"):
        lines[-1] = lines[-1][:-1]
        lines.append(input("... "))
    text = "\n".join(lines).strip()
    if not text:
        continue
    if text == "/bye":
        break
    if text == "/clear":
        history = list(start)
        print("reset to loaded state" if start else "cleared")
        continue
    if text.startswith("/save "):
        json.dump(history, open(text[6:].strip(), "w"), indent=1)
        print("saved")
        continue
    history.append({"role": "user", "content": text})
    r = chat(history)
    msg = r["message"]
    if msg.get("thinking"):
        print(f"{DIM}{msg['thinking'].strip()}{RST}\n")
    print(msg["content"].strip())
    print(f"{DIM}[prompt tokens {r.get('prompt_eval_count')}, out {r.get('eval_count')}]{RST}\n")
    history.append({"role": "assistant", "content": msg["content"]})  # thinking dropped here
