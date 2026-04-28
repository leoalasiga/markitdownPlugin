#!/usr/bin/env python3
"""
extract_md_images.py

Pull inline base64 images out of a Markdown file and replace the references
with relative paths to locally-saved image files.

Typical use: markitdown emits a single huge ``.md`` with
``data:image/png;base64,...`` payloads; this script makes the file usable
again in normal viewers.

Usage:
    python extract_md_images.py INPUT.md [INPUT2.md ...] [OPTIONS]

Common flags:
    -o DIR, --output DIR     output directory (single-input only)
    --image-subdir NAME      images subfolder name (default: images)
    --in-place               rewrite the input file; images go next to it
    --hash-names             content-addressed filenames for idempotent reruns
    --dry-run                scan and report, write nothing
    -v, --verbose            per-image log
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

IMG_RE = re.compile(
    r"!\[([^\]]*)\]\(data:image/([a-zA-Z0-9+\-.]+);base64,([A-Za-z0-9+/=\s]+?)\)",
    re.DOTALL,
)

MIME_EXT = {
    "png": ".png",
    "jpeg": ".jpg",
    "jpg": ".jpg",
    "gif": ".gif",
    "webp": ".webp",
    "svg+xml": ".svg",
    "bmp": ".bmp",
    "x-icon": ".ico",
    "tiff": ".tiff",
}


@dataclass
class Stats:
    matched: int = 0
    unique: int = 0
    duplicated: int = 0
    failed: int = 0
    by_mime: Counter = field(default_factory=Counter)

    def merge(self, other: "Stats") -> None:
        self.matched += other.matched
        self.unique += other.unique
        self.duplicated += other.duplicated
        self.failed += other.failed
        self.by_mime.update(other.by_mime)


# ---------- IO helpers ----------

def read_markdown(path: Path) -> str:
    """Read md, sniffing common BOMs. Returns str with BOM stripped."""
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8")
    for enc in ("utf-8", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", raw, 0, len(raw), f"cannot decode: {path}")


def write_markdown(path: Path, content: str) -> None:
    """Write as UTF-8 without BOM; preserve original newline sequences."""
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(content)


def mime_to_ext(mime_subtype: str) -> str:
    ext = MIME_EXT.get(mime_subtype.lower())
    if ext is None:
        print(f"[warn] unknown image mime: image/{mime_subtype} -> .bin", file=sys.stderr)
        return ".bin"
    return ext


# ---------- core ----------

def _decode(b64_raw: str) -> bytes | None:
    try:
        return base64.b64decode(re.sub(r"\s+", "", b64_raw), validate=False)
    except (ValueError, binascii.Error):
        return None


def _make_name(
    *,
    mime_subtype: str,
    data: bytes,
    index: int,
    hash_names: bool,
) -> str:
    ext = mime_to_ext(mime_subtype)
    if hash_names:
        digest8 = hashlib.sha256(data).hexdigest()[:8]
        return f"image_{digest8}{ext}"
    return f"image_{index:03d}{ext}"


def process_markdown(
    content: str,
    images_dir: Path,
    image_subdir_name: str,
    *,
    hash_names: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[str, Stats]:
    stats = Stats()
    hash_to_name: dict[str, str] = {}
    saved = 0

    def replace(match: re.Match) -> str:
        nonlocal saved
        stats.matched += 1
        idx = stats.matched
        alt = match.group(1)
        mime_subtype = match.group(2)
        data = _decode(match.group(3))

        if data is None:
            stats.failed += 1
            print(f"[warn] img #{idx}: base64 decode failed, keeping data URI", file=sys.stderr)
            return match.group(0)

        digest = hashlib.sha256(data).hexdigest()
        stats.by_mime[mime_subtype.lower()] += 1

        if (existing := hash_to_name.get(digest)) is not None:
            stats.duplicated += 1
            filename = existing
            if verbose:
                print(f"  [{idx:>3}] dup  -> {filename}")
        else:
            saved += 1
            filename = _make_name(
                mime_subtype=mime_subtype, data=data, index=saved, hash_names=hash_names
            )
            hash_to_name[digest] = filename
            stats.unique += 1
            if not dry_run:
                (images_dir / filename).write_bytes(data)
            if verbose:
                tag = "save" if not dry_run else "plan"
                print(f"  [{idx:>3}] {tag} -> {filename} ({len(data)/1024:.1f} KB)")

        return f"![{alt}]({image_subdir_name}/{filename})"

    return IMG_RE.sub(replace, content), stats


# ---------- driver ----------

@dataclass
class JobPaths:
    input_md: Path
    output_md: Path
    images_dir: Path
    image_subdir_name: str


def plan_paths(
    input_path: Path,
    output_dir: Path | None,
    image_subdir_name: str,
    in_place: bool,
) -> JobPaths:
    if in_place:
        parent = input_path.parent
        return JobPaths(
            input_md=input_path,
            output_md=input_path,
            images_dir=parent / image_subdir_name,
            image_subdir_name=image_subdir_name,
        )
    out_dir = output_dir or (input_path.parent / input_path.stem)
    return JobPaths(
        input_md=input_path,
        output_md=out_dir / input_path.name,
        images_dir=out_dir / image_subdir_name,
        image_subdir_name=image_subdir_name,
    )


def run_job(paths: JobPaths, *, hash_names: bool, dry_run: bool, verbose: bool) -> Stats:
    print(f"[info] read   : {paths.input_md}")
    content = read_markdown(paths.input_md)
    print(f"[info] chars  : {len(content):,}")

    if not dry_run:
        paths.output_md.parent.mkdir(parents=True, exist_ok=True)
        paths.images_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] images : {paths.images_dir}{' (dry-run)' if dry_run else ''}")
    new_content, stats = process_markdown(
        content,
        paths.images_dir,
        paths.image_subdir_name,
        hash_names=hash_names,
        dry_run=dry_run,
        verbose=verbose,
    )

    if not dry_run:
        write_markdown(paths.output_md, new_content)
        print(f"[info] wrote  : {paths.output_md}")
    return stats


def print_summary(stats: Stats, *, title: str = "Summary") -> None:
    print()
    print(f"=== {title} ===")
    print(f"matched total  : {stats.matched}")
    print(f"  unique saved : {stats.unique}")
    print(f"  duplicated   : {stats.duplicated}")
    print(f"  decode fail  : {stats.failed}")
    if stats.by_mime:
        parts = ", ".join(f"{m}={n}" for m, n in stats.by_mime.most_common())
        print(f"by mime        : {parts}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract inline base64 images from markdown files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("inputs", nargs="+", help="markdown file path(s)")
    p.add_argument("-o", "--output", help="output directory (single-input only)")
    p.add_argument("--image-subdir", default="images", help="images subfolder name")
    p.add_argument("--in-place", action="store_true",
                   help="rewrite input file(s); images go next to them")
    p.add_argument("--hash-names", action="store_true",
                   help="content-addressed filenames (idempotent reruns)")
    p.add_argument("--dry-run", action="store_true",
                   help="scan and report, do not write files")
    p.add_argument("-v", "--verbose", action="store_true", help="per-image log")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    inputs = [Path(p).resolve() for p in args.inputs]
    missing = [p for p in inputs if not p.is_file()]
    if missing:
        for p in missing:
            print(f"[error] not a file: {p}", file=sys.stderr)
        return 2

    if args.output and (len(inputs) > 1 or args.in_place):
        print("[error] -o/--output conflicts with multiple inputs or --in-place",
              file=sys.stderr)
        return 2

    output_dir = Path(args.output).resolve() if args.output else None

    overall = Stats()
    for input_path in inputs:
        paths = plan_paths(input_path, output_dir, args.image_subdir, args.in_place)
        stats = run_job(
            paths,
            hash_names=args.hash_names,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        print_summary(stats, title=f"Done: {input_path.name}")
        overall.merge(stats)

    if len(inputs) > 1:
        print_summary(overall, title="Total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
