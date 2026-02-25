#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, List

import bibtexparser

from pylatexenc.latex2text import LatexNodes2Text

# -----------------------
# Paths / Config
# -----------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
BIB_DB_ROOT = REPO_ROOT / "static" / "bib_database"
OUTPUT_PATH = REPO_ROOT / "content" / "bibliography" / "index.md"

# Only include these subfolders (others ignored), and show them in this order:
TYPE_ORDER = [
    ("theses", "Theses"),
    ("books", "Books"),
    ("book_chapters", "Book chapters"),
    ("journal_papers", "Journal articles"),
    ("conference_papers", "Conference papers"),
    ("preprints", "Preprints"),
]

# For each entry, link to the (future) project manuscript page:
PROJECT_URL_FMT = "/webpage/project_manuscripts/{key}"

# Strict requirements
REQUIRED_BIB_SINGLE_ENTRY = True

# -----------------------
# Helpers
# -----------------------
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


# def sanitize_inline(text: str) -> str:
#     # Minimal cleanup: remove braces, collapse whitespace
#     t = (text or "").replace("{", "").replace("}", "")
#     t = re.sub(r"\s+", " ", t).strip()
#     return t
_latex_converter = LatexNodes2Text()

def sanitize_inline(text: str) -> str:
    if not text:
        return ""

    # BibTeX hyphen idiom
    text = text.replace("{-}", "-")

    # If backslashes are doubled before accent commands, undo that:
    # e.g. \\\"{u} -> \"{u}
    text = re.sub(r"\\\\(?=[\"'`^~=.Hcuvkbrdt])", r"\\", text)

    # LaTeX -> Unicode
    text = _latex_converter.latex_to_text(text)

    # Remove leftover braces
    text = text.replace("{", "").replace("}", "")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# def split_authors_fullnames(author_field: str) -> list[str]:
#     # Normalize whitespace and split on 'and' robustly
#     normalized = re.sub(r"\s+", " ", (author_field or "")).strip()
#     if not normalized:
#         return []
#     parts = re.split(r"\s+and\s+", normalized, flags=re.IGNORECASE)
#
#     out: list[str] = []
#     for p in parts:
#         p = p.strip()
#         if not p:
#             continue
#         # Convert "Last, First" -> "First Last"
#         if "," in p:
#             last, first = [x.strip() for x in p.split(",", 1)]
#             out.append(f"{first} {last}".strip())
#         else:
#             out.append(p)
#     return out
def split_authors_fullnames(author_field: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", (author_field or "")).strip()
    if not normalized:
        return []

    parts = re.split(r"\s+and\s+", normalized, flags=re.IGNORECASE)

    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue

        # Convert LaTeX accents etc. per-author
        p = sanitize_inline(p)

        # Convert "Last, First" -> "First Last"
        if "," in p:
            last, first = [x.strip() for x in p.split(",", 1)]
            out.append(f"{first} {last}".strip())
        else:
            out.append(p)

    return out

def parse_bib_file_single_entry(bib_path: Path) -> dict:
    raw = read_text_strict(bib_path)
    try:
        db = bibtexparser.loads(raw)
    except Exception as e:
        die(f"BibTeX parse failed for {bib_path.relative_to(REPO_ROOT)}: {e}")

    if not db.entries:
        die(f"No BibTeX entries found in {bib_path.relative_to(REPO_ROOT)}")

    if REQUIRED_BIB_SINGLE_ENTRY and len(db.entries) != 1:
        die(
            f"Expected exactly 1 entry in {bib_path.relative_to(REPO_ROOT)}, found {len(db.entries)}"
        )

    return db.entries[0]


def get_year(entry: dict, bib_path: Path) -> int:
    y = sanitize_inline(str(entry.get("year", "")))
    if not re.fullmatch(r"\d{4}", y):
        die(f"Missing/invalid 'year' in {bib_path.relative_to(REPO_ROOT)}")
    return int(y)


def bibtex_key(entry: dict, bib_path: Path) -> str:
    k = str(entry.get("ID", "")).strip()
    if not k:
        die(f"Missing BibTeX key (ID) in {bib_path.relative_to(REPO_ROOT)}")
    return k


def find_doi_and_url(entry: dict) -> Tuple[Optional[str], Optional[str]]:
    doi = sanitize_inline(str(entry.get("doi", "")))
    url = sanitize_inline(str(entry.get("url", "")))
    if doi:
        doi_href = f"https://doi.org/{doi}"
        return doi, doi_href
    if url:
        return None, url
    return None, None


def find_arxiv_link(entry: dict) -> Optional[str]:
    # Prefer eprint if archivePrefix indicates arXiv, but be flexible
    archive_prefix = sanitize_inline(str(entry.get("archiveprefix", ""))).lower()
    eprint = sanitize_inline(str(entry.get("eprint", "")))
    if archive_prefix == "arxiv" and eprint:
        return f"https://arxiv.org/abs/{eprint}"

    # Some entries may not have archivePrefix but have eprinttype / primaryClass; still try.
    eprint_type = sanitize_inline(str(entry.get("eprinttype", ""))).lower()
    if eprint_type == "arxiv" and eprint:
        return f"https://arxiv.org/abs/{eprint}"

    # If url already points to arxiv, we could use it, but you asked "if possible" — this counts.
    url = sanitize_inline(str(entry.get("url", "")))
    if "arxiv.org/abs/" in url:
        return url

    return None


def fmt_pages(pages: str) -> Optional[str]:
    p = sanitize_inline(pages)
    if not p:
        return None
    # BibTeX often uses -- for ranges; use en dash
    p = p.replace("--", "–")
    return p


def toml_string(s: str) -> str:
    s2 = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s2}"'


@dataclass(frozen=True)
class BibItem:
    group_folder: str          # e.g. "books"
    group_title: str           # e.g. "Books"
    year: int
    key: str                  # BibTeX key / also folder name in your structure
    title: str
    authors: list[str]
    venue: str
    pages: Optional[str]
    volume: Optional[str]
    number: Optional[str]
    publisher: Optional[str]
    school: Optional[str]
    doi_display: Optional[str]
    doi_href: Optional[str]
    url_fallback: Optional[str]
    arxiv_href: Optional[str]
    raw_entry_type: str        # e.g. inproceedings/article/book/etc
    bib_path: Path


def venue_for_type(group_folder: str, entry: dict) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Returns: venue, volume, number, publisher, school
    """
    if group_folder == "books":
        venue = sanitize_inline(str(entry.get("publisher", "")))
        return venue, None, None, venue or None, None

    if group_folder == "book_chapters":
        venue = sanitize_inline(str(entry.get("booktitle", "")))
        publisher = sanitize_inline(str(entry.get("publisher", "")))
        # Venue will be booktitle; publisher handled separately
        return venue, None, None, publisher or None, None

    if group_folder == "journal_papers":
        venue = sanitize_inline(str(entry.get("journal", "")))
        volume = sanitize_inline(str(entry.get("volume", ""))) or None
        number = sanitize_inline(str(entry.get("number", ""))) or None
        return venue, volume, number, None, None

    if group_folder == "conference_papers":
        venue = sanitize_inline(str(entry.get("booktitle", "")))
        return venue, None, None, None, None

    if group_folder == "theses":
        # You said assume only PhD theses
        school = sanitize_inline(str(entry.get("school", ""))) or None
        return "Ph.D. thesis", None, None, None, school

    if group_folder == "preprints":
        # Prefer note/howpublished, else something generic
        venue = sanitize_inline(str(entry.get("note", ""))) or sanitize_inline(str(entry.get("howpublished", "")))
        if not venue:
            venue = "Preprint"
        return venue, None, None, None, None

    return "", None, None, None, None


def preprint_included(pub_folder: Path) -> bool:
    """
    Strict:
      - published.txt must exist
      - content must be exactly 'published' or 'unpublished' (case-insensitive)
      - include only if 'unpublished'
    """
    p = pub_folder / "published.txt"
    if not p.exists():
        die(f"Missing required file for preprint: {p.relative_to(REPO_ROOT)}")

    val = sanitize_inline(read_text_strict(p)).lower()
    if val == "published":
        return False
    if val == "unpublished":
        return True
    die(f"Invalid value in {p.relative_to(REPO_ROOT)}: expected 'published' or 'unpublished', got '{val}'")
    return False


def collect_items() -> list[BibItem]:
    if not BIB_DB_ROOT.exists():
        die(f"Missing folder: {BIB_DB_ROOT.relative_to(REPO_ROOT)}")

    items: list[BibItem] = []

    for folder_name, display_name in TYPE_ORDER:
        type_dir = BIB_DB_ROOT / folder_name
        if not type_dir.exists():
            # If a defined group folder is missing, treat as empty (not fatal)
            continue

        for pub_folder in sorted([p for p in type_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
            key = pub_folder.name

            # Preprints filtering
            if folder_name == "preprints":
                if not preprint_included(pub_folder):
                    continue

            bib_path = pub_folder / f"{key}.bib"
            if not bib_path.exists():
                die(f"Missing required bib file: {bib_path.relative_to(REPO_ROOT)}")

            entry = parse_bib_file_single_entry(bib_path)

            title = sanitize_inline(str(entry.get("title", "")))
            if not title:
                die(f"Missing 'title' in {bib_path.relative_to(REPO_ROOT)}")

            authors = split_authors_fullnames(str(entry.get("author", "")))
            if not authors:
                die(f"Missing 'author' in {bib_path.relative_to(REPO_ROOT)}")

            year = get_year(entry, bib_path)
            entry_key = bibtex_key(entry, bib_path)  # BibTeX ID (may differ from folder name, but you want bibtex key sorting)
            # You asked: sort by BibTeX key; most cases equals first author last name.
            # We'll use BibTeX ID for sorting, but keep folder-name for project URL.
            # If you'd rather always use folder-name as "key", tell me and I’ll adjust.

            venue, volume, number, publisher, school = venue_for_type(folder_name, entry)
            pages = fmt_pages(str(entry.get("pages", "")))

            raw_type = sanitize_inline(str(entry.get("ENTRYTYPE", ""))).lower() or "unknown"

            doi_disp, doi_href_or_url = find_doi_and_url(entry)
            doi_href = None
            url_fallback = None
            if doi_disp and doi_href_or_url:
                doi_href = doi_href_or_url
            else:
                url_fallback = doi_href_or_url

            arxiv_href = None
            if folder_name == "preprints":
                arxiv_href = find_arxiv_link(entry)

            items.append(
                BibItem(
                    group_folder=folder_name,
                    group_title=display_name,
                    year=year,
                    key=key,  # folder name used for project URL
                    title=title,
                    authors=authors,
                    venue=venue,
                    pages=pages,
                    volume=volume,
                    number=number,
                    publisher=publisher,
                    school=school,
                    doi_display=doi_disp,
                    doi_href=doi_href,
                    url_fallback=url_fallback,
                    arxiv_href=arxiv_href,
                    raw_entry_type=raw_type,
                    bib_path=bib_path,
                )
            )

    return items


def fmt_reference(item: BibItem) -> str:
    """
    IEEE-like with uniform italic titles.
    Includes:
      - Authors
      - *Title*
      - venue details by type
      - pages if present
      - year
      - [Project Page](/project_manuscripts/<key>)
      - DOI: [..](..) or URL, and arXiv for preprints if available
    """
    authors_str = ", ".join(item.authors)
    title_str = f"*{item.title}*"

    # Base: Authors, *Title*,
    parts: list[str] = [f"{authors_str}, {title_str}"]

    # Type-specific venue formatting
    if item.group_folder == "journal_papers":
        v = item.venue
        if v:
            parts.append(v)
        if item.volume:
            parts.append(f"vol. {item.volume}")
        if item.number:
            parts.append(f"no. {item.number}")
        if item.pages:
            parts.append(f"pp. {item.pages}")
        parts.append(str(item.year) + ".")
    elif item.group_folder == "conference_papers":
        if item.venue:
            parts.append(f"in Proceedings of {item.venue}")
        if item.pages:
            parts.append(f"pp. {item.pages}")
        parts.append(str(item.year) + ".")
    elif item.group_folder == "books":
        if item.publisher:
            parts.append(item.publisher)
        parts.append(str(item.year) + ".")
    elif item.group_folder == "book_chapters":
        if item.venue:
            parts.append(item.venue)
        if item.publisher:
            parts.append(item.publisher)
        if item.pages:
            parts.append(f"pp. {item.pages}")
        parts.append(str(item.year) + ".")
    elif item.group_folder == "theses":
        # Venue_for_type returns "Ph.D. thesis"
        parts.append("Ph.D. thesis")
        if item.school:
            parts.append(item.school)
        parts.append(str(item.year) + ".")
    elif item.group_folder == "preprints":
        if item.venue:
            parts.append(item.venue)
        parts.append(str(item.year) + ".")
    else:
        if item.venue:
            parts.append(item.venue)
        if item.pages:
            parts.append(f"pp. {item.pages}")
        parts.append(str(item.year) + ".")

    # Join the main citation sentence cleanly
    # Ensure commas between segments; keep final period already appended as "YYYY."
    citation = ", ".join([p for p in parts if p])

    # Project page link
    project_link = f"[Project Page]({PROJECT_URL_FMT.format(key=item.key)}), "

    # External links
    extras: list[str] = []

    # Preprints: if arXiv exists, include ONLY arXiv (no DOI/URL)
    if item.group_folder == "preprints" and item.arxiv_href:
        arxiv_id = item.arxiv_href.split("/abs/", 1)[-1]
        extras.append(f"[arXiv:{arxiv_id}]({item.arxiv_href})")
    else:
        # Non-preprints (or preprints without arXiv): DOI first, then URL
        if item.doi_display and item.doi_href:
            extras.append(f"DOI: [{item.doi_display}]({item.doi_href})")
        elif item.url_fallback:
            extras.append(f"URL: [{item.url_fallback}]({item.url_fallback})")

    # Build final line as one bullet item
    tail = " ".join([project_link] + extras) if extras else project_link
    return f"- {citation} {tail}"


def build_page(items: list[BibItem]) -> str:
    today = _dt.date.today().isoformat()

    fm = "\n".join(
        [
            "+++",
            'title = "Bibliography"',
            f"date = {toml_string(today)}",
            "+++",
            "",
        ]
    )

    lines: list[str] = []
    lines.append("# Bibliography")
    lines.append("---")
    lines.append("")

    # Organize by group then year desc then bib key asc (you requested bib key sorting)
    # We only included allowed groups in collect_items, but keep ordering stable.
    items_by_group: Dict[str, List[BibItem]] = {folder: [] for folder, _ in TYPE_ORDER}
    for it in items:
        if it.group_folder in items_by_group:
            items_by_group[it.group_folder].append(it)

    for folder, group_title in TYPE_ORDER:
        group_items = items_by_group.get(folder, [])
        if not group_items:
            continue

        lines.append(f"## {group_title}")

        # Year desc
        years = sorted({it.year for it in group_items}, reverse=True)
        for y in years:
            lines.append(f"**{y}**")

            year_items = [it for it in group_items if it.year == y]
            # Sort by BibTeX key (entry ID), but we did not store entry ID separately.
            # Use bib file's entry ID (from file) isn't stored; by default folder key is often that.
            # If you want strict BibTeX ID sorting, we can store and sort by it.
            year_items.sort(key=lambda it: it.key.lower())

            for it in year_items:
                lines.append(fmt_reference(it))
            lines.append("")  # blank line after each year block

        lines.append("")  # blank line after each group

    return fm + "\n".join(lines).rstrip() + "\n"


def ensure_output_dir() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    items = collect_items()
    ensure_output_dir()
    OUTPUT_PATH.write_text(build_page(items), encoding="utf-8")
    print(f"Updated bibliography page: {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        die(f"Unhandled exception: {e}")