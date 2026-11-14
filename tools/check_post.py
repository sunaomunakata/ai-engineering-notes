# -*- coding: utf-8 -*-
"""Check an article before publishing. Exit code 1 if any ERROR.

Usage: python -I tools/check_post.py <article.md> [...]
- en/*.md       : front matter needs title, description, tags, canonical_url (canonical may be empty until the GitHub URL exists -> WARN)
- articles/*.md : Zenn front matter needs title, emoji, type, topics, published
- both          : a sources section ("## Sources" / "## 出典"), a hiring line (marker <!-- hiring -->),
                  local links/images that exist, no leftover DRAFT/TODO/要確認 markers
TODO (after post #1): verify cited timestamps [h:mm:ss] against the knowledge-base raw transcripts.
"""
import os, re, sys

def front_matter(t):
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m: return None, t
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1); fm[k.strip()] = v.strip()
    return fm, t[m.end():]

def check(path):
    errs, warns = [], []
    t = open(path, encoding="utf-8").read()
    norm = path.replace("\\", "/")
    lang = "ja" if "/articles/" in norm else "en"
    fm, body = front_matter(t)
    need = ["title", "emoji", "type", "topics", "published"] if lang == "ja" else ["title", "description", "tags", "canonical_url"]
    if fm is None: errs.append("no front matter")
    else:
        for k in need:
            if k not in fm: errs.append(f"front matter missing: {k}")
            elif not fm[k].strip('"\''):
                (warns if k == "canonical_url" else errs).append(f"front matter empty: {k}")
        if lang == "ja" and fm.get("type") not in ("tech", "idea", None): errs.append("Zenn type must be tech or idea")
    if not re.search(r"^##\s*(Sources|出典)", body, re.M | re.I): errs.append("no sources section (## Sources / ## 出典)")
    if "<!-- hiring -->" not in body: errs.append("no hiring line (add the marker <!-- hiring --> before it)")
    for m in re.finditer(r"\b(DRAFT|TODO|TBD)\b|要確認|未定", body): errs.append(f"leftover marker: {m.group(0)}")
    for link in re.findall(r"\]\(([^)\s]+)\)", body):
        if re.match(r"^(https?:|mailto:|#)", link): continue
        p = os.path.normpath(os.path.join(os.path.dirname(path), link.split("#")[0]))
        if not os.path.exists(p): errs.append(f"broken local link: {link}")
    return errs, warns

bad = False
for f in sys.argv[1:]:
    e, w = check(f)
    print(f"== {f}: {len(e)} error(s), {len(w)} warning(s)")
    for x in e: print("  ERROR", x)
    for x in w: print("  WARN ", x)
    bad |= bool(e)
sys.exit(1 if bad else 0)
