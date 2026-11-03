"""Crossref lookup helper for the literature audit (verification of DOIs / search by bibliographic query).
Usage: python crossref.py q "query text" [rows]     -> top hits
       python crossref.py doi 10.xxxx/yyyy ...      -> record for each DOI (Y = resolves in Crossref)
Results are appended to audit/scripts/out/crossref_log.jsonl (the audit trail for literature_table.csv)."""
import json, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
LOG = Path(__file__).resolve().parent / "out" / "crossref_log.jsonl"; LOG.parent.mkdir(exist_ok=True)
UA = {"User-Agent": "thesis-audit-script/1.0"}
def get(url, tries=6):
    import time
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(5 * 2 ** i); continue
            raise
def short(m):
    au = "; ".join(f"{a.get('family','')}, {a.get('given','')}" for a in m.get("author", [])[:6])
    yr = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {"doi": m.get("DOI"), "title": (m.get("title") or [""])[0], "authors": au, "year": yr,
            "venue": (m.get("container-title") or [""])[0], "vol": m.get("volume"), "page": m.get("page") or m.get("article-number"), "type": m.get("type")}
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "q":
        rows = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        j = get("https://api.crossref.org/works?rows=%d&query.bibliographic=%s" % (rows, urllib.parse.quote(sys.argv[2])))
        out = [short(m) for m in j["message"]["items"]]
    else:
        out = []
        for d in sys.argv[2:]:
            try:
                out.append(dict(short(get("https://api.crossref.org/works/" + urllib.parse.quote(d))["message"]), verified="Y"))
            except Exception as e:
                out.append({"doi": d, "verified": "N", "error": str(e)})
    with LOG.open("a") as f:
        f.write(json.dumps({"mode": mode, "args": sys.argv[2:], "result": out}) + "\n")
    for o in out:
        print(json.dumps(o, ensure_ascii=False))
