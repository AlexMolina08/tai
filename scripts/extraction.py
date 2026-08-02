"""Extracción literal de cuestionarios con texto embebido y escaneados OCR."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ocr_sources import cache_paths, layout_path, needs_ocr, psm4_high_path, psm4_path, psm6_high_path


@dataclass
class ExtractedQuestion:
    segment: int
    original_number: int
    prompt: str
    options: list[str]
    page: int
    extraction: str
    order: int = 0


def clean(value: str) -> str:
    value = value.replace("\u00ad", "").replace("\ufb01", "fi").replace("\ufb02", "fl")
    value = re.sub(r"\s+", " ", value).strip(" \n\t-–")
    return value


def document_text(path: Path) -> tuple[str, str]:
    if needs_ocr(path):
        _, sidecar = cache_paths(path)
        if not sidecar.exists():
            raise FileNotFoundError(f"Falta OCR: {sidecar}. Ejecuta scripts/ocr_sources.py")
        return sidecar.read_text(encoding="utf-8"), "ocr_spa_psm6"
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout, "embedded_text"


def page_at(text: str, position: int) -> int:
    return text.count("\f", 0, position) + 1


def strip_page_noise(value: str) -> str:
    lines = []
    for line in value.splitlines():
        folded = line.casefold()
        if re.search(r"\bpagina\s+\d+\s+de\s+\d+\s*$", folded.replace("á", "a")):
            continue
        if len(line) < 120 and re.match(r"^\s*(?:instituto nacional de|comision permanente)", folded.replace("ó", "o")):
            continue
        if re.match(r"^\s*\d+\s*[-–]\s*test\b", folded):
            continue
        lines.append(line)
    return clean("\n".join(lines).replace("\f", " "))


def embedded_questions(text: str) -> list[ExtractedQuestion]:
    starts = list(re.finditer(r"(?m)^\s*(\d{1,3})(?:\s*[\.)]\s+|\s{2,})(?=\S)", text))
    parsed: list[tuple[int, str, list[str], int, int]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = text[start.end():end]
        candidates = list(re.finditer(r"(?<![\w])([a-d])\s*[\.)]\s+", body, re.I))
        option_marks = []
        expected = "a"
        for candidate in candidates:
            if candidate.group(1).lower() == expected:
                option_marks.append(candidate)
                if len(option_marks) == 4:
                    break
                expected = chr(ord(expected) + 1)
        if len(option_marks) != 4:
            continue
        prompt = strip_page_noise(body[:option_marks[0].start()])
        options = []
        for option_index, mark in enumerate(option_marks):
            option_end = option_marks[option_index + 1].start() if option_index < 3 else len(body)
            raw = body[mark.end():option_end]
            if option_index == 3 and "\f" in raw:
                raw = raw.split("\f", 1)[0]
            options.append(strip_page_noise(raw))
        if prompt and all(options):
            parsed.append((int(start.group(1)), prompt, options, page_at(text, start.start()), start.start()))

    result: list[ExtractedQuestion] = []
    segment = 1
    previous = 0
    for number, prompt, options, page, position in parsed:
        # Algunos PDF con texto embebido convierten un numero (por ejemplo,
        # ``2``) en una cifra espuria como ``422``. Si el resto de la serie es
        # consecutivo, conservar el orden documental es mas fiable que ese
        # token aislado.
        if previous and number > previous + 10:
            number = previous + 1
        if previous and number <= previous and (number <= 5 or number < previous - 10):
            segment += 1
        result.append(ExtractedQuestion(segment, number, prompt, options, page, "embedded_text", position))
        previous = number
    return result


LINE_MARKER = re.compile(r"(?m)^\s*([^\s]{1,3})(?:\s*[\.)-])?\s+(?=\S)")
OPTION_MARKER = re.compile(
    r"(?<![\w])(((?:[a-dA-D][jJ]|[hH]b|b[hH]|[eE]c|[dD]d|[oO0]d|[cC][ceElL])\s*[\.)/:,]{0,3})|((?:[a-dA-DOo€£<¢eE]|\d{1,2})\s*[\.)/:,]{1,3}))\s+"
)


def marker_label(token: str) -> str:
    token = token.strip().rstrip(".),/;:").strip().casefold()
    if token in {"a", "b", "c", "d"}:
        return token
    if token in {"aj", "bj", "cj", "dj"}:
        return token[0]
    if token == "hb":
        return "b"
    if token == "bh":
        return "b"
    if token == "ec":
        return "c"
    if token == "dd":
        return "d"
    if token in {"e", "€", "£", "<", "¢", "ç", "ce", "cc", "cl"}:
        return "c"
    if token in {"od", "0d"}:
        return "d"
    if token in {"o", "0"}:
        # La forma redonda aparece indistintamente por c/d en escaneos. El
        # alineador de la secuencia a-b-c-d decide la posicion, no el glifo.
        return "?"
    return "?"


def marker_number(token: str) -> int | None:
    token = token.strip().rstrip(".),;:")
    return int(token) if token.isdigit() else None


def option_group(markers: list[re.Match[str]], start: int, end: int) -> tuple[int, list[re.Match[str]]]:
    candidates = [
        marker for marker in markers
        if start <= marker.start() < end
        # En respuestas como "a) B." la B es contenido, no el marcador b).
        and not (
            len(marker.group(1).strip().rstrip(".),/;:")) == 1
            and marker.group(1).strip().rstrip(".),/;:").isupper()
            and "." in marker.group(1)
            and ")" not in marker.group(1)
        )
    ]
    expected = "abcd"
    scores = [[-10_000] * 5 for _ in range(len(candidates) + 1)]
    paths: list[list[list[int]]] = [[[] for _ in range(5)] for _ in range(len(candidates) + 1)]
    scores[0][0] = 0
    for row, marker in enumerate(candidates, 1):
        scores[row] = scores[row - 1][:]
        paths[row] = [path[:] for path in paths[row - 1]]
        label = marker_label(marker.group(1))
        for slot in range(4):
            base = scores[row - 1][slot]
            if base <= -10_000:
                continue
            delta = 2 if label == expected[slot] else (0 if label == "?" else -2)
            value = base + delta
            if value > scores[row][slot + 1]:
                scores[row][slot + 1] = value
                paths[row][slot + 1] = paths[row - 1][slot] + [row - 1]
    indices = paths[-1][4]
    return scores[-1][4], [candidates[index] for index in indices]


def prompt_quality(text: str, node: re.Match[str], options: list[re.Match[str]]) -> int:
    if not options:
        return -100
    prompt = clean(text[node.end():options[0].start()])
    if not 12 <= len(prompt) <= 2_000:
        return -100
    letters = sum(character.isalpha() for character in prompt)
    visible = sum(not character.isspace() for character in prompt)
    ratio = letters / max(1, visible)
    folded = f" {prompt.casefold()} "
    common = sum(folded.count(token) for token in (" de ", " la ", " el ", " en ", " que ", " según ", " cuál ", " señale "))
    cues = ("¿", "indique", "señale", "cuál", "qué", " es:", " son:")
    if common == 0 and not any(cue in folded for cue in cues):
        return -100
    if marker_number(node.group(1)) is None and common < 2 and not any(cue in folded for cue in cues):
        return -100
    penalty = 60 if ratio < 0.58 else 0
    if " map map " in folded or "instrucciones" in folded:
        penalty += 80
    return min(20, common * 2 + int(ratio * 10)) - penalty


def ocr_question_nodes(text: str) -> tuple[list[re.Match[str]], list[re.Match[str]]]:
    content_start = text.find("\f") + 1 if "\f" in text else 0
    markers = [marker for marker in OPTION_MARKER.finditer(text) if marker.start() >= content_start]
    line_markers = [marker for marker in LINE_MARKER.finditer(text) if marker.start() >= content_start]
    nodes = [
        marker for marker in line_markers
        if not re.fullmatch(r"[a-dA-D]", marker.group(1).rstrip(".)"))
    ]
    count = len(nodes)
    best = [-10**9] * count
    previous: list[int | None] = [None] * count
    for current, node in enumerate(nodes):
        number = marker_number(node.group(1))
        best[current] = 20 if number == 1 else (5 if number is None else 0)
        for candidate in range(max(0, current - 40), current):
            if best[candidate] < 0:
                continue
            score, options = option_group(markers, nodes[candidate].end(), node.start())
            if score < 4:
                continue
            quality = prompt_quality(text, nodes[candidate], options)
            if quality < 4:
                continue
            left = marker_number(nodes[candidate].group(1))
            if left is not None and number == left + 1:
                continuity = 5
            elif left is not None and left >= 10 and number == 1:
                continuity = 2
            elif number is None:
                continuity = 0
            else:
                continuity = -5
            value = best[candidate] + 100 + continuity + quality
            if value > best[current]:
                best[current] = value
                previous[current] = candidate

    endings = []
    for index, node in enumerate(nodes):
        score, options = option_group(markers, node.end(), len(text))
        if score >= 4 and prompt_quality(text, node, options) >= 4 and best[index] > 0:
            endings.append(index)
    if not endings:
        return markers, []
    cursor = max(endings, key=lambda index: best[index] + 100)
    path = []
    while cursor is not None:
        path.append(cursor)
        cursor = previous[cursor]
    path.reverse()
    return markers, [nodes[index] for index in path]


def ocr_questions(text: str) -> list[ExtractedQuestion]:
    markers, nodes = ocr_question_nodes(text)
    result: list[ExtractedQuestion] = []
    segment = 1
    previous_number = 0
    inferred_number = 1
    for index, node in enumerate(nodes):
        end = nodes[index + 1].start() if index + 1 < len(nodes) else len(text)
        score, options = option_group(markers, node.end(), end)
        if score < 4 or len(options) != 4:
            continue
        raw_number = marker_number(node.group(1))
        number = raw_number if raw_number is not None else inferred_number
        if previous_number and number > previous_number + 10:
            number = previous_number + 1
        if previous_number and number <= previous_number and (number <= 5 or number < previous_number - 10):
            segment += 1
        prompt = strip_page_noise(text[node.end():options[0].start()])
        values = []
        for option_index, marker in enumerate(options):
            option_end = options[option_index + 1].start() if option_index < 3 else end
            raw = text[marker.end():option_end]
            if option_index == 3 and "\f" in raw:
                raw = raw.split("\f", 1)[0]
            values.append(strip_page_noise(raw))
        if prompt and all(values):
            result.append(ExtractedQuestion(segment, number, prompt, values, page_at(text, node.start()), "ocr_spa_psm6", node.start()))
        previous_number = number
        inferred_number = number + 1
    return result


def relaxed_ocr_questions(text: str, extraction: str) -> list[ExtractedQuestion]:
    """Lectura local por bloques para OCR con uno o dos marcadores danados.

    A diferencia del recorrido global, una pregunta deteriorada no elimina la
    cadena valida que viene despues. Solo se aceptan bloques con cuatro
    opciones no vacias y un numero visible en el margen.
    """
    starts = [
        match for match in re.finditer(r"(?m)^\s*(\d{1,3})\s*[\.),:]\s+(?=\S)", text)
        if int(match.group(1)) <= 200
    ]
    markers = list(OPTION_MARKER.finditer(text))
    parsed: list[tuple[int, str, list[str], int, int]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        score, options = option_group(markers, start.end(), end)
        if score < 2 or len(options) != 4:
            continue
        prompt = strip_page_noise(text[start.end():options[0].start()])
        values = []
        for option_index, marker in enumerate(options):
            option_end = options[option_index + 1].start() if option_index < 3 else end
            raw = text[marker.end():option_end]
            if option_index == 3 and "\f" in raw:
                raw = raw.split("\f", 1)[0]
            values.append(strip_page_noise(raw))
        if len(re.sub(r"\W+", "", prompt)) >= 4 and all(values):
            parsed.append((int(start.group(1)), prompt, values, page_at(text, start.start()), start.start()))

    result: list[ExtractedQuestion] = []
    segment = 1
    previous = 0
    for number, prompt, values, page, position in parsed:
        if previous and number > previous + 10:
            number = previous + 1
        if previous and number <= previous and (number <= 5 or number < previous - 10):
            segment += 1
        result.append(ExtractedQuestion(segment, number, prompt, values, page, extraction, position))
        previous = number
    return result


def extract_questions(path: Path) -> list[ExtractedQuestion]:
    text, mode = document_text(path)
    if mode == "ocr_spa_psm6" and layout_path(path).exists():
        layout = layout_questions(path)
        linear = ocr_questions(text)
        embedded_text = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True,
        ).stdout
        embedded = embedded_questions(embedded_text)
        fallback = embedded if len(embedded) >= 20 else linear
        merged = {(question.segment, question.original_number): question for question in fallback}
        # La versión con coordenadas tiene mejor separación entre enunciado y
        # opciones; la lectura lineal se conserva como red de seguridad para
        # marcadores deteriorados.
        merged.update({(question.segment, question.original_number): question for question in layout})
        return sorted(merged.values(), key=lambda question: (question.segment, question.original_number))
    return ocr_questions(text) if mode == "ocr_spa_psm6" else embedded_questions(text)


def extract_question_sources(path: Path) -> list[list[ExtractedQuestion]]:
    """Devuelve lecturas independientes para poder completar huecos sin mezclar su orden."""
    text, mode = document_text(path)
    if mode != "ocr_spa_psm6" or not layout_path(path).exists():
        return [embedded_questions(text), relaxed_ocr_questions(text, "embedded_text_relaxed")]
    embedded_text = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True,
    ).stdout
    embedded = embedded_questions(embedded_text)
    layout = layout_questions(path)
    linear = ocr_questions(text)
    psm6_relaxed = relaxed_ocr_questions(text, "ocr_spa_psm6_relaxed")
    psm4_text = psm4_path(path).read_text(encoding="utf-8") if psm4_path(path).exists() else ""
    psm4 = ocr_questions(psm4_text) if psm4_text else []
    psm4_relaxed = relaxed_ocr_questions(psm4_text, "ocr_spa_psm4_relaxed") if psm4_text else []
    high_text = psm4_high_path(path).read_text(encoding="utf-8") if psm4_high_path(path).exists() else ""
    high = ocr_questions(high_text) if high_text else []
    high_relaxed = relaxed_ocr_questions(high_text, "ocr_spa_psm4_400_relaxed") if high_text else []
    psm6_high_text = psm6_high_path(path).read_text(encoding="utf-8") if psm6_high_path(path).exists() else ""
    psm6_high = ocr_questions(psm6_high_text) if psm6_high_text else []
    psm6_high_relaxed = relaxed_ocr_questions(psm6_high_text, "ocr_spa_psm6_high_relaxed") if psm6_high_text else []
    sources = [layout, linear, psm6_relaxed, psm4, psm4_relaxed, high, high_relaxed, psm6_high, psm6_high_relaxed]
    return [embedded, *sources] if len(embedded) >= 20 else sources


def layout_questions(path: Path) -> list[ExtractedQuestion]:
    pages = json.loads(layout_path(path).read_text(encoding="utf-8"))
    words: list[dict] = []
    nodes: list[int] = []
    option_markers: list[int] = []
    line_starts: list[int] = []
    for page in pages:
        width = max(1, page["width"])
        height = max(1, page["height"])
        # En estos escaneos los números de pregunta terminan, como máximo,
        # alrededor del 6,8 % del ancho. Las letras de opción comienzan en el
        # 7,7 %. Mantener este hueco evita confundir una opción con una nueva
        # pregunta, especialmente en las páginas inferiores de 2005.
        question_limit = width * 0.072
        question_minimum = width * 0.03
        for line in page["lines"]:
            line_words = line["words"]
            if not line_words or line["top"] < height * 0.025 or line["top"] > height * 0.98:
                continue
            line_start = len(words)
            line_starts.append(line_start)
            for word in line_words:
                words.append({**word, "page": page["page"], "pageWidth": width, "pageHeight": height})
            first = line_words[0]
            # Bordes y marcas del escaneo aparecen a veces como un token
            # previo (``| 51.``). Buscar el número en toda la estrecha banda
            # izquierda recupera esas preguntas sin aceptar números del
            # enunciado o de las opciones.
            for offset, word in enumerate(line_words):
                if word["left"] >= question_limit:
                    break
                if word["left"] < question_minimum:
                    continue
                token = word["text"].strip().rstrip(".),;:")
                if re.fullmatch(r"\d{1,3}", token) and len(line["text"]) >= 7:
                    nodes.append(line_start + offset)
                    break
            # Una opción siempre comienza una línea. Restringir el marcador al
            # primer token permite aceptar OCR como ``d`` o ``a /`` sin tomar
            # letras sueltas del propio texto como nuevas opciones.
            for offset, word in enumerate(line_words):
                option_token = word["text"].strip()
                if word["left"] < question_limit:
                    continue
                suffix = r"[\.)/]?" if offset == 0 else r"[\.)/]"
                marked = re.fullmatch(
                    rf"(?:[a-dA-DOo]|ce|CE|Cc|CC|cl|CL|od|0d|OD|€|£|<|¢|e|E|ç|[1-4])\s*{suffix}",
                    option_token,
                )
                preceded_by_noise = offset > 0 and re.fullmatch(r"[a-dA-D]", option_token) and all(
                    not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{2,}", previous["text"])
                    for previous in line_words[:offset]
                )
                if marked or preceded_by_noise:
                    option_markers.append(line_start + offset)

    node_pages: dict[int, int] = {}
    for node in nodes:
        page_number = words[node]["page"]
        node_pages[page_number] = node_pages.get(page_number, 0) + 1
    first_content_page = next((page["page"] for page in pages if node_pages.get(page["page"], 0) >= 2), pages[0]["page"] if pages else 1)
    nodes = [node for node in nodes if words[node]["page"] >= first_content_page]
    option_markers = [marker for marker in option_markers if words[marker]["page"] >= first_content_page]

    def group(start: int, end: int) -> tuple[int, list[int]]:
        candidates = [index for index in option_markers if start <= index < end]
        scores = [[-10_000] * 5 for _ in range(len(candidates) + 1)]
        paths: list[list[list[int]]] = [[[] for _ in range(5)] for _ in range(len(candidates) + 1)]
        scores[0][0] = 0
        for row, word_index in enumerate(candidates, 1):
            scores[row] = scores[row - 1][:]
            paths[row] = [path[:] for path in paths[row - 1]]
            label = marker_label(words[word_index]["text"])
            for slot in range(4):
                base = scores[row - 1][slot]
                delta = 2 if label == "abcd"[slot] else (0 if label == "?" else -2)
                value = base + delta
                if value > scores[row][slot + 1]:
                    scores[row][slot + 1] = value
                    paths[row][slot + 1] = paths[row - 1][slot] + [row - 1]
        selected = paths[-1][4]
        return scores[-1][4], [candidates[index] for index in selected]

    def text_between(start: int, end: int) -> str:
        selected = []
        for word in words[start:end]:
            if word["top"] < word["pageHeight"] * 0.025 or word["top"] > word["pageHeight"] * 0.98:
                continue
            selected.append(word["text"])
        return clean(" ".join(selected))

    def consecutive_groups(start: int, end: int) -> list[list[int]]:
        candidates = [index for index in option_markers if start <= index < end]
        groups: list[list[int]] = []
        current: list[int] = []
        for candidate in candidates:
            label = marker_label(words[candidate]["text"])
            expected = "abcd"[len(current)]
            if label == expected or label == "?":
                current.append(candidate)
                if len(current) == 4:
                    groups.append(current)
                    current = []
            elif label == "a":
                current = [candidate]
        return groups

    def inferred_start(lower: int, option_a: int) -> int | None:
        candidates = [
            index for index in line_starts
            if lower < index < option_a
            and question_minimum <= words[index]["left"] < question_limit
        ]
        return candidates[-1] if candidates else None

    result: list[ExtractedQuestion] = []
    segment = 1
    previous_number = 0
    inferred_number = 1
    # Procesar cada inicio por separado es más estable que buscar una única
    # cadena global: si una opción al pie de página es ilegible, se descarta
    # solo esa pregunta y no la primera pregunta válida de la página siguiente.
    for node_index, node in enumerate(nodes):
        end = nodes[node_index + 1] if node_index + 1 < len(nodes) else len(words)
        score, options = group(node + 1, end)
        if score < 4 or len(options) != 4:
            continue
        raw_number = marker_number(words[node]["text"])
        number = raw_number if raw_number is not None else inferred_number
        if previous_number and number <= previous_number and (number <= 5 or number < previous_number - 10):
            segment += 1
        prompt = text_between(node + 1, options[0])
        values = []
        for option_index, marker in enumerate(options):
            option_end = options[option_index + 1] if option_index < 3 else end
            values.append(text_between(marker + 1, option_end))
        if prompt and all(values):
            result.append(ExtractedQuestion(
                segment=segment,
                original_number=number,
                prompt=prompt,
                options=values,
                page=words[node]["page"],
                extraction="ocr_spa_psm6_layout",
                order=node,
            ))
        previous_number = number
        inferred_number = number + 1

    # Recuperar inicios cuyo número quedó convertido por el OCR en un símbolo
    # (por ejemplo ``A`` en vez de ``7``). La secuencia adicional a/b/c/d y la
    # sangría de pregunta permiten reconstruirlos sin inventar contenido.
    recovered: list[ExtractedQuestion] = []
    previous_number = 0
    current_segment = 1
    for node_index, node in enumerate(nodes):
        number = marker_number(words[node]["text"])
        if number is None:
            continue
        if previous_number and number <= previous_number and (number <= 5 or number < previous_number - 10):
            current_segment += 1
        end = nodes[node_index + 1] if node_index + 1 < len(nodes) else len(words)
        next_number = marker_number(words[end]["text"]) if end < len(words) else None
        groups = consecutive_groups(node + 1, end)
        missing = (next_number - number - 1) if next_number is not None and next_number > number else 0
        for offset in range(min(missing, max(0, len(groups) - 1))):
            option_group_indices = groups[offset + 1]
            lower = groups[offset][-1]
            start = inferred_start(lower, option_group_indices[0])
            if start is None:
                continue
            option_end = end
            values = []
            for option_index, marker in enumerate(option_group_indices):
                value_end = option_group_indices[option_index + 1] if option_index < 3 else option_end
                values.append(text_between(marker + 1, value_end))
            prompt = text_between(start + 1, option_group_indices[0])
            if prompt and all(values):
                recovered.append(ExtractedQuestion(
                    current_segment,
                    number + offset + 1,
                    prompt,
                    values,
                    words[start]["page"],
                    "ocr_spa_psm6_layout_inferred_number",
                    start,
                ))
        previous_number = number

    first_number = marker_number(words[nodes[0]]["text"]) if nodes else None
    if first_number and first_number > 1:
        leading_groups = consecutive_groups(0, nodes[0])
        for number, option_group_indices in enumerate(leading_groups[-(first_number - 1):], 1):
            lower = -1 if number == 1 else leading_groups[-(first_number - 1):][number - 2][-1]
            start = inferred_start(lower, option_group_indices[0])
            if start is None:
                continue
            values = []
            for option_index, marker in enumerate(option_group_indices):
                value_end = option_group_indices[option_index + 1] if option_index < 3 else nodes[0]
                values.append(text_between(marker + 1, value_end))
            prompt = text_between(start + 1, option_group_indices[0])
            if prompt and all(values):
                recovered.append(ExtractedQuestion(
                    1, number, prompt, values, words[start]["page"],
                    "ocr_spa_psm6_layout_inferred_number", start,
                ))

    existing = {(question.segment, question.original_number) for question in result}
    result.extend(question for question in recovered if (question.segment, question.original_number) not in existing)
    result.sort(key=lambda question: (question.page, question.order))
    parsed_page_counts: dict[int, int] = {}
    for question in result:
        parsed_page_counts[question.page] = parsed_page_counts.get(question.page, 0) + 1
    parsed_start_page = next((page["page"] for page in pages if parsed_page_counts.get(page["page"], 0) >= 5), first_content_page)
    result = [question for question in result if question.page >= parsed_start_page]
    result = [
        question for question in result
        if not folded_noise(question.prompt).startswith(("test 20", "instrucciones", "marque las respuestas"))
    ]
    if result and result[0].original_number > 1:
        first = result[0]
        page_start = next((index for index in line_starts if words[index]["page"] == parsed_start_page), 0)
        leading = consecutive_groups(page_start, first.order)
        needed = first.original_number - 1
        for number, option_group_indices in enumerate(leading[-needed:], 1):
            lower = page_start - 1 if number == 1 else leading[-needed:][number - 2][-1]
            start = inferred_start(lower, option_group_indices[0])
            if start is None:
                continue
            values = []
            for option_index, marker in enumerate(option_group_indices):
                value_end = option_group_indices[option_index + 1] if option_index < 3 else first.order
                values.append(text_between(marker + 1, value_end))
            prompt = text_between(start + 1, option_group_indices[0])
            if prompt and all(values):
                result.append(ExtractedQuestion(1, number, prompt, values, words[start]["page"], "ocr_spa_psm6_layout_inferred_number", start))
        result.sort(key=lambda question: (question.page, question.order))
    first_one = next((index for index, question in enumerate(result) if question.original_number == 1), None)
    if first_one is not None and first_one <= 3:
        result = result[first_one:]
    segment = 1
    previous = 0
    for question in result:
        if previous and question.original_number > previous + 10:
            question.original_number = previous + 1
        if previous and question.original_number <= previous and (question.original_number <= 5 or question.original_number < previous - 10):
            segment += 1
        question.segment = segment
        previous = question.original_number
    return result


def folded_noise(value: str) -> str:
    import unicodedata
    return "".join(character for character in unicodedata.normalize("NFD", value.casefold()) if unicodedata.category(character) != "Mn")
