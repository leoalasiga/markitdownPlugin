from __future__ import annotations

import base64
import binascii
import hashlib
import html
from html.parser import HTMLParser
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


IMAGE_PLACEHOLDER_PREFIX = r"[\ufffc\ufffd]*"

MD_IMG_RE = re.compile(
    IMAGE_PLACEHOLDER_PREFIX
    + r"!\[([^\]]*)\]\(\s*<?data:image/([a-zA-Z0-9+\-.]+);base64,"
    r"([A-Za-z0-9+/=\s]+?)>?(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]+\)))?\s*\)",
    re.DOTALL,
)
HTML_IMG_RE = re.compile(
    IMAGE_PLACEHOLDER_PREFIX + r"<img\b(?P<attrs>[^>]*)>",
    re.IGNORECASE | re.DOTALL,
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


class _ImgAttrParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            self.attrs = {key.lower(): value or "" for key, value in attrs}


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

    def save_image(alt: str, mime_subtype: str, b64_raw: str, original: str) -> str:
        nonlocal saved
        stats.matched += 1
        idx = stats.matched
        data = _decode(b64_raw)

        if data is None:
            stats.failed += 1
            print(f"[warn] img #{idx}: base64 decode failed, keeping data URI", file=sys.stderr)
            return original

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

    def replace_markdown_image(match: re.Match) -> str:
        return save_image(
            alt=match.group(1),
            mime_subtype=match.group(2),
            b64_raw=match.group(3),
            original=match.group(0),
        )

    def replace_html_image(match: re.Match) -> str:
        parser = _ImgAttrParser()
        parser.feed(match.group(0))
        src = parser.attrs.get("src", "")
        src_match = re.fullmatch(
            r"\s*data:image/([a-zA-Z0-9+\-.]+);base64,([A-Za-z0-9+/=\s]+)\s*",
            src,
            re.DOTALL,
        )
        if src_match is None:
            return match.group(0)
        return save_image(
            alt=html.escape(parser.attrs.get("alt", ""), quote=False),
            mime_subtype=src_match.group(1),
            b64_raw=src_match.group(2),
            original=match.group(0),
        )

    content = MD_IMG_RE.sub(replace_markdown_image, content)
    content = HTML_IMG_RE.sub(replace_html_image, content)
    return content, stats


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
