#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import shutil

# -----------------------
# Paths
# -----------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "static" / "bib_database"
DEST_ROOT = REPO_ROOT / "content" / "project_manuscripts"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def ensure_destination_dir() -> None:
    DEST_ROOT.mkdir(parents=True, exist_ok=True)


def find_publication_folders() -> list[Path]:
    if not SOURCE_ROOT.exists():
        die(f"Missing source directory: {SOURCE_ROOT.relative_to(REPO_ROOT)}")

    publication_dirs: list[Path] = []

    # Traverse all subfolders regardless of name
    for category_dir in SOURCE_ROOT.iterdir():
        if not category_dir.is_dir():
            continue

        for pub_dir in category_dir.iterdir():
            if pub_dir.is_dir():
                publication_dirs.append(pub_dir)

    return sorted(publication_dirs, key=lambda p: p.name.lower())


def copy_index_file(pub_dir: Path) -> None:
    key = pub_dir.name
    source_file = pub_dir / "index.md"

    if not source_file.exists():
        die(f"Missing required file: {source_file.relative_to(REPO_ROOT)}")

    dest_file = DEST_ROOT / f"{key}.md"

    try:
        content = source_file.read_text(encoding="utf-8")
    except Exception as e:
        die(f"Failed reading {source_file.relative_to(REPO_ROOT)}: {e}")

    try:
        dest_file.write_text(content, encoding="utf-8")
    except Exception as e:
        die(f"Failed writing {dest_file.relative_to(REPO_ROOT)}: {e}")


def main() -> None:
    ensure_destination_dir()

    publication_dirs = find_publication_folders()

    if not publication_dirs:
        die("No publication folders found in static/bib_database/")

    count = 0
    for pub_dir in publication_dirs:
        copy_index_file(pub_dir)
        count += 1

    print(f"Copied {count} publication pages to content/project_manuscripts/")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        die(f"Unhandled exception: {e}")