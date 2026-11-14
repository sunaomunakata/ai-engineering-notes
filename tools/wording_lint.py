# -*- coding: utf-8 -*-
"""Find wording that reads as AI-written. Exit code 1 if any hit.
This only catches fixed phrases. Whether a sentence reads naturally is judged by the
ai-wording-check skill (Japanese section / English section), not here.

Usage: python -I tools/wording_lint.py <article.md> [...]
Language: articles/ -> Japanese list, otherwise English list.
Lists are a starting set (2026-11-14). Add to them when the review finds a new pattern.
"""
import re, sys

EN = [  # (pattern, why)
    (r"\bdelve[sd]?\b|\bdelving\b", "AI favourite word"),
    (r"\btapestry\b|\blandscape\b|\brealm\b", "vague metaphor"),
    (r"\bcrucial\b|\bpivotal\b|\bparamount\b", "inflated emphasis"),
    (r"\bleverag(e|es|ed|ing)\b", "jargon; say 'use'"),
    (r"\bseamless(ly)?\b|\brobust\b|\bgame[- ]changer\b", "buzzword"),
    (r"\bIn today's (fast-paced|rapidly)", "stock opener"),
    (r"\bIt'?s not (just )?\w+[^.]{0,40}, it'?s\b", "'not X, it's Y' pattern"),
    (r"\bIn conclusion\b|\bIn summary\b", "stock closer"),
    (r"\bunlock(s|ed|ing)? the (power|potential)\b", "marketing phrase"),
    (r"\bnavigat(e|ing) the complexit", "stock phrase"),
]
JA = [  # 例は ai-wording-check の types.md から
    (r"ゲームチェンジャー", "英語の直訳"),
    (r"レバレッジする|インサイト", "不要なカタカナ"),
    (r"〜?すること、それが", "英語の語順の名残"),
    (r"鍵となる|カギとなる", "直訳調"),
    (r"重要です。|不可欠です。", "強調の決まり文句（中身で言う）"),
    (r"いかがでしたか", "定型の締め"),
]

bad = False
for f in sys.argv[1:]:
    t = open(f, encoding="utf-8").read()
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)       # skip front matter
    t = re.sub(r"```.*?```", "", t, flags=re.S)                 # skip code
    rules = JA if "articles" in f.replace("\\", "/").split("/") else EN
    dashes = t.count("—")
    hits = []
    for i, line in enumerate(t.splitlines(), 1):
        for pat, why in rules:
            for m in re.finditer(pat, line, re.I):
                hits.append(f"  L{i}: '{m.group(0)}' — {why}")
    if rules is EN and dashes > 5:
        hits.append(f"  {dashes} em dashes — too many; use commas or periods")
    print(f"== {f}: {len(hits)} hit(s)"); print("\n".join(hits))
    bad |= bool(hits)
sys.exit(1 if bad else 0)
