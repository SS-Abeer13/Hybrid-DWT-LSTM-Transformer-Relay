"""R0: audit the 40 thesis references against Crossref (and, where the PDF is in the project, against the PDF's first page).
Writes documents/reference_audit.json and documents/reference_audit.md. The Crossref answer is kept verbatim next to what the thesis lists;
a human decision (documents/reference_audit.md, column 'decision') is made from it, not from this script.

    python tools/audit_references.py
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "latex_source" / "latex" / "main.tex"
PDFS = ROOT / "documents" / "Reference Papers"
OUT_JSON = ROOT / "documents" / "reference_audit.json"
MAILTO = "arcadian1333@gmail.com"


def clean(s: str) -> str:
    rep = {r"\~{o}": "o", r"\v{c}": "c", r"\'{c}": "c", r"\\ ": " ", "~": " ", "--": "-", "``": "", "''": ""}
    for a, b in rep.items():
        s = s.replace(a, b)
    s = re.sub(r"\\textit\{(.*?)\}", r"\1", s)
    s = re.sub(r"\\[A-Za-z]+\.?\\? ?", " ", s)
    return re.sub(r"\s+", " ", s.replace("{", "").replace("}", "")).strip()


def g(pat: str, text: str) -> str:
    m = re.search(pat, text)
    return m.group(1) if m else ""


def parse() -> list[dict]:
    t = TEX.read_text(encoding="utf-8")
    body = t[t.index(r"\begin{thebibliography}"):t.index(r"\end{thebibliography}")]
    out = []
    for m in re.finditer(r"\\bibitem\{(ref\d+)\}\s*(.*?)(?=\\bibitem|\Z)", body, re.S):
        key, raw = m.group(1), " ".join(m.group(2).split())
        tm = re.search(r"``(.*?),''", raw)
        vm = re.search(r"\\textit\{(.*?)\}", raw)
        authors = raw.split("``")[0] if "``" in raw else raw.split(r"\textit")[0]
        out.append({
            "key": key, "raw": clean(raw), "authors": clean(authors).rstrip(", ."), "title": clean(tm.group(1)) if tm else "",
            "venue": clean(vm.group(1)) if vm else "", "year": (re.findall(r"(19\d\d|20\d\d)", raw) or [""])[-1],
            "vol": g(r"vol\.~?(\d+)", raw), "no": g(r"no\.~?(\d+)", raw),
            "pages": g(r"pp\.~?([\d\-]+)", raw).replace("--", "-"), "art": g(r"(?:art|p)\.~?(\d+)", raw),
        })
    return out


def crossref(q: str, rows: int = 4) -> list[dict]:
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": rows, "mailto": MAILTO,
                                                                    "select": "DOI,title,author,container-title,volume,issue,page,article-number,issued,type"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"reference-audit/1.0 (mailto:{MAILTO})"}), timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))["message"]["items"]
        except Exception:
            time.sleep(2)
    return []


def summarise(it: dict) -> dict:
    au = [f"{a.get('given', '')} {a.get('family', a.get('name', ''))}".strip() for a in it.get("author", [])]
    yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {"doi": it.get("DOI"), "title": (it.get("title") or [""])[0], "authors": au, "venue": (it.get("container-title") or [""])[0],
            "volume": it.get("volume"), "issue": it.get("issue"), "pages": it.get("page"), "article": it.get("article-number"), "year": yr, "type": it.get("type")}


def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def surname_list(authors: str) -> list[str]:
    s = authors.replace(" and ", ", ")
    return [p.strip().split()[-1].lower() for p in s.split(",") if p.strip()]


def pdf_first_page(ref_title: str) -> str | None:
    best, bs = None, 0.0
    for p in PDFS.glob("*.pdf*"):
        s = sim(p.stem, ref_title)
        if s > bs:
            best, bs = p, s
    if best is None or bs < 0.45:
        return None
    try:
        txt = subprocess.run(["pdftotext", "-l", "1", str(best), "-"], capture_output=True, text=True, timeout=60).stdout
        return best.name + " :: " + " ".join(txt.split())[:900]
    except Exception:
        return best.name


def main() -> None:
    refs = parse()
    print(len(refs), "references parsed")
    res = []
    for r in refs:
        q = f"{r['title']} {r['authors'].split(',')[0]}" if r["title"] else r["raw"]
        cands = [summarise(i) for i in crossref(q)]
        scored = []
        for c in cands:
            ts = sim(c["title"], r["title"]) if r["title"] else 0.0
            au_l = set(surname_list(r["authors"])); au_c = {a.split()[-1].lower() for a in c["authors"] if a}
            overlap = len(au_l & au_c) / max(len(au_l), 1)
            scored.append({**c, "title_similarity": round(ts, 3), "listed_author_surnames_found": round(overlap, 2),
                           "year_match": str(c["year"]) == r["year"], "volume_match": (str(c["volume"]) == r["vol"]) if r["vol"] else None,
                           "pages_match": (r["pages"] != "" and r["pages"] == (c["pages"] or "").replace("--", "-")) if r["pages"] else None})
        scored.sort(key=lambda x: -(x["title_similarity"] + 0.5 * x["listed_author_surnames_found"]))
        best = scored[0] if scored else None
        if best and best["title_similarity"] >= 0.9 and best["listed_author_surnames_found"] >= 0.99 and best["year_match"] and best["volume_match"] in (True, None):
            verdict = "MATCH"
        elif best and best["title_similarity"] >= 0.75:
            verdict = "PARTIAL"
        else:
            verdict = "NOT_FOUND"
        res.append({"listed": r, "pdf_first_page": pdf_first_page(r["title"]) if r["title"] else None, "best": best, "others": scored[1:3], "verdict_auto": verdict})
        print(r["key"], verdict, (best or {}).get("doi"), flush=True)
        time.sleep(0.4)
    OUT_JSON.write_text(json.dumps({"date": time.strftime("%Y-%m-%d %H:%M"), "source": "Crossref REST API (query.bibliographic)", "refs": res}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
