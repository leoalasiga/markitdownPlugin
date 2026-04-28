from __future__ import annotations

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
                images_dir.mkdir(parents=True, exist_ok=True)
                (images_dir / filename).write_bytes(data)
            if verbose:
                tag = "save" if not dry_run else "plan"
                print(f"  [{idx:>3}] {tag} -> {filename} ({len(data)/1024:.1f} KB)")

        return f"![{alt}]({image_subdir_name}/{filename})"

    return IMG_RE.sub(replace, content), stats


def extract_inline_images_for_markdown(
    content: str,
    output_markdown_path: str | Path,
    *,
    image_subdir_name: str = "images",
) -> str:
    output_path = Path(output_markdown_path)
    images_dir = output_path.parent / image_subdir_name
    processed, _ = process_markdown(content, images_dir, image_subdir_name)
    return processed
