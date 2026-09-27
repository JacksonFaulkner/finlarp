"""Resumable bulk downloader for the big once-in-a-while datasets
(see research/BULK_SOURCES.md). Nothing is parsed here — files land raw in
~/.local/share/nvim/security_spread/bulk/<group>/ for loaders to read.

USPTO ODP files need USPTO_API_KEY (env or repo-root .env): the API answers
with a 302 to a signed data.uspto.gov URL that supports Range, so an
interrupted file resumes from its .part. A file is done when its size
matches what the source reports; reruns skip finished files.

    python services/bulk_pull.py            # every group
    python services/bulk_pull.py pv sec     # just these groups
"""
from __future__ import annotations

import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.edgar import UA
from services.universe import data_dir

ODP = "https://api.uspto.gov/api/v1/datasets/products"
ENV = Path(__file__).resolve().parents[4] / ".env"
CHUNK = 1 << 20

# group -> (ODP product, filename regex). Only the tables loaders use.
ODP_GROUPS = {
    "pv": ("PVGPATDIS", r"^g_(patent|application|assignee_disambiguated|cpc_current|wipo_technology"
                        r"|inventor_disambiguated|patent_abstract|cpc_title|assignee_not_disambiguated)\.tsv\.zip$"),
    "pvpg": ("PVPGPUBDIS", r"^pg_(published_application|assignee_disambiguated|cpc_current|wipo_technology"
                           r"|inventor_disambiguated|published_application_abstract|granted_pgpubs_crosswalk)\.tsv\.zip$"),
    "aipd": ("ECOPATAI", r"^2023_r1/ai_model_predictions\.csv\.zip$"),
    "assign": ("PASYR", r"^ad\d+-\d+-\d+\.zip$"),
}
SEC_FILES = {
    "companyfacts.zip": "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip",
    "submissions.zip": "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip",
}
LCA_PAGE = "https://www.dol.gov/agencies/eta/foreign-labor/performance"


def api_key() -> str:
    if k := os.environ.get("USPTO_API_KEY"):
        return k
    for line in ENV.read_text().splitlines():
        if line.startswith("USPTO_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("USPTO_API_KEY missing (env or .env)")


def odp_files(product: str, pattern: str, key: str) -> list[tuple[str, str, int]]:
    """(relative name, download URL, size) for the product's files matching pattern."""
    r = requests.get(f"{ODP}/{product}", params={"includeFiles": "true"},
                     headers={"X-API-Key": key}, timeout=60)
    r.raise_for_status()
    body = r.json()
    bag = (body.get("bulkDataProductBag") or [body])[0]
    out = []
    for f in bag["productFileBag"]["fileDataBag"]:
        uri = f["fileDownloadURI"]
        rel = uri.split(f"/files/{product}/", 1)[1]
        if re.match(pattern, rel):
            out.append((rel, uri, int(f.get("fileSize") or 0)))
    return out


def lca_files() -> list[tuple[str, str, int]]:
    """Latest quarter's H-1B LCA disclosure xlsx (size unknown until HEAD)."""
    html = requests.get(LCA_PAGE, headers={"User-Agent": UA}, timeout=60).text
    urls = re.findall(r'href="([^"]*LCA_Disclosure_Data_FY\d{4}_Q\d\.xlsx)"', html)
    if not urls:
        return []
    url = urls[0] if urls[0].startswith("http") else "https://www.dol.gov" + urls[0]
    return [(url.rsplit("/", 1)[1], url, 0)]


def download(dest: Path, url: str, size: int, headers: dict) -> str:
    """Resume-capable GET into dest. size=0 means trust Content-Length."""
    if dest.exists() and (size == 0 or dest.stat().st_size == size):
        return f"skip {dest.name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    for attempt in range(6):
        have = part.stat().st_size if part.exists() else 0
        h = dict(headers)
        if have:
            h["Range"] = f"bytes={have}-"
        try:
            with requests.get(url, headers=h, stream=True, timeout=120, allow_redirects=True) as r:
                if r.status_code == 416:            # .part already complete
                    break
                if have and r.status_code == 200:   # server ignored Range: restart
                    have = 0
                r.raise_for_status()
                if not size:
                    size = have + int(r.headers.get("Content-Length") or 0)
                with open(part, "ab" if have else "wb") as fh:
                    for chunk in r.iter_content(CHUNK):
                        fh.write(chunk)
            if not size or part.stat().st_size >= size:
                break
        except requests.exceptions.RequestException:
            time.sleep(2 ** attempt * 5)
    got = part.stat().st_size
    if size and got != size:
        return f"FAIL {dest.name}: {got}/{size} bytes (rerun to resume)"
    part.rename(dest)
    return f"ok   {dest.name} ({got / 1e6:,.0f} MB)"


def plan(groups: list[str]) -> list[tuple[Path, str, int, dict]]:
    jobs = []
    odp = [g for g in groups if g in ODP_GROUPS]
    if odp:
        key = api_key()
        for g in odp:
            product, pattern = ODP_GROUPS[g]
            for rel, url, size in odp_files(product, pattern, key):
                jobs.append((data_dir(f"bulk/{g}") / rel.replace("/", "_"), url, size, {"X-API-Key": key}))
    if "sec" in groups:
        for name, url in SEC_FILES.items():
            jobs.append((data_dir("bulk/sec") / name, url, 0, {"User-Agent": UA}))
    if "lca" in groups:
        for name, url, size in lca_files():
            jobs.append((data_dir("bulk/lca") / name, url, size, {"User-Agent": UA}))
    return jobs


def main(argv: list[str]) -> None:
    groups = argv or [*ODP_GROUPS, "sec", "lca"]
    jobs = plan(groups)
    total = sum(s for _, _, s, _ in jobs)
    print(f"{len(jobs)} files, {total / 1e9:.1f} GB known size, groups={groups}", flush=True)
    # SEC asks for <=10 req/s; 3 concurrent streams of large files is far under.
    with ThreadPoolExecutor(3) as ex:
        for msg in ex.map(lambda j: download(*j), jobs):
            print(msg, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
