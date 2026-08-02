"""Lectura trazable de plantillas oficiales, respetando el flujo de columnas."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pdfplumber

from ocr_sources import layout_path


ANSWER = r"(?:[A-Da-d]|ANULADA|Anulada|anulada)"


def normalize_answer(value: str) -> str:
    value = value.casefold()
    return "anulada" if value == "anulada" else value


def _cluster_x(pairs: list[tuple[float, float, int, str]]) -> list[list[tuple[float, float, int, str]]]:
    clusters: list[list[tuple[float, float, int, str]]] = []
    for pair in sorted(pairs, key=lambda item: item[0]):
        cluster = next((group for group in clusters if abs(group[0][0] - pair[0]) <= 18), None)
        if cluster is None:
            clusters.append([pair])
        else:
            cluster.append(pair)
    clusters.sort(key=lambda group: min(item[0] for item in group))
    for cluster in clusters:
        cluster.sort(key=lambda item: item[1])
    return clusters


def _pdf_pairs(page) -> list[tuple[float, float, int, str]]:
    words = page.extract_words()
    pairs: list[tuple[float, float, int, str]] = []
    for index, word in enumerate(words):
        token = word["text"].strip()
        combined = re.fullmatch(rf"(\d{{1,3}})[\.)]\s*({ANSWER})", token)
        if combined:
            pairs.append((word["x0"], word["top"], int(combined.group(1)), normalize_answer(combined.group(2))))
            continue
        number = re.fullmatch(r"(\d{1,3})[\.)]", token)
        if not number or index + 1 >= len(words):
            continue
        answer_word = words[index + 1]
        if abs(answer_word["top"] - word["top"]) > 3 or not re.fullmatch(ANSWER, answer_word["text"]):
            continue
        pairs.append((word["x0"], word["top"], int(number.group(1)), normalize_answer(answer_word["text"])))
    return pairs


def _ocr_pairs(path: Path, page_number: int) -> list[tuple[float, float, int, str]]:
    if not layout_path(path).exists():
        return []
    import json

    pages = json.loads(layout_path(path).read_text(encoding="utf-8"))
    page = pages[page_number - 1]
    pairs: list[tuple[float, float, int, str]] = []
    for line in page["lines"]:
        words = line["words"]
        for index, word in enumerate(words):
            token = word["text"].strip()
            combined = re.fullmatch(rf"(\d{{1,3}})[\.)]\s*({ANSWER})", token)
            if combined:
                pairs.append((word["left"], word["top"], int(combined.group(1)), normalize_answer(combined.group(2))))
                continue
            number = re.fullmatch(r"(\d{1,3})[\.)]", token)
            if not number or index + 1 >= len(words):
                continue
            answer_word = words[index + 1]
            if not re.fullmatch(ANSWER, answer_word["text"]):
                continue
            pairs.append((word["left"], word["top"], int(number.group(1)), normalize_answer(answer_word["text"])))
    return pairs


def answer_stream(path: Path, page_number: int) -> list[tuple[int, str]]:
    """Devuelve las respuestas en el orden editorial de columnas de la plantilla."""
    with pdfplumber.open(path) as pdf:
        resolved_page = len(pdf.pages) if page_number == -1 else page_number
        page = pdf.pages[resolved_page - 1]
        pairs = _pdf_pairs(page)
    if len(pairs) < 5:
        pairs = _ocr_pairs(path, resolved_page)
    stream: list[tuple[int, str]] = []
    for cluster in _cluster_x(pairs):
        stream.extend((number, answer) for _, _, number, answer in cluster)
    return stream


def split_answers(stream: list[tuple[int, str]], lengths: list[int]) -> list[list[str]]:
    expected = sum(lengths)
    if len(stream) != expected:
        raise ValueError(f"La plantilla contiene {len(stream)} respuestas; se esperaban {expected}")
    result: list[list[str]] = []
    cursor = 0
    for length in lengths:
        values = stream[cursor:cursor + length]
        expected_numbers = list(range(1, length + 1))
        numbers = [number for number, _ in values]
        if numbers != expected_numbers:
            raise ValueError(f"Numeración inesperada en plantilla: {numbers[:5]}…{numbers[-5:]} frente a 1…{length}")
        result.append([answer for _, answer in values])
        cursor += length
    return result
