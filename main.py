#!/usr/bin/env python3
"""
main.py
-------
CLI for Role 3's OCR & Extraction module.

Usage:
    # single label image
    python main.py --image sample_data/label1.jpg --out result.json

    # bulk folder of listing images
    python main.py --folder sample_data/ --out results.json

    # no PaddleOCR installed yet? develop against the mock engine:
    python main.py --image sample_data/label1.jpg --mock --out result.json
"""

import argparse
import json
import sys
from pathlib import Path

# If not running in the project's virtual environment, automatically switch to it if available
_venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
if _venv_python.exists() and Path(sys.executable).resolve() != _venv_python.resolve():
    import subprocess
    sys.exit(subprocess.call([str(_venv_python), str(Path(__file__).resolve())] + sys.argv[1:]))

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from pipeline import process_batch, process_label_image  # noqa: E402
except ModuleNotFoundError as e:
    if "pydantic" in str(e):
        print(
            "Error: 'pydantic' is not installed in the current Python environment.\n"
            "Please activate the virtual environment:\n"
            "    .\\venv\\Scripts\\activate\n"
            "or install dependencies:\n"
            "    pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)
    raise


def main():
    parser = argparse.ArgumentParser(description="MetroScan AI - OCR & Field Extraction (Role 3)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Path to a single label image")
    group.add_argument("--folder", help="Path to a folder of images (bulk mode)")
    parser.add_argument("--lang", default="en", help="OCR language code (default: en)")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use the mock OCR engine instead of PaddleOCR (useful before PaddleOCR is installed)",
    )
    parser.add_argument("--out", default="result.json", help="Output JSON file path")
    args = parser.parse_args()

    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Image not found: {image_path}", file=sys.stderr)
            sys.exit(1)
        result = process_label_image(str(image_path), lang=args.lang, force_mock=args.mock)
        output = result.model_dump()
    else:
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"Directory not found: {folder}", file=sys.stderr)
            sys.exit(1)
        image_paths = [
            str(p) for p in sorted(folder.iterdir())
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
        ]
        if not image_paths:
            print(f"No images found in {folder}", file=sys.stderr)
            sys.exit(1)
        results = process_batch(image_paths, lang=args.lang, force_mock=args.mock)
        output = [r.model_dump() for r in results]

    Path(args.out).write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"Wrote extraction result to {args.out}")


if __name__ == "__main__":
    main()
