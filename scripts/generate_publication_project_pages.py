#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import bibtexparser

# -----------------------
# Config
# -----------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
BIB_DB_ROOT = REPO_ROOT / "static" / "bib_database"

REQUIRED_INFO_FILES = [
    Path("info/abstract.txt"),
    Path("info/tags.csv"),
    Path("info/video_links.csv"),
    Path("info/github_link.txt"),
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
MISC_EXTS = {".pdf", ".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg", ".pptx", ".zip"}

AUTO_INDEX_PATH = BIB_DB_ROOT / "index.md"

MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

MONTH_REGEX = re.compile(
    r"\b("
    r"January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|"
    r"September|Sep|Sept|October|Oct|November|Nov|December|Dec"
    r")\b",
    re.IGNORECASE,
)

# Matches: "October 1-5, 2018" or "October 1, 2018"
MONTH_DAY_YEAR_REGEX = re.compile(
    r"\b(?P<month>January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|"
    r"September|Sep|Sept|October|Oct|November|Nov|December|Dec)"
    r"\s+(?P<day>\d{1,2})(?:\s*[-–]\s*\d{1,2})?"
    r"\s*,\s*(?P<year>\d{4})\b",
    re.IGNORECASE,
)

# Matches: "October 2018"
MONTH_YEAR_REGEX = re.compile(
    r"\b(?P<month>January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|"
    r"September|Sep|Sept|October|Oct|November|Nov|December|Dec)"
    r"\s+(?P<year>\d{4})\b",
    re.IGNORECASE,
)

TOML_FM_REGEX = re.compile(r"(?s)\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n")


@dataclass(frozen=True)
class PublicationRef:
    category: str
    key: str
    folder: Path  # absolute path to pub folder


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def read_text_strict(path: Path) -> str:
    if not path.exists():
        die(f"Missing required file: {path.relative_to(REPO_ROOT)}")
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        die(f"Failed reading {path.relative_to(REPO_ROOT)}: {e}")


def read_lines_allow_empty_strict(path: Path) -> list[str]:
    # File must exist, but may be empty.
    txt = read_text_strict(path)
    lines = [ln.strip() for ln in txt.splitlines()]
    return [ln for ln in lines if ln]


def parse_gen_lock(existing_index_md: Path) -> bool:
    if not existing_index_md.exists():
        return False

    raw = existing_index_md.read_text(encoding="utf-8", errors="replace")
    m = TOML_FM_REGEX.search(raw)
    if not m:
        return False

    fm = m.group(1)
    # Use tomllib in 3.11
    import tomllib
    try:
        data = tomllib.loads(fm)
    except Exception:
        # If front matter is malformed, fail (strict)
        die(f"Malformed TOML front matter in {existing_index_md.relative_to(REPO_ROOT)}")

    return bool(data.get("gen_lock", False) is True)


def sanitize_bibtex_title(title: str) -> str:
    # Keep it simple: remove common LaTeX braces; don't attempt full LaTeX -> unicode conversion
    t = title.replace("{", "").replace("}", "")
    return " ".join(t.split())


def split_authors(author_field: str) -> list[str]:
    # BibTeX: "A and B and C"
    parts = [a.strip() for a in author_field.split(" and ") if a.strip()]
    # Normalize "Last, First" to "First Last" for display
    out = []
    for p in parts:
        if "," in p:
            last, first = [x.strip() for x in p.split(",", 1)]
            out.append(f"{first} {last}".strip())
        else:
            out.append(p)
    return out


def infer_date(entry: dict) -> str:
    """
    Requirement: use year + venue text (booktitle/journal/etc) to infer a full date.
    Rule implemented:
      - If BibTeX has 'month' (jan/feb/... or number), use it (day=1).
      - Else, search date-like text in a priority list of fields and parse:
        * Month day-range, year  -> YYYY-MM-DD using first day
        * Month year             -> YYYY-MM-01
      - Else fallback: YYYY-01-01
    """
    year_raw = str(entry.get("year", "")).strip()
    if not re.fullmatch(r"\d{4}", year_raw):
        die(f"BibTeX entry missing/invalid 'year' for key '{entry.get('ID', '<unknown>')}'")

    year = int(year_raw)

    # 1) month field
    month_raw = str(entry.get("month", "")).strip()
    if month_raw:
        mnorm = month_raw.strip().lower().strip("{}").strip()
        # Some bibs use "oct" or "10"
        if mnorm.isdigit():
            mm = int(mnorm)
            if 1 <= mm <= 12:
                return f"{year:04d}-{mm:02d}-01"
        mm = MONTHS.get(mnorm)
        if mm:
            return f"{year:04d}-{mm:02d}-01"

    # 2) parse from descriptive fields
    field_candidates = [
        "booktitle", "journal", "howpublished", "note", "eventtitle", "eventdate"
    ]
    text_blob = " ".join(str(entry.get(f, "") or "") for f in field_candidates)

    # Prefer full date occurrences first
    m1 = MONTH_DAY_YEAR_REGEX.search(text_blob)
    if m1:
        month = MONTHS[m1.group("month").lower()]
        day = int(m1.group("day"))
        y2 = int(m1.group("year"))
        # If year in text differs, trust the bib 'year' but keep month/day
        return f"{year:04d}-{month:02d}-{day:02d}"

    m2 = MONTH_YEAR_REGEX.search(text_blob)
    if m2:
        month = MONTHS[m2.group("month").lower()]
        return f"{year:04d}-{month:02d}-01"

    # 3) fallback
    return f"{year:04d}-01-01"


def bibtex_type(entry: dict) -> str:
    # bibtexparser uses ENTRYTYPE
    t = str(entry.get("ENTRYTYPE", "")).strip().lower()
    return t or "unknown"


def doi_url(entry: dict) -> Optional[str]:
    doi = str(entry.get("doi", "")).strip()
    if doi:
        return f"https://doi.org/{doi}"
    url = str(entry.get("url", "")).strip()
    if "doi.org/" in url:
        return url
    return None


def find_publications() -> list[PublicationRef]:
    if not BIB_DB_ROOT.exists():
        die(f"Missing folder: {BIB_DB_ROOT.relative_to(REPO_ROOT)}")

    pubs: list[PublicationRef] = []
    for category_dir in sorted([p for p in BIB_DB_ROOT.iterdir() if p.is_dir()]):
        category = category_dir.name
        for pub_dir in sorted([p for p in category_dir.iterdir() if p.is_dir()]):
            key = pub_dir.name
            pubs.append(PublicationRef(category=category, key=key, folder=pub_dir))
    return pubs


def list_files_with_ext(folder: Path, exts: set[str]) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    files.sort(key=lambda p: p.name.lower())
    return files


def ensure_required_files(pub: PublicationRef) -> None:
    bib_path = pub.folder / f"{pub.key}.bib"
    if not bib_path.exists():
        die(f"Missing required bib file: {bib_path.relative_to(REPO_ROOT)}")

    for rel in REQUIRED_INFO_FILES:
        p = pub.folder / rel
        if not p.exists():
            die(f"Missing required file: {p.relative_to(REPO_ROOT)}")


def parse_bib_file(bib_path: Path) -> dict:
    raw = read_text_strict(bib_path)
    try:
        db = bibtexparser.loads(raw)
    except Exception as e:
        die(f"BibTeX parse failed for {bib_path.relative_to(REPO_ROOT)}: {e}")

    if not db.entries:
        die(f"No BibTeX entries found in {bib_path.relative_to(REPO_ROOT)}")
    if len(db.entries) != 1:
        die(f"Expected exactly 1 entry in {bib_path.relative_to(REPO_ROOT)}, found {len(db.entries)}")

    return db.entries[0]


def build_pub_index_md(pub: PublicationRef) -> str:
    ensure_required_files(pub)

    bib_path = pub.folder / f"{pub.key}.bib"
    entry = parse_bib_file(bib_path)

    title = sanitize_bibtex_title(str(entry.get("title", "")).strip())
    if not title:
        die(f"BibTeX entry missing 'title' in {bib_path.relative_to(REPO_ROOT)}")

    author_field = str(entry.get("author", "")).strip()
    if not author_field:
        die(f"BibTeX entry missing 'author' in {bib_path.relative_to(REPO_ROOT)}")
    authors = split_authors(author_field)

    btype = bibtex_type(entry)
    date_str = infer_date(entry)

    abstract = read_text_strict(pub.folder / "info" / "abstract.txt").strip()

    tags = read_lines_allow_empty_strict(pub.folder / "info" / "tags.csv")
    videos = read_lines_allow_empty_strict(pub.folder / "info" / "video_links.csv")

    gh_lines = read_lines_allow_empty_strict(pub.folder / "info" / "github_link.txt")
    github_link = gh_lines[0] if gh_lines else ""

    paper_link = doi_url(entry)

    # Images gallery
    images_dir = pub.folder / "images"
    images = list_files_with_ext(images_dir, IMAGE_EXTS)

    # Misc downloads
    misc_dir = pub.folder / "misc"
    misc_files = list_files_with_ext(misc_dir, MISC_EXTS)

    # Absolute path style (as requested): "static/bib_database/..."
    base_abs = f"static/bib_database/{pub.category}/{pub.key}"

    # Front matter (TOML)
    # Note: you required `author: [separated string with author names]` but also "list".
    # We write an array; Hugo supports that.
    tag_list = ["publication", btype] + tags

    fm_lines = []
    fm_lines.append("+++")
    fm_lines.append(f'title = {toml_string(title)}')
    fm_lines.append(f'date = {toml_string(date_str)}')
    fm_lines.append(f'categories = ["publication", {toml_string(btype)}]')
    fm_lines.append(f"tags = {toml_array(tag_list)}")
    fm_lines.append(f"author = {toml_array(authors)}")
    fm_lines.append(f"keywords = {toml_array(tags)}")
    fm_lines.append("draft = false")
    fm_lines.append("+++")
    fm = "\n".join(fm_lines)

    # Body
    body = []

    # 1) Title
    body.append(f"# {title}")
    body.append("")

    # 2) Authors
    body.append("**Authors:** " + ", ".join(authors))
    body.append("")

    # 3) Links
    links = []
    if github_link:
        links.append(f"- **Code:** {github_link}")
    else:
        links.append("- **Code:** <!-- TODO: add GitHub link -->")
    if paper_link:
        links.append(f"- **Paper (DOI):** {paper_link}")
    else:
        links.append("- **Paper (DOI):** <!-- TODO: DOI missing in BibTeX -->")
    body.append("## Links")
    body.extend(links)
    body.append("")

    # 4) Figures
    body.append("## Gallery")
    if images:
        for img in images:
            img_path = f"{base_abs}/images/{img.name}"
            # Simple Markdown image embed
            body.append(f"![{img.stem}]({img_path})")
    else:
        body.append("_No images available._")
    body.append("")

    # 5) Abstract
    body.append("## Abstract")
    if abstract:
        body.append(abstract)
    else:
        body.append("<!-- TODO: add abstract -->")
    body.append("")

    # 6) Tags and keywords
    body.append("## Tags")
    if tags:
        body.append(", ".join(tags))
    else:
        body.append("<!-- No tags provided -->")
    body.append("")

    # 7) Videos + misc
    body.append("## Videos")
    if videos:
        for v in videos:
            body.append(f"- {v}")
    else:
        body.append("<!-- No videos provided -->")
    body.append("")

    body.append("## Downloads")
    if misc_files:
        for f in misc_files:
            fpath = f"{base_abs}/misc/{f.name}"
            body.append(f"- [{f.name}]({fpath})")
    else:
        body.append("_No additional files._")
    body.append("")

    # 8) Plain bib information
    body.append("## BibTeX")
    body.append("```bibtex")
    body.append(read_text_strict(bib_path).rstrip())
    body.append("```")
    body.append("")

    return fm + "\n\n" + "\n".join(body)


def toml_string(s: str) -> str:
    # Minimal TOML string escaper
    s2 = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s2}"'


def toml_array(items: Iterable[str]) -> str:
    return "[" + ", ".join(toml_string(str(x)) for x in items) + "]"


def write_pub_index(pub: PublicationRef) -> bool:
    """
    Returns True if a file was written/updated, False if skipped (gen_lock=true).
    """
    index_path = pub.folder / "index.md"
    if parse_gen_lock(index_path):
        # Locked; do not overwrite
        return False

    content = build_pub_index_md(pub)
    index_path.write_text(content, encoding="utf-8")
    return True


def build_aggregate_index(pubs: list[PublicationRef]) -> str:
    today = _dt.date.today().isoformat()

    # TOML front matter for the aggregate index (kept simple)
    fm = "\n".join([
        "+++",
        f'title = "bib_database index"',
        f'date = "{today}"',
        'categories = ["publication"]',
        'tags = ["publication"]',
        "draft = false",
        "+++",
        "",
    ])

    # Sort by publication key (global alphabetical across categories)
    pubs_sorted = sorted(pubs, key=lambda p: p.key.lower())

    lines = []
    lines.append("# Publication index")
    lines.append("")
    for p in pubs_sorted:
        link = f"static/bib_database/{p.category}/{p.key}/index.md"
        lines.append(f"- [{p.key}]({link})")
    lines.append("")
    return fm + "\n".join(lines)


def main() -> None:
    pubs = find_publications()
    if not pubs:
        die("No publications found under static/bib_database/<category>/<key>/")

    wrote_any = 0
    skipped = 0
    for pub in pubs:
        # Validate required folder structure early (strict mode):
        ensure_required_files(pub)

        did_write = write_pub_index(pub)
        if did_write:
            wrote_any += 1
        else:
            skipped += 1

    # Aggregate index always regenerated
    AUTO_INDEX_PATH.write_text(build_aggregate_index(pubs), encoding="utf-8")

    print(f"Done. Updated: {wrote_any} publication pages. Skipped (gen_lock=true): {skipped}.")
    print(f"Updated aggregate index: {AUTO_INDEX_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    # Ensure working dir isn't relevant; always operate from repo root paths
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        die(f"Unhandled exception: {e}")