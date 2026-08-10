#!/usr/bin/env python3
"""Validación de integridad, cobertura y seguridad del banco generado."""

import json
import re
import sqlite3
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "src" / "data" / "bank.json"
COVERAGE = ROOT / "reports" / "coverage-matrix.json"
PAGE_REFERENCE_RE = re.compile(r"\bp[aá]gina\s+\d+\s+de\s+\d+\b", re.IGNORECASE)
INTERNAL_OPTION_MARKER_RE = re.compile(r"(?:^|\s)[a-d][.)]\s+", re.IGNORECASE)


def main() -> None:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    assert bank["meta"]["officialCall"] == "TAILI.pdf"
    assert bank["meta"]["schemaVersion"] == 2
    assert sum(len(block["topics"]) for block in bank["program"]) == 33
    assert [block["id"] for block in bank["program"]] == ["I", "II", "III", "IV"]
    assert bank["examConfig"] == {
        "durationMinutes": 120, "firstPartQuestions": 80, "firstPartReserve": 5,
        "practicalQuestions": 20, "practicalReserve": 5, "wrongPenalty": 1 / 3,
        "blankPenalty": 0, "officialMaximum": 100, "partMaximum": 50,
        "officialCutNote": "Cada parte exige 25/50 tras la transformación de la CPS; la puntuación directa mínima se publica por separado.",
    }
    assert len(bank["documents"]) == 49
    assert all(document["status"] not in {"reviewed_not_imported", "reviewed_ocr_required"} for document in bank["documents"])
    ids = [question["id"] for question in bank["questions"]]
    assert len(ids) == len(set(ids))
    document_pages = {document["path"]: document["pages"] for document in bank["documents"]}
    source_pages: dict[str, int] = {}
    for question in bank["questions"]:
        assert len(question["options"]) == 4
        assert all(option.strip() for option in question["options"])
        assert question["correctAnswer"] in {"a", "b", "c", "d", "anulada", None}
        assert question["topicId"].startswith(question["blockId"] + ".")
        assert question["topicId"] in {topic["id"] for block in bank["program"] for topic in block["topics"]}
        source = ROOT / question["source"]["pdf"]
        if str(source) not in source_pages:
            if source.exists():
                source_pages[str(source)] = len(PdfReader(str(source)).pages)
            else:
                assert question["source"]["pdf"] in document_pages
                source_pages[str(source)] = document_pages[question["source"]["pdf"]]
        assert 1 <= question["source"]["page"] <= source_pages[str(source)]
        if question["active"]:
            assert question["status"] == "valid"
            assert question["correctAnswer"] in {"a", "b", "c", "d"}
            assert question["classificationConfidence"] >= 0.68
            assert not PAGE_REFERENCE_RE.search(question["prompt"] + " " + " ".join(question["options"]))
            assert not any(INTERNAL_OPTION_MARKER_RE.search(option) for option in question["options"])
            assert len(question["prompt"]) <= 2400
            assert all(len(option) <= 1200 for option in question["options"])
    assert sum(row["extracted"] for row in coverage) == len(bank["questions"])
    assert all(row["extracted"] == row["expected"] and not row["missing"] for row in coverage)
    with sqlite3.connect(ROOT / "src" / "data" / "bank.sqlite") as database:
        assert database.execute("SELECT COUNT(*) FROM questions").fetchone()[0] == len(bank["questions"])
        assert database.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    print(f"Validación correcta: {len(ids)} preguntas, {sum(q['active'] for q in bank['questions'])} vigentes y {len(bank['documents'])} documentos")


if __name__ == "__main__":
    main()
