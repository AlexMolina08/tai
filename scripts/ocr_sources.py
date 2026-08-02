#!/usr/bin/env python3
"""Crea copias OCR temporales de los PDF escaneados sin tocar las fuentes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "TAI AGE"
CACHE = ROOT / "tmp" / "ocr"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_characters(path: Path) -> int:
    return sum(len(page.extract_text() or "") for page in PdfReader(str(path)).pages)


def needs_ocr(path: Path) -> bool:
    pages = len(PdfReader(str(path)).pages)
    relative = str(path.relative_to(SOURCE)).casefold()
    year = next((value for value in range(2005, 2019) if str(value) in relative), None)
    name = path.name.casefold()
    complex_historical_questionnaire = bool(
        year
        and ("respuesta" not in name or "cuestionario y respuestas" in name)
        and "plant" not in name
        and (
            "cuestionario" in name
            or name in {"tai libre 2018.pdf", "tai libre 2018_segundo ejercicio.pdf", "tai pi 2018.pdf"}
        )
    )
    return pages > 2 and (text_characters(path) < 5_000 or complex_historical_questionnaire)


def cache_paths(path: Path) -> tuple[Path, Path]:
    key = sha256(path)[:16]
    stem = "-".join(path.relative_to(SOURCE).parts).replace(".pdf", "")
    base = CACHE / f"{stem}-{key}"
    return base.with_suffix(".pdf"), Path(str(base) + ".psm6.txt")


def page_ocr(path: Path, page: int, key: str) -> tuple[int, str, str, dict]:
    image_path = CACHE / f".{key}-page-{page}.png"
    relative = str(path.relative_to(SOURCE))
    use_200 = (
        "2005-LI-PRIMER EJERCICIO" in path.name
        or any(year in relative for year in ("2015", "2016", "2017"))
        or ("2018" in relative and path.name != "TAI LIBRE 2018.pdf")
    )
    dpi = "200" if use_200 else "300"
    subprocess.run(
        [
            "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
            "-gray", "-r", dpi, "-png", str(path), str(image_path.with_suffix("")),
        ],
        check=True,
        capture_output=True,
    )
    try:
        result = subprocess.run(
            [
                "tesseract", str(image_path), "stdout", "-l", "spa", "--psm", "6", "tsv",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        rows = list(csv.DictReader(io.StringIO(result.stdout), delimiter="\t"))
        psm4 = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "spa", "--psm", "4"],
            check=True, capture_output=True, text=True,
        ).stdout
        page_row = next((row for row in rows if row.get("level") == "1"), {})
        grouped: dict[tuple[str, str, str], list[dict]] = {}
        for row in rows:
            text = (row.get("text") or "").strip()
            if row.get("level") != "5" or not text:
                continue
            key_line = (row["block_num"], row["par_num"], row["line_num"])
            grouped.setdefault(key_line, []).append({
                "text": text,
                "left": int(row["left"]),
                "top": int(row["top"]),
                "width": int(row["width"]),
                "height": int(row["height"]),
                "confidence": float(row["conf"]),
            })
        lines = []
        for words in grouped.values():
            words.sort(key=lambda word: word["left"])
            lines.append({
                "text": " ".join(word["text"] for word in words),
                "left": min(word["left"] for word in words),
                "top": min(word["top"] for word in words),
                "words": words,
            })
        lines.sort(key=lambda line: (line["top"], line["left"]))
        text = "\n".join(line["text"] for line in lines)
        layout = {
            "page": page,
            "width": int(page_row.get("width") or 0),
            "height": int(page_row.get("height") or 0),
            "lines": lines,
        }
        return page, text, psm4, layout
    finally:
        image_path.unlink(missing_ok=True)


def layout_path(path: Path) -> Path:
    _, sidecar = cache_paths(path)
    return Path(str(sidecar).replace(".psm6.txt", ".layout.json"))


def psm4_path(path: Path) -> Path:
    _, sidecar = cache_paths(path)
    return Path(str(sidecar).replace(".psm6.txt", ".psm4.txt"))


def psm4_high_path(path: Path) -> Path:
    _, sidecar = cache_paths(path)
    return Path(str(sidecar).replace(".psm6.txt", ".psm4-400.txt"))


def psm6_high_path(path: Path) -> Path:
    _, sidecar = cache_paths(path)
    return Path(str(sidecar).replace(".psm6.txt", ".psm6-high.txt"))


def needs_high_accuracy(path: Path) -> bool:
    relative = str(path.relative_to(SOURCE)).casefold()
    return not any(token in relative for token in ("2007 libre", "2008 pi", "2014 pi"))


def page_psm4(path: Path, page: int, key: str, dpi: int | None = None) -> tuple[int, str]:
    image_path = CACHE / f".{key}-psm4-{dpi or 'base'}-page-{page}.png"
    relative = str(path.relative_to(SOURCE))
    use_200 = (
        "2005-LI-PRIMER EJERCICIO" in path.name
        or any(year in relative for year in ("2015", "2016", "2017"))
        or ("2018" in relative and path.name != "TAI LIBRE 2018.pdf")
    )
    subprocess.run([
        "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-gray",
        "-r", str(dpi or (200 if use_200 else 300)), "-png", str(path), str(image_path.with_suffix("")),
    ], check=True, capture_output=True)
    try:
        text = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "spa", "--psm", "4"],
            check=True, capture_output=True, text=True,
        ).stdout
        return page, text
    finally:
        image_path.unlink(missing_ok=True)


def page_psm6_high(path: Path, page: int, key: str, dpi: int) -> tuple[int, str]:
    image_path = CACHE / f".{key}-psm6-high-page-{page}.png"
    subprocess.run([
        "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-gray",
        "-r", str(dpi), "-png", str(path), str(image_path.with_suffix("")),
    ], check=True, capture_output=True)
    try:
        text = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "spa", "--psm", "6"],
            check=True, capture_output=True, text=True,
        ).stdout
        return page, text
    finally:
        image_path.unlink(missing_ok=True)


def write_psm4_sidecar(path: Path, *, high: bool = False) -> None:
    pages = len(PdfReader(str(path)).pages)
    key = sha256(path)[:16]
    relative = str(path.relative_to(SOURCE))
    high_dpi = 300 if any(year in relative for year in ("2015", "2016", "2017", "2018")) else 400
    with ThreadPoolExecutor(max_workers=4) as pool:
        extracted = list(pool.map(lambda page: page_psm4(path, page, key, high_dpi if high else None), range(1, pages + 1)))
    extracted.sort()
    target = psm4_high_path(path) if high else psm4_path(path)
    target.write_text("\n\f\n".join(text for _, text in extracted) + "\n", encoding="utf-8")


def write_psm6_high_sidecar(path: Path) -> None:
    pages = len(PdfReader(str(path)).pages)
    key = sha256(path)[:16]
    relative = str(path.relative_to(SOURCE))
    dpi = 300 if any(year in relative for year in ("2015", "2016", "2017", "2018")) else 400
    with ThreadPoolExecutor(max_workers=8) as pool:
        extracted = list(pool.map(lambda page: page_psm6_high(path, page, key, dpi), range(1, pages + 1)))
    extracted.sort()
    psm6_high_path(path).write_text("\n\f\n".join(text for _, text in extracted) + "\n", encoding="utf-8")


def write_psm6_sidecar(path: Path, sidecar: Path) -> None:
    pages = len(PdfReader(str(path)).pages)
    key = sha256(path)[:16]
    with ThreadPoolExecutor(max_workers=4) as pool:
        extracted = list(pool.map(lambda page: page_ocr(path, page, key), range(1, pages + 1)))
    extracted.sort()
    sidecar.write_text("\n\f\n".join(text for _, text, _, _ in extracted) + "\n", encoding="utf-8")
    psm4_path(path).write_text("\n\f\n".join(text for _, _, text, _ in extracted) + "\n", encoding="utf-8")
    layout_path(path).write_text(
        json.dumps([layout for _, _, _, layout in extracted], ensure_ascii=False),
        encoding="utf-8",
    )


def ensure_ocr(path: Path, force: bool = False) -> tuple[Path, Path]:
    output_pdf, sidecar = cache_paths(path)
    high_ready = (psm4_high_path(path).exists() and psm6_high_path(path).exists()) or not needs_high_accuracy(path)
    if output_pdf.exists() and sidecar.exists() and layout_path(path).exists() and psm4_path(path).exists() and high_ready and not force:
        return output_pdf, sidecar
    if output_pdf.exists() and sidecar.exists() and layout_path(path).exists() and psm4_path(path).exists() and needs_high_accuracy(path) and not psm4_high_path(path).exists() and not force:
        write_psm4_sidecar(path, high=True)
        write_psm6_high_sidecar(path)
        return output_pdf, sidecar
    if output_pdf.exists() and sidecar.exists() and layout_path(path).exists() and psm4_path(path).exists() and needs_high_accuracy(path) and psm4_high_path(path).exists() and not psm6_high_path(path).exists() and not force:
        write_psm6_high_sidecar(path)
        return output_pdf, sidecar
    if output_pdf.exists() and sidecar.exists() and layout_path(path).exists() and not psm4_path(path).exists() and not force:
        write_psm4_sidecar(path)
        return output_pdf, sidecar
    CACHE.mkdir(parents=True, exist_ok=True)
    sidecar.unlink(missing_ok=True)
    if force:
        output_pdf.unlink(missing_ok=True)
    if not output_pdf.exists():
        subprocess.run(
            [
                str(ROOT / ".venv" / "bin" / "ocrmypdf"),
                "--force-ocr", "--deskew", "--rotate-pages", "--language", "spa",
                "--jobs", "4", "--output-type", "pdf", str(path), str(output_pdf),
            ],
            check=True,
        )
    write_psm6_sidecar(path, sidecar)
    if needs_high_accuracy(path):
        write_psm4_sidecar(path, high=True)
        write_psm6_high_sidecar(path)
    return output_pdf, sidecar


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    candidates = [path for path in sorted(SOURCE.rglob("*.pdf")) if needs_ocr(path)]
    print(f"OCR necesario: {len(candidates)} PDF")
    for index, path in enumerate(candidates, 1):
        output_pdf, _ = ensure_ocr(path, args.force)
        pages = len(PdfReader(str(path)).pages)
        print(f"[{index}/{len(candidates)}] {path.relative_to(ROOT)} -> {output_pdf.name} ({pages} páginas)")


if __name__ == "__main__":
    main()
