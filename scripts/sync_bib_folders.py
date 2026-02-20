#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


# Matches entry header: @article{Key,
ENTRY_HEADER_RE = re.compile(r"@(?P<etype>\w+)\s*{\s*(?P<key>[^,\s]+)\s*,", re.IGNORECASE)

# Roughly finds an entire entry block by balancing braces.
# This is a pragmatic parser: good for typical .bib files.
def split_bib_entries(text: str) -> List[str]:
    entries: List[str] = []
    i = 0
    n = len(text)

    while i < n:
        m = re.search(r"@\w+\s*{", text[i:], flags=re.IGNORECASE)
        if not m:
            break
        start = i + m.start()

        # Find the end by brace balancing starting at first "{"
        brace_start = text.find("{", start)
        if brace_start == -1:
            break

        depth = 0
        j = brace_start
        while j < n:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    # include closing brace
                    entries.append(text[start : j + 1].strip())
                    i = j + 1
                    break
            j += 1
        else:
            # Unbalanced braces; stop.
            break

    return entries


@dataclass(frozen=True)
class BibEntry:
    key: str
    entry_type: str
    raw: str


def parse_entries(bib_text: str) -> List[BibEntry]:
    raw_entries = split_bib_entries(bib_text)
    parsed: List[BibEntry] = []

    for raw in raw_entries:
        m = ENTRY_HEADER_RE.search(raw)
        if not m:
            continue
        etype = m.group("etype").lower().strip()
        key = m.group("key").strip()
        parsed.append(BibEntry(key=key, entry_type=etype, raw=raw))

    return parsed

def is_arxiv(entry: BibEntry) -> bool:
    raw = entry.raw.lower()

    # Common BibTeX arXiv indicators:
    # - archivePrefix = {arXiv}
    # - eprint = {2401.12345}
    # - journal = {arXiv preprint ...}
    # - url contains arxiv.org
    if "arxiv.org" in raw:
        return True
    if re.search(r"\barchiveprefix\s*=\s*[{\"\']\s*arxiv\s*[{\"\']", raw):
        return True
    if re.search(r"\beprint\s*=\s*[{\"\']\s*\d{4}\.\d{4,5}\s*[{\"\']", raw):
        return True
    if "arxiv" in raw and "arxiv preprint" in raw:
        return True

    # Slightly broader fallback: if the entry mentions arXiv anywhere.
    # Comment this out if you want stricter matching.
    if "arxiv" in raw:
        return True

    return False

def normalize_bibkey(key: str) -> str:
    """
    Strip DBLP-style slash prefixes:
      DBLP/conf/iros/Smith2024 -> Smith2024
      DBLP/journals/tro/Miller2023 -> Miller2023
    """
    key = key.strip()

    # If it contains slashes, take only the last segment
    if "/" in key:
        return key.split("/")[-1]

    return key



def make_safe_folder_name(key: str) -> str:
    key = key.strip()
    key = key.replace("/", "_").replace("\\", "_")
    key = re.sub(r"[:*?\"<>|]", "_", key)  # Windows-illegal chars
    return key


def category_for_entry(entry: BibEntry, fallback: str = "misc") -> str:
    """
    Map BibTeX entry types to your folder categories.
    Adjust mapping rules here to match your bib conventions.
    """
    t = entry.entry_type

    mapping: Dict[str, str] = {
        # journals
        "article": "journal_papers",
        "periodical": "journal_papers",

        # conferences / workshops
        "inproceedings": "conference_papers",
        "proceedings": "conference_papers",
        "conference": "conference_papers",

        # books
        "book": "books",

        # book chapters
        "incollection": "book_chapters",
        "inbook": "book_chapters",

        # theses
        "phdthesis": "theses",
        "mastersthesis": "theses",
        "thesis": "theses",

        # preprints-ish
        "unpublished": "preprints",
        "misc": "preprints",
        "techreport": "preprints",
        "report": "preprints",
    }

    return mapping.get(t, fallback)


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def ensure_entry_scaffold(
    base_dir: Path,
    category: str,
    entry: BibEntry,
    dry_run: bool,
) -> tuple[bool, Path]:
    """
    Create the scaffold for one bib entry.
    Only checks existence of the outer folder (the bibkey folder).
    Returns: (created?, entry_folder_path)
    """
    clean_key = normalize_bibkey(entry.key)
    safe_key = make_safe_folder_name(clean_key)
    entry_dir = base_dir / category / safe_key

    if entry_dir.exists():
        return (False, entry_dir)

    if dry_run:
        return (True, entry_dir)

    # Create outer + required subfolders
    (entry_dir / "images").mkdir(parents=True, exist_ok=False)
    (entry_dir / "misc").mkdir(parents=True, exist_ok=False)
    (entry_dir / "info").mkdir(parents=True, exist_ok=False)

    # Files in entry folder
    index_md = (
        "---\n"
        f'title: "{entry.key}"\n'
        f"bibkey: {entry.key}\n"
        f"category: {category}\n"
        "draft: true\n"
        "---\n\n"
        "Auto-generated entry scaffold.\n"
    )
    write_if_missing(entry_dir / "index.md", index_md)

    # Raw bib entry stored alongside
    bib_filename = safe_key + ".bib"
    write_if_missing(entry_dir / bib_filename, entry.raw.strip() + "\n")

    # Files inside info/
    write_if_missing(entry_dir / "info" / "tags.csv", "tag\n")
    write_if_missing(entry_dir / "info" / "abstract.txt", "")
    write_if_missing(entry_dir / "info" / "video_links.csv", "url\n")
    write_if_missing(entry_dir / "info" / "github_link.txt", "")
    write_if_missing(entry_dir / "images" / ".gitkeep", "")
    write_if_missing(entry_dir / "misc" / ".gitkeep", "")

    # Extra file for preprints only
    if category == "preprints":
        write_if_missing(entry_dir / "published.txt", "")

    return (True, entry_dir)


def main() -> int:
    p = argparse.ArgumentParser(description="Sync bib_database folder scaffolding from a BibTeX file.")
    p.add_argument("--bib", default="bibliography.bib", help="Path to .bib file relative to repo root")
    p.add_argument(
        "--out",
        default="static/bib_database",
        help="Output directory relative to repo root (default: static/bib_database)",
    )
    p.add_argument("--dry-run", action="store_true", help="Print actions without writing")

    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    bib_path = (repo_root / args.bib).resolve()
    out_dir = (repo_root / args.out).resolve()

    if not bib_path.exists():
        raise FileNotFoundError(f"Bib file not found: {bib_path}")

    bib_text = bib_path.read_text(encoding="utf-8")
    entries = parse_entries(bib_text)
    if not entries:
        print("No BibTeX entries found.")
        return 0

    # Ensure category folders exist
    categories = ["journal_papers", "conference_papers", "books", "book_chapters", "theses", "preprints", "misc"]
    for cat in categories:
        (out_dir / cat).mkdir(parents=True, exist_ok=True)

    created = skipped = 0

    for entry in entries:
        # arXiv wins: goes ONLY to preprints
        cat = "preprints" if is_arxiv(entry) else category_for_entry(entry)

        did_create, entry_dir = ensure_entry_scaffold(out_dir, cat, entry, dry_run=args.dry_run)
        if did_create:
            created += 1
            if args.dry_run:
                print(f"[dry-run] Would create scaffold: {entry_dir}")
            else:
                print(f"Created scaffold: {entry_dir}")
        else:
            skipped += 1



    print(f"Done. Entries: {len(entries)} | Created: {created} | Skipped (already existed): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
