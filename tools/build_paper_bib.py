"""Builds paper_epsr/refs.bib (paper-v1) from the VERIFIED rows of audit/literature_table.csv.

Each DOI row: BibTeX fetched from Crossref (api.crossref.org/works/<doi>/transform/application/x-bibtex), key renamed.
Rows without a DOI (JMLR, IEC, arXiv): an entry built only from the CSV fields. Rows marked N (unverified): written with a TODO comment.
EXTRA: three references outside the CSV, each resolved on Crossref when this script runs (failure = not written, TODO left).
Nothing is typed from memory. Raw Crossref responses: paper_epsr/generated/crossref_bib_log.json.
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "audit" / "literature_table.csv"
OUT = ROOT / "paper_epsr" / "refs.bib"
LOG = ROOT / "paper_epsr" / "generated" / "crossref_bib_log.json"

KEYS = {  # DOI (lower case) -> citation key
    "10.1109/pct.2007.4538488": "rebizant2007", "10.1109/tpwrd.2022.3230468": "lin2023", "10.1049/gtd2.70379": "rezaei2026",
    "10.1109/icepes.2016.7915908": "bhatt2016", "10.1016/j.ijepes.2014.05.056": "bejmert2014", "10.1016/j.epsr.2021.107297": "simoes2021",
    "10.3390/en15113905": "abdusalam2022", "10.1109/tii.2019.2929744": "afrasiabi2020", "10.1109/access.2025.3618747": "key2025",
    "10.3390/a17090397": "alhamd2024", "10.1109/tie.2021.3109535": "afrasiabi2022", "10.1109/tpwrd.2021.3080927": "murugan2022",
    "10.1016/j.epsr.2023.109255": "afsharisefat2023", "10.1049/gtd2.13112": "afsharisefat2024", "10.1016/j.eswa.2025.128632": "wang2025",
    "10.1049/iet-gtd.2020.0542": "li2020", "10.3390/pr14030449": "shi2026", "10.1109/tpwrd.2009.2028800": "tripathy2010",
    "10.1109/tpwrd.2015.2513778": "medeiros2016", "10.1109/tpwrd.2018.2852485": "medeiros2018", "10.1111/ecog.02881": "roberts2017",
    "10.1016/j.patter.2023.100804": "kapoor2023", "10.36001/phme.2024.v8i1.4125": "matania2024", "10.1162/089976698300017197": "dietterich1998",
    "10.1007/bf02295996": "mcnemar1947", "10.1080/01621459.1927.10502953": "wilson1927", "10.1109/smartgridcomm.2019.8909810": "khaw2019",
    "10.1109/tpwrd.2020.3035885": "sahoo2021", "10.1109/tpwrd.2019.2893279": "farzin2019", "10.1016/j.ijepes.2020.106158": "farzin2020",
    "10.1049/icp.2025.0483": "mieske2025", "10.1109/ieeestd.2008.4483716": "ieeec37110", "10.1049/ip-smt:19951953": "bronzeado1995",
    "10.1016/j.epsr.2015.12.011": "rudez2016", "10.1109/ieeestd.2021.9471045": "ieeec3791", "10.1109/access.2025.3609541": "chothani2025",
}
URL_ROWS = {"https://arxiv.org/abs/2609.28149": "oelhaf2026", "https://jmlr.org/papers/v7/demsar06a.html": "demsar2006",
            "https://webstore.iec.ch/en/publication/32570": "iec60255187"}
UNVERIFIED = {"https://www.jstor.org/stable/4615733": "holm1979", "documents/Reference Papers (git f92ea33), not in Crossref": "ngaopitakkul2006"}
SKIP = {"https://arxiv.org/abs/2604.01928"}   # same paper as lin2023 (TPWRD): cite the journal version
EXTRA = {"10.1162/neco.1997.9.8.1735": "hochreiter1997", "10.1109/34.192463": "mallat1989", "10.1109/tpwrd.2015.2411736": "hajipour2015"}


def get(url: str) -> str:
    for k in range(6):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": "reference-check-script/1.0"})
            return urllib.request.urlopen(r, timeout=30).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(3 * 2 ** k); continue
            raise
    raise RuntimeError("rate limited")


MONTHS = {"jan": "jan", "feb": "feb", "mar": "mar", "apr": "apr", "may": "may", "jun": "jun", "jul": "jul", "aug": "aug", "sep": "sep", "oct": "oct", "nov": "nov", "dec": "dec"}


def fix_month(b: str) -> str:
    """Crossref writes month=July / Sept; BibTeX month macros are jan ... dec."""
    return re.sub(r"month=([A-Za-z]+)", lambda m: f"month={MONTHS[m.group(1)[:3].lower()]}", b)


def standard_bib(doi: str, key: str, designation: str, year: str) -> str:
    """IEEE standards: Crossref's BibTeX has no title or year; title from the Crossref JSON record, designation and edition year
    from audit/literature_table.csv (the record has no issue date)."""
    m = json.loads(get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"))["message"]
    assert m["type"] == "standard", doi
    return (f"@misc{{{key}, title={{{m['title'][0]}}}, howpublished={{IEEE Std {designation}}}, organization={{IEEE}}, "
            f"year={{{year}}}, DOI={{{m['DOI']}}}, url={{http://dx.doi.org/{m['DOI']}}} }}")


def crossref_bib(doi: str, key: str) -> str:
    b = get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}/transform/application/x-bibtex").strip()
    b = fix_month(b)
    b = re.sub(r"^@(\w+)\{[^,]*,", lambda m: f"@{m.group(1)}{{{key},", b, count=1)
    b = b.replace("–", "--").replace("—", "---").replace("‐", "-").replace("’", "'").replace("‘", "`").replace("&amp;", r"\&").replace(" & ", r" \& ")
    b = b.replace("õ", r"{\~o}").replace("é", r"{\'e}").replace("ć", r"{\'c}").replace("č", r"{\v{c}}").replace("ö", r'{\"o}').replace("ü", r'{\"u}')
    return b


def authors(a: str) -> str:
    """'Oelhaf J., Kordowich G.' -> 'Oelhaf, J. and Kordowich, G.'"""
    out = []
    for x in [x.strip() for x in a.split(",") if x.strip()]:
        m = re.match(r"(.+?)\s+((?:[A-Z]\.\s*)+)$", x)
        out.append(f"{m.group(1)}, {m.group(2).strip()}" if m else x)
    return " and ".join(out)


def structured(key: str, r: dict, u: str) -> str:
    """BibTeX for the CSV rows without a DOI: fields parsed from the CSV citation string (plus the project PDF's pages for Ngaopitakkul)."""
    c = r["citation"]
    if key == "oelhaf2026":
        m = re.match(r"(.+?): (.+), arXiv:(\d{4}\.\d{4,5})$", c)
        return (f"@misc{{{key}, author={{{authors(m.group(1))}}}, title={{{m.group(2)}}}, howpublished={{arXiv preprint arXiv:{m.group(3)} [eess.SY]}}, "
                f"eprint={{{m.group(3)}}}, archivePrefix={{arXiv}}, year={{{r['year']}}}, note={{Preprint}}, url={{{u}}} }}")
    if key == "demsar2006":
        m = re.match(r"(.+?): (.+), J\. Mach\. Learn\. Res\. (\d+):(\d+)-(\d+), (\d{4})$", c)
        return (f"@article{{{key}, author={{{authors(m.group(1))}}}, title={{{m.group(2)}}}, journal={{Journal of Machine Learning Research}}, "
                f"volume={{{m.group(3)}}}, pages={{{m.group(4)}--{m.group(5)}}}, year={{{m.group(6)}}}, url={{{u}}} }}")
    if key == "iec60255187":
        m = re.match(r"(IEC [\d-]+:\d{4}) (.+)$", c)
        return f"@misc{{{key}, title={{{m.group(2)}}}, howpublished={{{m.group(1)}}}, organization={{IEC}}, year={{{r['year']}}}, url={{{u}}} }}"
    if key == "holm1979":
        m = re.match(r"(.+?): (.+), Scand\. J\. Statist\. (\d+)\((\d+)\):(\d+)-(\d+), (\d{4})$", c)
        return (f"@article{{{key}, author={{{authors(m.group(1))}}}, title={{{m.group(2)}}}, journal={{Scandinavian Journal of Statistics}}, "
                f"volume={{{m.group(3)}}}, number={{{m.group(4)}}}, pages={{{m.group(5)}--{m.group(6)}}}, year={{{m.group(7)}}}, note={{{{JSTOR}} 4615733}} }}")
    if key == "ngaopitakkul2006":
        # title, volume, issue and pages from the project PDF as recorded in documents/baselines/ngaopitakkul2006_dwt_bpnn_spec.md; no DOI exists
        spec = (ROOT / "documents" / "baselines" / "ngaopitakkul2006_dwt_bpnn_spec.md").read_text(encoding="utf-8")
        m = re.search(r'Paper: (.+?), "(.+?),"\s*\*(.+?)\*\s*(\d+)\((\d+)\), (\d+)-(\d+), \w+ (\d{4})', spec)
        auth = " and ".join(x.strip() for x in m.group(1).split(" and "))
        return (f"@article{{{key}, author={{{auth}}}, title={{{m.group(2)}}}, journal={{{m.group(3)}}}, volume={{{m.group(4)}}}, number={{{m.group(5)}}}, "
                f"pages={{{m.group(6)}--{m.group(7)}}}, year={{{m.group(8)}}} }}")
    raise KeyError(key)


def protect_title(entry: str) -> str:
    """elsarticle-num sentence-cases titles: brace every token with two or more capitals (IEEE, CT, LSTM, EvEMTBench) so it keeps its case."""
    def fix(m):
        t = re.sub(r"(?<![{\\\w])([A-Za-z]*[A-Z][a-z]*[A-Z][A-Za-z0-9-]*)", r"{\1}", m.group(2))
        return m.group(1) + t + "}"
    return re.sub(r"(title=\{)((?:[^{}]|\{[^{}]*\})*)\}", fix, entry) if entry.startswith("@") else entry


def main() -> None:
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    out, log, todo = ["% generated by tools/build_paper_bib.py from audit/literature_table.csv (verified rows) - do not edit by hand"], {}, []
    for r in rows:
        u = r["DOI/URL"].strip()
        doi = u.lower().replace("https://doi.org/", "") if u.lower().startswith("https://doi.org/") else None
        if u in SKIP:
            continue
        if doi and doi in KEYS:
            assert r["verified (Y/N)"] == "Y", u
            std = re.search(r"IEEE (C[\d.]+)-(\d{4})", r["method"]) if doi.startswith("10.1109/ieeestd") else None
            if std:
                b = standard_bib(doi, KEYS[doi], f"{std.group(1)}-{std.group(2)}", std.group(2))
                note = "% verified: audit/literature_table.csv (Crossref standard record: title; designation and edition year from the CSV)"
            else:
                b = crossref_bib(doi, KEYS[doi]); note = "% verified: audit/literature_table.csv (Crossref)"
            log[doi] = b; out += [note, b, ""]
        elif u in URL_ROWS:
            assert r["verified (Y/N)"] == "Y", u
            out += [f"% verified: audit/literature_table.csv (URL {u}); fields parsed from the CSV row", structured(URL_ROWS[u], r, u), ""]
        elif u in UNVERIFIED:
            assert r["verified (Y/N)"] == "N", u
            todo.append(UNVERIFIED[u])
            out += [f"% TODO UNVERIFIED (audit/literature_table.csv: verified = N; source: {u}); check before submission.", structured(UNVERIFIED[u], r, u), ""]
    for doi, key in EXTRA.items():
        try:
            b = crossref_bib(doi, key); log[doi] = b
            out += [f"% EXTRA (not in audit/literature_table.csv): resolved on Crossref by this script, DOI {doi}", b, ""]
        except Exception as e:  # noqa: BLE001
            todo.append(key); out += [f"% TODO {key}: DOI {doi} did not resolve ({e}); not written", ""]
    out = [protect_title(x) for x in out]
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    LOG.write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {sum(1 for l in out if l.startswith('@'))} entries; TODO: {todo}")


if __name__ == "__main__":
    main()
