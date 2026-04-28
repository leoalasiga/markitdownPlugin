from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ConversionResult:
    source_path: Path
    output_path: Path | None
    success: bool
    message: str


@dataclass(slots=True)
class ConversionTask:
    source_path: Path
    output_dir: Path | None = None
