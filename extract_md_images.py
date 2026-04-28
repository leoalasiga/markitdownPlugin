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
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from src.markdown_images import Stats, process_markdown, read_markdown, write_markdown


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
    p.add_argument(
        "--in-place",
        action="store_true",
        help="rewrite input file(s); images go next to them",
    )
    p.add_argument(
        "--hash-names",
        action="store_true",
        help="content-addressed filenames (idempotent reruns)",
    )
    p.add_argument("--dry-run", action="store_true", help="scan and report, do not write files")
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
        print("[error] -o/--output conflicts with multiple inputs or --in-place", file=sys.stderr)
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
