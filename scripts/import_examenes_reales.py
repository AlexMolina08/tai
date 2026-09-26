#!/usr/bin/env python3
"""Importa los 5 exámenes reales desde EXAMENES REALES al banco del preparador.

Este script:
  1. Parsea los 5 ficheros TXT con formato estandarizado.
  2. Clasifica cada pregunta en uno de los 33 temas del programa.
  3. Valida la integridad: 4 opciones no vacías, respuesta coherente.
  4. Genera src/data/bank.json con todas las preguntas verificadas.
  5. Produce un informe detallado de importación.

No ejecuta build_bank.py ni toca las fuentes de TAI AGE.
No modifica los PDF originales.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

# ─── Rutas ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]
EXAMENES_DIR = Path.home() / "Desktop" / "TAI — Temas y tests" / "EXAMENES REALES"
DATA = ROOT / "src" / "data"
REPORTS = ROOT / "reports"

# ─── Programa oficial ────────────────────────────────────────────────────────

PROGRAM = json.loads((DATA / "program.json").read_text(encoding="utf-8"))

ALL_TOPICS = {
    topic["id"]: topic["name"]
    for block in PROGRAM
    for topic in block["topics"]
}

# ─── Manifiesto de exámenes ──────────────────────────────────────────────────

EXAM_MANIFEST = [
    {
        "folder": "2019 - Ordinario",
        "id": "2019-libre-ordinario",
        "name": "TAI Libre 2019 · Ordinario",
        "year": 2019,
        "access": "libre",
        "sitting": "ordinario",
        "answerStatus": "oficial_definitiva",
    },
    {
        "folder": "2023 - Ordinario",
        "id": "2023-libre-ordinario",
        "name": "TAI Libre 2023 · Ordinario",
        "year": 2023,
        "access": "libre",
        "sitting": "ordinario",
        "answerStatus": "oficial_provisional",
    },
    {
        "folder": "2024 - Ordinario",
        "id": "2024-libre-ordinario",
        "name": "TAI Libre 2024 · Ordinario",
        "year": 2024,
        "access": "libre",
        "sitting": "ordinario",
        "answerStatus": "oficial_provisional",
    },
    {
        "folder": "2025 - Extraordinario",
        "id": "2025-libre-extraordinario",
        "name": "TAI Libre 2025 · Extraordinario",
        "year": 2025,
        "access": "libre",
        "sitting": "extraordinario",
        "answerStatus": "oficial_provisional",
    },
    {
        "folder": "2025 - Modelo A",
        "id": "2025-libre-modelo-a",
        "name": "TAI Libre 2025 · Modelo A",
        "year": 2025,
        "access": "libre",
        "sitting": "modelo_a",
        "answerStatus": "oficial_provisional",
    },
]

# ─── Secciones esperadas en cada examen ──────────────────────────────────────

SECTION_SPECS = [
    {
        "header_pattern": r"PRIMERA PARTE\s*[—–-]\s*Preguntas\s+1\s+a\s+80",
        "key": "first",
        "exercise": "primera_parte",
        "reserve": False,
        "count": 80,
        "blocks": ["I", "II", "III", "IV"],
    },
    {
        "header_pattern": r"PRIMERA PARTE\s*[—–-]\s*Preguntas\s+de\s+reserva",
        "key": "first_reserve",
        "exercise": "primera_parte",
        "reserve": True,
        "count": 5,
        "blocks": ["I", "II", "III", "IV"],
    },
    {
        "header_pattern": r"SUPUESTO I\s*[—–-]\s*Preguntas\s+1\s+a\s+20",
        "key": "case_iii",
        "exercise": "supuesto_practico",
        "reserve": False,
        "count": 20,
        "blocks": ["III"],
    },
    {
        "header_pattern": r"SUPUESTO I\s*[—–-]\s*Preguntas\s+de\s+reserva",
        "key": "case_iii_reserve",
        "exercise": "supuesto_practico",
        "reserve": True,
        "count": 5,
        "blocks": ["III"],
    },
    {
        "header_pattern": r"SUPUESTO II\s*[—–-]\s*Preguntas\s+1\s+a\s+20",
        "key": "case_iv",
        "exercise": "supuesto_practico",
        "reserve": False,
        "count": 20,
        "blocks": ["IV"],
    },
    {
        "header_pattern": r"SUPUESTO II\s*[—–-]\s*Preguntas\s+de\s+reserva",
        "key": "case_iv_reserve",
        "exercise": "supuesto_practico",
        "reserve": True,
        "count": 5,
        "blocks": ["IV"],
    },
]

# ─── Patrones de clasificación (mismos que build_bank.py) ────────────────────

PATTERNS: dict[str, list[str]] = {
    "I.1": ["constitucion", "derecho fundamental", "libertad", "corona", "rey", "reina", "trono", "estado de sitio", "estado de excepcion", "reforma constitucional", "titulo preliminar", "articulo 1 ", "articulo 2 ", "derechos y deberes"],
    "I.2": ["cortes generales", "congreso", "senado", "diputado", "senador", "tribunal constitucional", "defensor del pueblo", "recurso de amparo", "diputacion permanente", "circunscripcion electoral"],
    "I.3": ["gobierno", "consejo de ministros", "presidente del gobierno", "ministro", "mocion de censura", "cuestion de confianza", "investidura", "ley 50/1997"],
    "I.4": ["empleado publico", "funcionario", "estatuto basico", "provision de puestos", "carrera profesional", "incompatibilidad", "regimen disciplinario", "transparencia", "publicidad activa", "agenda 2030", "desarrollo sostenible", "ley 19/2013", "ebep", "trebep", "real decreto legislativo 5/2015"],
    "I.5": ["igualdad", "violencia de genero", "lgtbi", "persona trans", "discriminacion", "discapacidad", "dependencia", "accesibilidad universal", "ley organica 1/2004", "ley organica 3/2007", "ley 4/2023", "ley 15/2022"],
    "I.6": ["firma electronica", "certificado electronico", "certificado reconocido", "prestador de servicios", "dni electronico", "dnie", "eidas", "sociedad de la informacion", "agenda digital", "reglamento 910/2014", "ley 6/2020"],
    "I.7": ["proteccion de datos", "datos personales", "responsable del fichero", "encargado del tratamiento", "agencia espanola de proteccion", "lopd", "rgpd", "derechos digitales", "consentimiento del interesado", "ley organica 3/2018", "reglamento 2016/679", "delegado de proteccion"],
    "I.8": ["procedimiento administrativo", "registro electronico", "notificacion electronica", "expediente electronico", "esquema nacional de seguridad", "esquema nacional de interoperabilidad", "norma tecnica de interoperabilidad", "documento electronico", "ley 39/2015", "ley 40/2015", "real decreto 311/2022", "ens ", "eni ", "ccn-cert", "ccn", "centro criptologico nacional", "guia ccn-stic", "ccn-stic", "pilar", "clara", "codigo danino", "codigo malicioso"],
    "I.9": ["sede electronica", "punto de acceso", "carpeta ciudadana", "clave ", "cl@ve", "plataforma de intermediacion", "identificacion", "autenticacion", "red sara", "inside", "apodera", "notific", "direccion electronica habilitada"],
    "II.1": ["arquitectura de ordenador", "procesador", "cpu", "unidad aritmetica", "memoria ram", "memoria cache", "bus ", "placa base", "codigo binario", "representacion de la informacion", "bit ", "byte", "von neumann"],
    "II.2": ["periferico", "impresora", "scanner", "digitalizacion", "pantalla", "monitor", "almacenamiento", "disco ssd", "usb", "hdmi", "thunderbolt", "blu-ray"],
    "II.3": ["estructura de datos", "lista enlazada", "pila", "cola", "arbol", "grafo", "algoritmo", "fichero", "archivo", "json", "formato", "ordenacion", "complejidad", "hash", "tabla hash"],
    "II.4": ["sistema operativo", "windows", "unix", "linux", "android", "ios", "proceso", "hilo", "kernel", "shell", "powershell", "directorio", "sistema de archivos", "ntfs", "ext4"],
    "II.5": ["sistema gestor de base", "sgbd", "dbms", "base de datos relacional", "nosql", "mongodb", "mysql", "oracle", "sql server", "postgresql"],
    "III.1": ["modelo de datos", "entidad", "atributo", "relacion", "diagrama e/r", "modelo relacional", "normalizacion", "forma normal", "clave primaria", "clave ajena", "integridad referencial", "cardinalidad"],
    "III.2": ["lenguaje de programacion", "pseudocodigo", "variable", "operador", "bucle", "recurs", "vector", "registro", "procedimiento", "funcion", "parametro", "compilador", "interprete"],
    "III.3": [" sql", "select ", "insert ", "update ", "delete ", "create table", "alter table", "trigger", "procedimiento almacenado", "consulta", "transaccion", "where ", "group by", "having", "join "],
    "III.4": ["orientad", "objeto", "clase", "herencia", "encapsul", "polimorf", "uml", "caso de uso", "patron de diseno", "singleton", "factory", "diagrama de clases", "abstract", "interface"],
    "III.5": ["java", "jakarta", " j2ee", "java ee", "ejb", "servlet", "jsp", "spring", ".net", "ado.net", " c#", "visual basic", "maven", "glassfish", "hibernate", "jpa"],
    "III.6": ["cliente-servidor", "cliente/servidor", "multicapa", "tres capas", "servicio web", "soap", "wsdl", "rest", "api ", "arquitectura orientada a servicios", "microservicio"],
    "III.7": ["html", " xhtml", "css", "javascript", "typescript", "php", "xml", "xsl", "navegador", "pagina web", "dom ", "cookie", "script", "ajax", "angular", "react", "vue"],
    "III.8": ["accesibilidad", "usabilidad", "wcag", "wai", "aria", "diseno universal", "xss", "inyeccion", "seguridad en el desarrollo", "puesto de usuario", "owasp"],
    "III.9": ["repositorio", "git", "svn", "control de versiones", "prueba", "testing", "scrum", "metodologia", "integracion continua", "jenkins", "sonarqube", "desarrollo colaborativo", "agil", "devops", "ci/cd"],
    "IV.1": ["administrador de sistemas", "administracion del sistema", "software de base", "systemctl", "servicio", "actualizacion", "parche", "mantenimiento", "arranque", "registro de windows", "active directory", "gpo", "politica de grupo"],
    "IV.2": ["administracion de base", "backup", "copia de seguridad", "recuperacion", "snapshot", "raid", "san ", "nas ", "almacenamiento", "virtualizacion", "hipervisor", "maquina virtual", "lto", "lvm", "vmware", "hyper-v"],
    "IV.3": ["correo electronico", "smtp", "pop3", "imap", "exchange", "postfix", "contenedor", "docker", "kubernetes", "microservicio", "orquestacion"],
    "IV.4": ["administracion de red", "monitorizacion", "snmp", "gestion de usuarios", "directorio activo", "control de trafico", "vlan", "dhcp", "switch", "router", "nagios", "zabbix"],
    "IV.5": ["seguridad", "amenaza", "vulnerabilidad", "riesgo", "cifrado", "criptograf", "certificado digital", "cpd", "incidencia", "malware", "virus", "auditoria", "control remoto", "aes", "rsa", "centro de proceso"],
    "IV.6": ["comunicacion", "medio de transmision", "fibra", "cable", "modem", "conmutacion", "wifi", "wi-fi", "bluetooth", "wimax", "inalambric", "telefonia", "adsl", "rdsi", "atm", "multiplexacion"],
    "IV.7": ["modelo osi", "tcp/ip", "capa de", "ipv4", "ipv6", "direccion ip", "subred", "mascara", "tcp ", "udp ", "icmp", "arp ", "enrutamiento", "protocolo de transporte", "capa de red"],
    "IV.8": ["internet", "http", "https", "ssl", "tls", "url", "uri", "dns", "ftp", "telnet", "www", "navegacion", "protocolo de aplicacion"],
    "IV.9": ["vpn", "firewall", "cortafuegos", "seguridad perimetral", "dmz", "acceso remoto", "ipsec", "tunel", "proxy", "ids", "ips", "phishing", "spoofing", "nids", "hids"],
    "IV.10": ["red local", "lan", "ethernet", "802.", "topologia", "metodo de acceso", "csma", "token ring", "interconexion", "mac ", "cableado estructurado", "hub", "gigabit"],
}

OUTDATED = {
    "ley 30/1992": "Ley 30/1992 derogada",
    "ley 11/2007": "Ley 11/2007 derogada",
    "ley organica 15/1999": "LOPD 15/1999 derogada",
    "ley 59/2003": "Ley 59/2003 derogada",
    "real decreto 1671/2009": "Real Decreto 1671/2009 derogado",
    "real decreto 209/2003": "Real Decreto 209/2003 derogado",
    "ley 6/1997": "LOFAGE derogada",
}

MIN_CONFIDENCE = 0.68

# Curaciones manuales de tema para casos inequívocos
TOPIC_OVERRIDES: dict[str, tuple[str, float, str]] = {
    # Herramienta del CCN-CERT (análisis estático de código dañino: MARIA, PILAR, CLARA, REYES) -> ENS (Tema I.8)
    "2019-libre-ordinario:first:77": ("I.8", 1.0, "curacion_manual_verificada"),
}


def folded(value: str) -> str:
    """Normaliza para búsqueda: minúsculas, sin acentos."""
    return "".join(
        c for c in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(c) != "Mn"
    )


# ─── Parser del TXT ─────────────────────────────────────────────────────────

QUESTION_START = re.compile(r"^(\d+)\.\s+(.+)")
OPTION_LINE = re.compile(r"^\s+([A-D])\)\s+(.+)")
ANSWER_LINE = re.compile(r"^\s+RESPUESTA CORRECTA:\s+([A-D])\)")
SECTION_HEADER = re.compile(
    r"^(PRIMERA PARTE|SUPUESTO [IV]+)\s*[—–-]\s*(Preguntas.*)"
)


def parse_txt(path: Path) -> list[dict]:
    """Parsea un TXT de examen y devuelve preguntas con sus secciones."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    questions: list[dict] = []
    current_section = None
    current_number = None
    current_prompt_lines: list[str] = []
    current_options: list[tuple[str, str]] = []
    current_answer = None

    # Identify section boundaries
    section_ranges: list[tuple[int, dict]] = []
    for i, line in enumerate(lines):
        for spec in SECTION_SPECS:
            if re.search(spec["header_pattern"], line):
                section_ranges.append((i, spec))
                break

    # Build a mapping: line_number -> section spec
    def get_section_for_line(line_num: int) -> dict | None:
        result = None
        for start, spec in section_ranges:
            if line_num > start:
                result = spec
        return result

    def flush_question():
        nonlocal current_number, current_prompt_lines, current_options, current_answer, current_section
        if current_number is not None and current_prompt_lines:
            prompt = " ".join(current_prompt_lines).strip()
            prompt = re.sub(r"\s+", " ", prompt)
            options = [text.strip() for _, text in current_options]
            answer_letter = current_answer.lower() if current_answer else None
            questions.append({
                "section_spec": current_section,
                "number": current_number,
                "prompt": prompt,
                "options": options,
                "answer": answer_letter,
                "answer_raw": current_answer,
            })
        current_number = None
        current_prompt_lines = []
        current_options = []
        current_answer = None

    in_answer_line = False

    for i, line in enumerate(lines):
        # Skip header lines and section markers
        if SECTION_HEADER.match(line):
            flush_question()
            current_section = get_section_for_line(i)
            continue
        if re.match(r"^[-=]+$", line.strip()):
            continue

        # Check for answer line
        answer_match = ANSWER_LINE.match(line)
        if answer_match:
            current_answer = answer_match.group(1)
            flush_question()
            continue

        # Check for option line
        option_match = OPTION_LINE.match(line)
        if option_match:
            current_options.append((option_match.group(1), option_match.group(2)))
            continue

        # Check for question start
        question_match = QUESTION_START.match(line)
        if question_match:
            # Before starting a new question, flush the old one
            # (shouldn't have pending questions here because answer lines flush)
            section_at_line = get_section_for_line(i)
            if section_at_line:
                current_section = section_at_line
            current_number = int(question_match.group(1))
            current_prompt_lines = [question_match.group(2)]
            current_options = []
            current_answer = None
            continue

        # Continuation of prompt text (multi-line prompts)
        stripped = line.strip()
        if stripped and current_number is not None and not current_options:
            current_prompt_lines.append(stripped)
        elif stripped and current_number is not None and current_options:
            # Continuation of the last option
            letter, text = current_options[-1]
            current_options[-1] = (letter, text + " " + stripped)

    flush_question()
    return questions


# ─── Clasificación temática ──────────────────────────────────────────────────

def classify(prompt: str, options: list[str], allowed_blocks: list[str]) -> tuple[str, float, str]:
    """Clasifica una pregunta en un tema usando el sistema de patrones."""
    prompt_folded = folded(prompt)
    all_text = folded(prompt + " " + " ".join(options))
    scores: dict[str, float] = {}

    for topic, patterns in PATTERNS.items():
        block = topic.split(".")[0]
        if block not in allowed_blocks:
            continue
        score = 0.0
        for pattern in patterns:
            term = folded(pattern)
            if term in prompt_folded:
                score += 3.0 + min(2.0, len(term) / 20)
            elif term in all_text:
                score += 1.0
        scores[topic] = score

    if not scores:
        # Fallback: search all topics
        for topic, patterns in PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                term = folded(pattern)
                if term in prompt_folded:
                    score += 3.0 + min(2.0, len(term) / 20)
                elif term in all_text:
                    score += 1.0
            scores[topic] = score

    ranking = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    topic, top = ranking[0]
    second = ranking[1][1] if len(ranking) > 1 else 0

    if top == 0:
        return topic, 0.30, "fallback_sin_indicio"

    margin = top - second
    confidence = min(0.98, 0.56 + top * 0.035 + margin * 0.025)
    return topic, round(confidence, 2), "taxonomia_reglas_2025"


# ─── Validaciones ────────────────────────────────────────────────────────────

def validate_question(q: dict) -> list[str]:
    """Devuelve una lista de problemas encontrados."""
    issues = []
    if len(q["options"]) != 4:
        issues.append(f"Tiene {len(q['options'])} opciones en lugar de 4")
    if any(not opt.strip() for opt in q["options"]):
        issues.append("Tiene alguna opción vacía")
    if not q["prompt"].strip():
        issues.append("Enunciado vacío")
    if q["answer"] not in ("a", "b", "c", "d", None):
        issues.append(f"Respuesta inválida: {q['answer']}")
    if not q.get("section_spec"):
        issues.append("Sin sección asignada")
    return issues


def detect_outdated(prompt: str, options: list[str]) -> str | None:
    """Detecta normativa derogada en el texto."""
    full = folded(prompt + " " + " ".join(options))
    for term, reason in OUTDATED.items():
        if term in full:
            return reason
    return None


# ─── Construcción del banco ──────────────────────────────────────────────────

def build_bank() -> tuple[dict, list[dict], list[dict]]:
    """Construye el banco completo desde los TXT."""
    questions: list[dict] = []
    exam_summaries: list[dict] = []
    coverage: list[dict] = []
    excluded: list[dict] = []

    for exam in EXAM_MANIFEST:
        folder = EXAMENES_DIR / exam["folder"]
        txt_path = folder / "03 Preguntas y respuestas en texto.txt"
        pdf_path = folder / "01 Cuestionario.pdf"
        plantilla_path = folder / "02 Plantilla de respuestas.pdf"

        if not txt_path.exists():
            print(f"AVISO: No se encuentra {txt_path}")
            continue

        raw_questions = parse_txt(txt_path)
        exam_questions: list[dict] = []
        exam_excluded: list[dict] = []
        section_counts: dict[str, int] = {}

        for rq in raw_questions:
            spec = rq["section_spec"]
            if spec is None:
                excluded.append({
                    "exam": exam["id"],
                    "number": rq["number"],
                    "prompt_preview": rq["prompt"][:100],
                    "reason": "Pregunta fuera de cualquier sección reconocida",
                })
                continue

            # Validation
            issues = validate_question(rq)
            if issues:
                excluded.append({
                    "exam": exam["id"],
                    "section": spec["key"],
                    "number": rq["number"],
                    "prompt_preview": rq["prompt"][:100],
                    "reason": "; ".join(issues),
                })
                continue

            qid = f"{exam['id']}:{spec['key']}:{rq['number']}"

            # Classification
            if qid in TOPIC_OVERRIDES:
                topic, confidence, method = TOPIC_OVERRIDES[qid]
            else:
                topic, confidence, method = classify(
                    rq["prompt"], rq["options"], spec["blocks"]
                )
            block = topic.split(".")[0]

            # Status determination
            outdated_reason = detect_outdated(rq["prompt"], rq["options"])
            if rq["answer"] is None:
                status = "missing_official_answer"
                reason = "Sin plantilla oficial disponible"
                active = False
            elif outdated_reason:
                status = "outdated"
                reason = outdated_reason
                active = False
            elif confidence < MIN_CONFIDENCE:
                status = "classification_review"
                reason = "Tema asignado con indicios insuficientes para el banco vigente"
                active = False
            else:
                status = "valid"
                reason = "Respuesta oficial enlazada y clasificación compatible con el programa vigente"
                active = True

            question = {
                "id": qid,
                "examId": exam["id"],
                "year": exam["year"],
                "access": exam["access"],
                "sitting": exam["sitting"],
                "exercise": spec["exercise"],
                "section": spec["key"],
                "isReserve": spec["reserve"],
                "originalNumber": rq["number"],
                "prompt": rq["prompt"],
                "options": rq["options"],
                "correctAnswer": rq["answer"],
                "answerStatus": exam["answerStatus"],
                "blockId": block,
                "topicId": topic,
                "classificationConfidence": confidence,
                "classificationMethod": method,
                "status": status,
                "statusReason": reason,
                "active": active,
                "duplicateOf": None,
                "source": {
                    "pdf": f"EXAMENES REALES/{exam['folder']}/01 Cuestionario.pdf",
                    "page": 0,
                    "answerPdf": f"EXAMENES REALES/{exam['folder']}/02 Plantilla de respuestas.pdf",
                    "extraction": "transcripcion_manual_verificada",
                },
            }

            section_counts[spec["key"]] = section_counts.get(spec["key"], 0) + 1
            exam_questions.append(question)

        # Check for duplicates within the exam set
        for q in exam_questions:
            questions.append(q)

        exam_summaries.append({
            "id": exam["id"],
            "name": exam["name"],
            "year": exam["year"],
            "access": exam["access"],
            "sitting": exam["sitting"],
        })

        coverage.append({
            "examId": exam["id"],
            "expected": 135,
            "extracted": len(exam_questions),
            "active": sum(1 for q in exam_questions if q["active"]),
            "sectionCounts": section_counts,
            "excluded": len(exam_excluded),
        })

    # Detect cross-exam duplicates
    seen: dict[str, str] = {}
    for question in questions:
        sig = re.sub(r"\W+", "", folded(question["prompt"]))[:160]
        if sig in seen:
            question["duplicateOf"] = seen[sig]
            if question["active"]:
                question["status"] = "duplicate"
                question["statusReason"] = "Duplicada literalmente; se conserva la primera aparición"
                question["active"] = False
        else:
            seen[sig] = question["id"]

    bank = {
        "meta": {
            "schemaVersion": 2,
            "builtAt": date.today().isoformat(),
            "officialCall": "TAILI.pdf",
            "sourceFolder": "EXAMENES REALES/ (transcripción manual verificada)",
            "scoringNote": "Directa = aciertos - errores/3. La nota oficial requiere la transformación de la CPS.",
        },
        "examConfig": {
            "durationMinutes": 120,
            "firstPartQuestions": 80,
            "firstPartReserve": 5,
            "practicalQuestions": 20,
            "practicalReserve": 5,
            "wrongPenalty": 1 / 3,
            "blankPenalty": 0,
            "officialMaximum": 100,
            "partMaximum": 50,
            "officialCutNote": "Cada parte exige 25/50 tras la transformación de la CPS; la puntuación directa mínima se publica por separado.",
        },
        "program": PROGRAM,
        "documents": [
            {
                "id": f"examreal-{exam['id']}-cuestionario",
                "path": f"EXAMENES REALES/{exam['folder']}/01 Cuestionario.pdf",
                "pages": 0,
                "role": "cuestionario",
                "year": exam["year"],
                "status": "imported",
                "note": f"Cuestionario oficial {exam['year']} ({exam['sitting']})",
            }
            for exam in EXAM_MANIFEST
        ] + [
            {
                "id": f"examreal-{exam['id']}-plantilla",
                "path": f"EXAMENES REALES/{exam['folder']}/02 Plantilla de respuestas.pdf",
                "pages": 0,
                "role": "plantilla",
                "year": exam["year"],
                "status": "imported",
                "note": f"Plantilla de respuestas {exam['year']} ({exam['sitting']})",
            }
            for exam in EXAM_MANIFEST
        ],
        "exams": exam_summaries,
        "questions": questions,
    }

    return bank, coverage, excluded


# ─── Informes ────────────────────────────────────────────────────────────────

def generate_report(
    bank: dict,
    coverage: list[dict],
    excluded: list[dict],
) -> str:
    """Genera el informe en Markdown."""
    lines: list[str] = []
    total = len(bank["questions"])
    active = sum(1 for q in bank["questions"] if q["active"])
    status_counts = Counter(q["status"] for q in bank["questions"])
    topic_counts = Counter(q["topicId"] for q in bank["questions"] if q["active"])

    lines.append("# Informe de importación · EXAMENES REALES → Preparador TAI")
    lines.append("")
    lines.append(f"Fecha: {date.today().isoformat()}")
    lines.append(f"Fuente: `EXAMENES REALES/` (5 convocatorias)")
    lines.append("")

    lines.append("## Resumen general")
    lines.append("")
    lines.append(f"- **Exámenes procesados**: {len(bank['exams'])}")
    lines.append(f"- **Preguntas totales**: {total}")
    lines.append(f"- **Banco activo (vigente)**: {active}")
    lines.append(f"- **Excluidas del banco activo**: {total - active}")
    lines.append(f"- **Rechazadas en parsing**: {len(excluded)}")
    lines.append("")

    lines.append("## Estado de las preguntas")
    lines.append("")
    for key, val in sorted(status_counts.items()):
        lines.append(f"- `{key}`: {val}")
    lines.append("")

    lines.append("## Cobertura por examen")
    lines.append("")
    lines.append("| Examen | Esperadas | Extraídas | Activas | Secciones |")
    lines.append("|--------|-----------|-----------|---------|-----------|")
    for c in coverage:
        sections = ", ".join(f"{k}={v}" for k, v in c["sectionCounts"].items())
        lines.append(f"| {c['examId']} | {c['expected']} | {c['extracted']} | {c['active']} | {sections} |")
    lines.append("")

    lines.append("## Distribución por tema (banco activo)")
    lines.append("")
    for block in PROGRAM:
        lines.append(f"### Bloque {block['id']}: {block['name']}")
        lines.append("")
        for topic in block["topics"]:
            count = topic_counts.get(topic["id"], 0)
            lines.append(f"- **{topic['id']}**: {count} preguntas")
        lines.append("")

    if excluded:
        lines.append("## Preguntas rechazadas en parsing")
        lines.append("")
        for ex in excluded:
            lines.append(f"- [{ex.get('exam', '?')}] #{ex.get('number', '?')}: {ex['reason']}")
            lines.append(f"  Texto: _{ex.get('prompt_preview', '')}_")
        lines.append("")

    # Questions excluded from active bank
    inactive = [q for q in bank["questions"] if not q["active"]]
    if inactive:
        lines.append("## Preguntas fuera del banco activo")
        lines.append("")
        lines.append("| ID | Examen | Sección | # | Estado | Motivo |")
        lines.append("|----|--------|---------|---|--------|--------|")
        for q in inactive:
            lines.append(f"| {q['id']} | {q['examId']} | {q['section']} | {q['originalNumber']} | `{q['status']}` | {q['statusReason']} |")
        lines.append("")

    lines.append("## Criterio de admisión")
    lines.append("")
    lines.append("Las preguntas entran en el banco vigente (`active: true`) únicamente si:")
    lines.append("1. Tienen respuesta oficial (letra A–D).")
    lines.append("2. La clasificación temática alcanza confianza ≥ 0.68.")
    lines.append("3. No hacen referencia a normativa expresamente derogada.")
    lines.append("4. No son duplicadas literales de otra pregunta anterior.")
    lines.append("")
    lines.append("Las preguntas excluidas se conservan con trazabilidad completa y")
    lines.append("pueden consultarse en el explorador con el filtro 'Pendientes de revisión'.")

    return "\n".join(lines) + "\n"


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not EXAMENES_DIR.exists():
        raise SystemExit(f"No se encuentra la carpeta: {EXAMENES_DIR}")

    print(f"Escaneando {EXAMENES_DIR}...")
    bank, coverage, excluded = build_bank()

    total = len(bank["questions"])
    active = sum(1 for q in bank["questions"] if q["active"])
    print(f"Total: {total} preguntas; {active} vigentes; {len(excluded)} rechazadas")

    # Validate all questions
    print("\nValidando integridad...")
    errors = 0
    for q in bank["questions"]:
        if len(q["options"]) != 4:
            print(f"  ERROR: {q['id']} tiene {len(q['options'])} opciones")
            errors += 1
        if any(not opt.strip() for opt in q["options"]):
            print(f"  ERROR: {q['id']} tiene opción vacía")
            errors += 1
        if not q["prompt"].strip():
            print(f"  ERROR: {q['id']} tiene enunciado vacío")
            errors += 1
        if q["correctAnswer"] not in ("a", "b", "c", "d"):
            print(f"  ERROR: {q['id']} respuesta inválida: {q['correctAnswer']}")
            errors += 1
        if q["topicId"] not in ALL_TOPICS:
            print(f"  ERROR: {q['id']} tema desconocido: {q['topicId']}")
            errors += 1

    if errors:
        print(f"\n¡{errors} errores de integridad encontrados!")
    else:
        print("  ✓ Todas las preguntas superan la validación de integridad.")

    # Verify section counts per exam
    print("\nRecuentos por sección:")
    for c in coverage:
        print(f"  {c['examId']}: {c['extracted']}/135 preguntas")
        for key, count in sorted(c["sectionCounts"].items()):
            expected = next((s["count"] for s in SECTION_SPECS if s["key"] == key), "?")
            mark = "✓" if count == expected else f"✗ (esperado {expected})"
            print(f"    {key}: {count} {mark}")

    # Write bank.json
    DATA.mkdir(parents=True, exist_ok=True)
    bank_path = DATA / "bank.json"
    bank_path.write_text(
        json.dumps(bank, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nBanco escrito: {bank_path}")

    # Write report
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = generate_report(bank, coverage, excluded)
    report_path = REPORTS / "import-examenes-reales.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Informe escrito: {report_path}")

    # Write detailed coverage
    coverage_path = REPORTS / "coverage-examenes-reales.json"
    coverage_path.write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Cobertura escrita: {coverage_path}")

    # Write excluded questions detail
    excluded_path = REPORTS / "excluded-examenes-reales.json"
    excluded_path.write_text(
        json.dumps(excluded, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Excluidas escrito: {excluded_path}")

    # Topic distribution summary
    print("\nDistribución por tema (banco activo):")
    topic_counts = Counter(q["topicId"] for q in bank["questions"] if q["active"])
    for block in PROGRAM:
        block_total = sum(topic_counts.get(t["id"], 0) for t in block["topics"])
        print(f"  Bloque {block['id']}: {block_total}")
        for topic in block["topics"]:
            count = topic_counts.get(topic["id"], 0)
            print(f"    {topic['id']}: {count}")


if __name__ == "__main__":
    main()
