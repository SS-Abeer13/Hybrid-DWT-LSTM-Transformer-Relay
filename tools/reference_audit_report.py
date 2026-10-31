"""R0 step 2: decisions on the 40 thesis references (made by reading documents/reference_audit.json + the PDFs of the papers), the verified records
fetched from Crossref by DOI, documents/reference_audit.md, and the corrected \\bibitem lines applied to latex_source/latex/main.tex.

    python tools/reference_audit_report.py [--apply]
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUD = json.loads((ROOT / "documents" / "reference_audit.json").read_text(encoding="utf-8"))
TEX = ROOT / "latex_source" / "latex" / "main.tex"
MAILTO = "arcadian1333@gmail.com"

# key: (decision, DOI or None, note). Decisions: VERIFIED (listed data correct), CORRECTED (same paper, listed data wrong in at least one field),
# UNVERIFIED (no record found by title/author/year in Crossref and not among the project PDFs: to be removed or replaced by the author).
D = {
    "ref1": ("VERIFIED", "10.3390/a17090397", ""),
    "ref2": ("UNVERIFIED", None, "Crossref queries by title and by authors return no such paper (best hit: another Algorithms paper by the same group = ref1). Possibly a different title/venue."),
    "ref3": ("CORRECTED", "10.52783/jes.3163", "Title and pages match; Crossref lists ONE author (W. A. Atiyah) and issue 4s. A second Atiyah paper is the one in the project folder: J. Electr. Eng. Technol. 19(8), 2024, DOI 10.1007/s42835-024-02048-7 (WT + LSTM) - the benchmark's 'Standalone LSTM' row cites that one."),
    "ref4": ("VERIFIED", "10.1002/9781119513100", "Book. The listed entry is the 1999 first edition (P. M. Anderson, IEEE Press / McGraw-Hill). The PDF in the project is the Wiley/IEEE Press edition (DOI above, five authors, 2nd edition): cite the edition that was actually used."),
    "ref5": ("UNVERIFIED", None, "No such paper found. Project PDF 'Sundararaman & Jain, Eng. Proc. 59, 71 (2023), DOI 10.3390/engproc2023059071' is a possible intended source; not substituted automatically."),
    "ref6": ("CORRECTED", "10.1016/j.epsr.2014.04.008", "Title, volume, pages and an author initial were wrong."),
    "ref7": ("CORRECTED", "10.1109/aieepas.1958.4500059", "Title and pages were wrong."),
    "ref8": ("CORRECTED", "10.1109/ciced.2016.7576109", "Authors and venue were wrong (conference paper)."),
    "ref9": ("VERIFIED", "10.1109/tpwrd.2009.2028800", ""),
    "ref10": ("UNVERIFIED", None, "No such paper found. Candidate: Raichura, Chothani, Patel, IET Energy Syst. Integr. 3(2), 2021, DOI 10.1049/esi2.12012 (review of inrush/fault detection methods); not substituted automatically."),
    "ref11": ("CORRECTED", "10.3390/en15113905", "Authors (O. Abdusalam, A. Ibrahim, F. Anayi, M. Packianather), title, issue and article number were wrong. Classifiers in the paper: KNN, SVM, ANN - no random forest."),
    "ref12": ("CORRECTED", "10.1016/j.eswa.2025.128632", "Authors, title, volume, article number and year were wrong; the Crossref record is the closest match (reinforcement-learning early classification for transformer differential protection)."),
    "ref13": ("VERIFIED", "10.1016/j.epsr.2021.107297", "Article number 107297 (not 107297 vs 'art.' difference); authors as listed."),
    "ref14": ("CORRECTED", "10.15676/ijeei.2021.13.1.1", "Authors (M. Y. Suliman, M. T. Al-Khayyat), venue (Int. J. Electr. Eng. Informatics 13(1), Mar. 2021) wrong; confirmed on the PDF."),
    "ref15": ("CORRECTED", "10.1109/pct.2007.4538488", "Authors (Rebizant, Bejmert, Schiel) and venue (2007 IEEE Lausanne PowerTech, pp. 1209-1214) wrong; confirmed on the PDF."),
    "ref16": ("VERIFIED", "10.1109/tii.2019.2929744", ""),
    "ref17": ("CORRECTED", "10.15598/aeee.v18i3.3833", "Authors (M. Raichura, N. Chothani, D. Patel), journal (Adv. Electr. Electron. Eng.), title and pages wrong."),
    "ref18": ("UNVERIFIED", None, "No such paper found in Crossref (queries by title and authors)."),
    "ref19": ("CORRECTED", None, "Not in Crossref. PDF in the project: A. Ngaopitakkul and A. Kunakorn, 'Internal fault classification in transformer windings using combination of discrete wavelet transforms and back-propagation neural networks,' Int. J. Control, Autom. Syst. 4(3), 365-371, June 2006 (title/venue/pages read from the PDF first page)."),
    "ref20": ("CORRECTED", "10.5539/mas.v4n5p67", "Authors (S. Subramanian, B. Mathur, J. Henry), venue (Modern Applied Science 4(5), 2010) and title wording wrong."),
    "ref21": ("CORRECTED", "10.1109/tpwrd.2013.2280023", "Title, issue and pages wrong (29(2), pp. 777-785); confirmed on the PDF."),
    "ref22": ("CORRECTED", "10.1002/cta.3476", "Authors (N. Shahbazi, S. Bagheri, G. B. Gharehpetian), venue (Int. J. Circuit Theory Appl. 51(3)) and title wrong."),
    "ref23": ("CORRECTED", "10.1109/access.2025.3618747", "Authors (S. Key, S. Leap, S.-M. Yoon, H. Lee, S.-R. Nam) and pages (178492-178504) wrong."),
    "ref24": ("CORRECTED", "10.1016/j.jestch.2025.102144", "Title wording ('Transformer differential protection with wavelet transform and difference function') and first author spelling."),
    "ref25": ("CORRECTED", "10.3390/app112210619", "Authors (9 authors incl. P. Chiradeja, C. Pothisarn) and title wrong; confirmed on the PDF."),
    "ref26": ("CORRECTED", "10.1016/j.epsr.2014.01.001", "First author B. Noshad; venue (Electr. Power Syst. Res. 110, 9-24, 2014) and title wrong."),
    "ref27": ("CORRECTED", "10.1109/tdc.2005.1547155", "Conference paper (2005 IEEE/PES T&D Asia Pacific) by Y. Yuan, Y. Lu, Y. Xu, not an IEEE Trans. Power Del. paper."),
    "ref28": ("VERIFIED", "10.1109/tpwrd.2008.916758", ""),
    "ref29": ("VERIFIED", "10.3390/en15217995", ""),
    "ref30": ("CORRECTED", "10.1109/tpwrd.2016.2575981", "Title, volume/issue and pages wrong (32(1), pp. 209-218); a conference version exists (PESGM 2017)."),
    "ref31": ("UNVERIFIED", None, "No such paper found in Crossref."),
    "ref32": ("UNVERIFIED", None, "No such paper found in Crossref (a 1999 conference paper by the same authors has a different title)."),
    "ref33": ("UNVERIFIED", None, "No such paper found in Crossref."),
    "ref34": ("UNVERIFIED", None, "No such paper found in Crossref (a 2009 PowerTech paper by Oliveira and Bretas on DWT-based transformer differential protection exists, DOI 10.1109/ptc.2009.5282195; different title)."),
    "ref35": ("UNVERIFIED", None, "No such paper found in Crossref."),
    "ref36": ("CORRECTED", "10.1109/ptc.2003.1304742", "Conference paper (2003 IEEE Bologna PowerTech), authors Y.-C. Kang, S.-H. Kang, P. A. Crossley; title uses 'third-difference'."),
    "ref37": ("VERIFIED", "10.1109/tpwrd.2002.803730", ""),
    "ref38": ("VERIFIED", "10.1109/tpwrd.2015.2513778", ""),
    "ref39": ("VERIFIED", "10.1109/tpwrd.2021.3059732", "Crossref lists 'Jose de Jesus Chavez Muro'."),
    "ref40": ("CORRECTED", "10.1109/drpt.2011.5994027", "Authors (Y. Wang, Y. Lu, C. Cai), venue (DRPT 2011) and title wrong; confirmed by the PDF file name in the project."),
}
SEL = "DOI,title,author,container-title,volume,issue,page,article-number,issued,type,publisher"


def fetch(doi: str) -> dict:
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + doi, headers={"User-Agent": f"reference-audit/1.0 (mailto:{MAILTO})"}), timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))["message"]
        except Exception:
            time.sleep(2)
    raise RuntimeError("Crossref fetch failed for " + doi)


def ascii_fold(s: str) -> str:
    s = html.unescape(s).replace("\u2010", "-").replace("\u2011", "-").replace("\u2013", "--").replace("\u2019", "'")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def initials(given: str) -> str:
    return " ".join((p[0] + "." if "-" not in p else "-".join(q[0] + "." for q in p.split("-"))) for p in ascii_fold(given).replace(".", " ").split() if p)


def bib(key: str, it: dict) -> str:
    au = []
    for a in it.get("author", []):
        g, f = a.get("given", ""), a.get("family", "")
        if not f and a.get("name"):
            g, f = a["name"].rsplit(" ", 1) if " " in a["name"] else ("", a["name"])
        au.append(f"{initials(g)} {ascii_fold(f)}".strip())
    authors = au[0] if len(au) == 1 else (", ".join(au[:-1]) + (", and " if len(au) > 2 else " and ") + au[-1])
    yr = (it.get("issued", {}).get("date-parts") or [[""]])[0][0]
    venue = ascii_fold((it.get("container-title") or [""])[0])
    title = ascii_fold((it.get("title") or [""])[0]).replace("&", r"\&")
    parts = [rf"\textit{{{venue.replace('&', chr(92) + '&')}}}"]
    if it.get("volume"):
        parts.append(f"vol.~{it['volume']}")
    if it.get("issue"):
        parts.append(f"no.~{it['issue']}")
    if it.get("page"):
        parts.append("pp.~" + it["page"].replace("-", "--"))
    elif it.get("article-number"):
        parts.append(f"art.~{it['article-number']}")
    parts.append(str(yr))
    return rf"\bibitem{{{key}}} {authors}, ``{title},'' " + ", ".join(parts) + f". doi:{it['DOI']}."


def main() -> None:
    apply = "--apply" in sys.argv
    rec, lines, newbib = {}, [], {}
    tex = TEX.read_text(encoding="utf-8")
    for r in AUD["refs"]:
        k = r["listed"]["key"]
        dec, doi, note = D[k]
        item = fetch(doi) if doi else None
        rec[k] = {"decision": dec, "doi": doi, "note": note, "crossref": item}
        listed = r["listed"]
        if item:
            au = "; ".join(f"{a.get('given', '')} {a.get('family', a.get('name', ''))}".strip() for a in item.get("author", []))
            yr = (item.get("issued", {}).get("date-parts") or [[""]])[0][0]
            ver = f"{au}. {(item.get('title') or [''])[0]}. {(item.get('container-title') or [''])[0]}, vol. {item.get('volume', '-')}, no. {item.get('issue', '-')}, pp. {item.get('page') or item.get('article-number', '-')}, {yr}. DOI {doi}"
        else:
            ver = "(no Crossref record)"
        lines.append(f"| {k} | {dec} | {listed['authors'][:60]}: {listed['title'][:70]} ({listed['year']}) | {ver.replace('|', '/')} | {note.replace('|', '/')} |")
        if dec in ("CORRECTED", "VERIFIED") and item and k not in ("ref13", "ref4"):
            newbib[k] = bib(k, item)
    n = {d: sum(1 for v in D.values() if v[0] == d) for d in ("VERIFIED", "CORRECTED", "UNVERIFIED")}
    md = ["# Reference audit (R0, BENCHMARK_FAIRNESS_PLAN.md)", "",
          f"Date: {time.strftime('%Y-%m-%d')}. Source: Crossref REST API (title + author queries, then fetch by DOI), first pages of the PDFs in git commit `f92ea33` (`documents/Reference Papers/`) for ref14, ref15, ref19, ref21, ref25 and the Wiley front matter of ref4. Raw search results: `documents/reference_audit.json`; decisions and fetched records: `documents/reference_audit_decisions.json`; script: `tools/reference_audit_report.py`.", "",
          f"Result for the 40 entries of the thesis bibliography (`latex_source/latex/main.tex`): **{n['VERIFIED']} verified as listed, {n['CORRECTED']} refer to a real paper but at least one listed field was wrong (corrected), {n['UNVERIFIED']} could not be found.**", "",
          "UNVERIFIED entries are not deleted by this script, because they are cited in the text (see the list at the end): the author must replace or drop the citing sentences. They must not go into a submitted paper in their current form.", "",
          "| key | decision | listed | verified record (Crossref) | note |", "|---|---|---|---|---|"] + lines
    cited = []
    for k, v in D.items():
        if v[0] == "UNVERIFIED":
            for m in re.finditer(r"[^\n]*\\cite\{[^}]*\b" + k + r"\b[^}]*\}[^\n]*", tex):
                cited.append(f"- {k}: `{m.group(0)[:200].strip()}`")
    md += ["", "## Unverified entries and where the thesis cites them", ""] + cited
    (ROOT / "documents" / "reference_audit.md").write_text("\n".join(md), encoding="utf-8")
    (ROOT / "documents" / "reference_audit_decisions.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(n)
    if apply:
        out = tex
        for k, new in newbib.items():
            out, c = re.subn(r"\\bibitem\{" + k + r"\}[^\n]*", lambda m: new, out, count=1)
            assert c == 1, k
        # book and ref19 (not in Crossref): hand-written from the PDF
        out = re.sub(r"\\bibitem\{ref19\}[^\n]*", lambda m: r"\bibitem{ref19} A. Ngaopitakkul and A. Kunakorn, ``Internal fault classification in transformer windings using combination of discrete wavelet transforms and back-propagation neural networks,'' \textit{International Journal of Control, Automation, and Systems}, vol.~4, no.~3, pp.~365--371, June 2006.", out, count=1)
        for k, v in D.items():
            if v[0] == "UNVERIFIED":
                out = re.sub(r"(\\bibitem\{" + k + r"\}[^\n]*)", lambda m: "% R0 2026-10-31: UNVERIFIED (see documents/reference_audit.md)\n" + m.group(1), out, count=1)
        TEX.write_text(out, encoding="utf-8")
        print("main.tex bibliography updated:", len(newbib) + 1, "entries rewritten,", n["UNVERIFIED"], "flagged")


if __name__ == "__main__":
    main()
