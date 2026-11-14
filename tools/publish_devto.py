# -*- coding: utf-8 -*-
"""Post an English article (en/*.md) to dev.to. Python stdlib only.

Usage:
  python -I tools/publish_devto.py en/<file>.md --dry-run     # print payload, send nothing
  python -I tools/publish_devto.py en/<file>.md               # create/update as DRAFT on dev.to
  python -I tools/publish_devto.py en/<file>.md --publish     # go live (only after approval)

Front matter: title, description, tags (comma list or [a, b]), canonical_url (optional; defaults to
the GitHub file URL), devto_id (optional; set -> PUT update, else POST create).
API key: env var DEVTO_API_KEY (never printed).
After success, devto_id and devto_url are written back into the front matter.
Exit codes: 0 ok, 1 validation error, 2 API error.
"""
import argparse, json, os, re, subprocess, sys, urllib.request, urllib.error

API = "https://dev.to/api/articles"
REPO_BLOB = "https://github.com/sunaomunakata/ai-engineering-notes/blob/main/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def split_fm(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None, None, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"\'')
    return fm, m.group(1), text[m.end():]


def parse_tags(v):
    v = (v or "").strip().strip("[]")
    return [t.strip().strip('"\'').lower().replace("-", "") for t in v.split(",") if t.strip()][:4]


def write_back(path, raw_fm, body, updates):
    lines = raw_fm.splitlines()
    for k, v in updates.items():
        new = f"{k}: {v}"
        for i, ln in enumerate(lines):
            if ln.split(":", 1)[0].strip() == k:
                lines[i] = new
                break
        else:
            lines.append(new)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\n" + "\n".join(lines) + "\n---\n" + body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--publish", action="store_true", help="go live (default: draft)")
    ap.add_argument("--dry-run", action="store_true", help="print payload, do not send")
    ap.add_argument("--skip-check", action="store_true", help="skip check_post.py (testing only)")
    a = ap.parse_args()

    path = os.path.abspath(a.file)
    if not os.path.isfile(path):
        print(f"ERROR file not found: {a.file}"); return 1
    if not a.skip_check:
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "check_post.py"), path])
        if r.returncode != 0:
            print("ERROR check_post.py failed; aborting"); return 1

    text = open(path, encoding="utf-8").read()
    fm, raw_fm, body = split_fm(text)
    if fm is None:
        print("ERROR no front matter"); return 1
    if not fm.get("title"):
        print("ERROR front matter missing: title"); return 1

    canonical = fm.get("canonical_url")
    if not canonical:
        canonical = REPO_BLOB + "en/" + os.path.basename(path)
    article = {
        "title": fm["title"],
        "body_markdown": body,
        "published": bool(a.publish),
        "tags": parse_tags(fm.get("tags")),
        "canonical_url": canonical,
    }
    if fm.get("description"):
        article["description"] = fm["description"]
    if fm.get("series"):
        article["series"] = fm["series"]
    devto_id = fm.get("devto_id") or None
    method, url = ("PUT", f"{API}/{devto_id}") if devto_id else ("POST", API)

    if a.dry_run:
        shown = dict(article, body_markdown=f"<{len(body)} chars> " + body[:120].replace("\n", " ") + "...")
        print(f"DRY RUN: {method} {url}")
        print(json.dumps({"article": shown}, ensure_ascii=False, indent=2))
        print("api-key: " + ("set" if os.environ.get("DEVTO_API_KEY") else "NOT SET"))
        return 0

    key = os.environ.get("DEVTO_API_KEY")
    if not key:
        print("ERROR env var DEVTO_API_KEY is not set"); return 1
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps({"article": article}).encode("utf-8"),
                                 headers={"api-key": key, "Content-Type": "application/json",
                                          "Accept": "application/vnd.forem.api-v1+json",
                                          "User-Agent": "ai-engineering-notes-publisher"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"ERROR dev.to API {e.code}: {e.read().decode('utf-8', 'replace')[:500]}"); return 2
    except urllib.error.URLError as e:
        print(f"ERROR dev.to API: {e.reason}"); return 2

    write_back(path, raw_fm, body, {"devto_id": data.get("id"), "devto_url": data.get("url")})
    state = "PUBLISHED" if data.get("published") else "DRAFT"
    print(f"OK {state} id={data.get('id')} url={data.get('url')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
