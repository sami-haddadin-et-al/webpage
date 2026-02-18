from __future__ import annotations

import argparse
import re
from pathlib import Path

ENTRY_KEY_RE = re.compile(r"@\w+\s*{\s*([^,\s]+)\s*,", re.IGNORECASE)

def extract_keys(bib_text: str) -> set[str]:
    return {m.group(1).strip() for m in ENTRY_KEY_RE.finditer(bib_text)}

def make_safe_folder_name(key: str) -> str:
    key = key.strip()
    key = key.replace("/", "_").replace("\\", "_")
    key = re.sub(r"[:*?\"<>|]", "_", key)  # Windows-illegal chars
    return key

def ensure_hugo_stub(folder: Path, key: str, create_stub: bool) -> None:
    """
    For Hugo, a folder can be a page bundle if it contains index.md.
    Some themes prefer _index.md for section/list pages.
    Here we create index.md per entry (a single page per publication).
    """
    if not create_stub:
        return
    stub = folder / "index.md"
    if stub.exists():
        return
    stub.write_text(
        f"---\n"
        f'title: "{key}"\n'
        f"bibkey: {key}\n"
        f"draft: true\n"
        f"---\n\n"
        f"Auto-generated folder for `{key}`.\n",
        encoding="utf-8",
    )

def main() -> int:
    p = argparse.ArgumentParser(description="Create Hugo content folders from BibTeX entry keys.")
    p.add_argument("--bib", default="bibliography.bib", help="Path to .bib file (default: bibliography.bib)")
    p.add_argument("--section", default="publications", help="Subfolder under content/ (default: publications)")
    p.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    p.add_argument("--stub", action="store_true", help="Create index.md inside new folders (Hugo-friendly)")
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    bib_path = (repo_root / args.bib).resolve()
    content_dir = (repo_root / "content").resolve()
    out_dir = content_dir / args.section

    if not bib_path.exists():
        raise FileNotFoundError(f"Bib file not found: {bib_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    keys = sorted(extract_keys(bib_path.read_text(encoding="utf-8")))
    if not keys:
        print("No BibTeX keys found.")
        return 0

    created = skipped = 0
    for key in keys:
        folder_name = make_safe_folder_name(key)
        target = out_dir / folder_name

        if target.exists():
            skipped += 1
            continue

        if args.dry_run:
            print(f"[dry-run] Would create: {target}")
        else:
            target.mkdir(parents=True, exist_ok=False)
            ensure_hugo_stub(target, key, create_stub=args.stub)
            print(f"Created: {target}")

        created += 1

    print(f"Done. Keys: {len(keys)} | Created: {created} | Skipped: {skipped}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())