#!/usr/bin/env python3
"""Construye el banco completo, trazable y conservador desde los PDF fuente."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from answer_templates import answer_stream, split_answers
from exam_manifest import EXAMS
from extraction import ExtractedQuestion, extract_question_sources
from ocr_sources import needs_ocr


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "TAI AGE"
OFFICIAL_CALL = ROOT / "TAILI.pdf"
DATA = ROOT / "src" / "data"
REPORTS = ROOT / "reports"
MIN_CLASSIFICATION_CONFIDENCE = 0.68


PROGRAM = [
    {"id": "I", "name": "Organización del Estado y Administración electrónica", "topics": [
        {"id": "I.1", "name": "La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. La Corona: funciones constitucionales del Rey."},
        {"id": "I.2", "name": "Las Cortes Generales: atribuciones del Congreso de los Diputados y del Senado. El Tribunal Constitucional: composición y atribuciones. El Defensor del Pueblo."},
        {"id": "I.3", "name": "El Gobierno: composición, nombramiento y cese. Las funciones del Gobierno. Relaciones entre el Gobierno y las Cortes Generales."},
        {"id": "I.4", "name": "El texto refundido del Estatuto Básico del Empleo Público y demás normativa de aplicación: derechos y deberes, formas de provisión de puestos, promoción interna y carrera profesional; situaciones administrativas, incompatibilidades y régimen sancionador. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno. La Agenda 2030 y los Objetivos de Desarrollo Sostenible."},
        {"id": "I.5", "name": "Políticas de igualdad y contra la violencia de género. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico."},
        {"id": "I.6", "name": "La sociedad de la información. Identidad y firma electrónica: régimen jurídico. El DNI electrónico. La Agenda Digital para España."},
        {"id": "I.7", "name": "La protección de datos personales y su régimen jurídico: principios, derechos y obligaciones. Derechos digitales."},
        {"id": "I.8", "name": "Acceso electrónico de los ciudadanos a los servicios públicos y normativa de desarrollo. La gestión electrónica de los procedimientos administrativos: registros, notificaciones y uso de medios electrónicos. Esquema Nacional de Seguridad y de Interoperabilidad. Normas técnicas de Interoperabilidad."},
        {"id": "I.9", "name": "Instrumentos para el acceso electrónico a las Administraciones públicas: sedes electrónicas, canales y puntos de acceso, identificación y autenticación. Infraestructuras y servicios comunes en materia de administración electrónica."},
    ]},
    {"id": "II", "name": "Tecnología básica", "topics": [
        {"id": "II.1", "name": "Informática básica. Representación y comunicación de la información: elementos constitutivos de un sistema de información. Características y funciones. Arquitectura de ordenadores. Componentes internos de los equipos microinformáticos."},
        {"id": "II.2", "name": "Periféricos: conectividad y administración. Elementos de impresión. Elementos de almacenamiento. Elementos de visualización y digitalización."},
        {"id": "II.3", "name": "Tipos abstractos y Estructuras de datos. Organizaciones de ficheros. Algoritmos. Formatos de información y ficheros."},
        {"id": "II.4", "name": "Sistemas operativos. Características y elementos constitutivos. Sistemas Windows. Sistemas Unix y Linux. Sistemas operativos para dispositivos móviles."},
        {"id": "II.5", "name": "Sistemas de gestión de bases de datos relacionales, orientados a objetos y NoSQL: características y componentes."},
    ]},
    {"id": "III", "name": "Desarrollo de sistemas", "topics": [
        {"id": "III.1", "name": "Modelado de datos, metodologías y reglas. Entidades, atributos y relaciones. Diseño de bases de datos. Diseño lógico y físico. El modelo lógico relacional. Normalización."},
        {"id": "III.2", "name": "Lenguajes de programación. Representación de tipos de datos. Operadores. Instrucciones condicionales. Bucles y recursividad. Procedimientos, funciones y parámetros. Vectores y registros. Estructura de un programa."},
        {"id": "III.3", "name": "Lenguajes de interrogación de bases de datos. Estándar ANSI SQL. Procedimientos almacenados. Eventos y disparadores."},
        {"id": "III.4", "name": "Diseño y programación orientada a objetos. Elementos y componentes software: objetos, clases, herencia, métodos, sobrecarga. Ventajas e inconvenientes. Patrones de diseño y lenguaje de modelado unificado (UML)."},
        {"id": "III.5", "name": "Arquitectura Java EE/Jakarta EE y plataforma .NET: componentes, persistencia y seguridad. Características, elementos, lenguajes y funciones en ambos entornos. Desarrollo de Interfaces."},
        {"id": "III.6", "name": "Arquitectura de sistemas cliente/servidor y multicapas: componentes y operación. Arquitecturas de servicios web y protocolos asociados."},
        {"id": "III.7", "name": "Aplicaciones web. Desarrollo web front-end y en servidor, multiplataforma y multidispositivo. Lenguajes: HTML, XML y sus derivaciones. Navegadores y lenguajes de programación web. Lenguajes de script."},
        {"id": "III.8", "name": "Accesibilidad, diseño universal y usabilidad. Acceso y usabilidad de las tecnologías, productos y servicios relacionados con la sociedad de la información. Confidencialidad y disponibilidad de la información en puestos de usuario final. Conceptos de seguridad en el desarrollo de los sistemas."},
        {"id": "III.9", "name": "Repositorios: estructura y actualización. Generación de código y documentación. Metodologías de desarrollo. Pruebas. Programas para control de versiones. Plataformas de desarrollo colaborativo de software."},
    ]},
    {"id": "IV", "name": "Sistemas y comunicaciones", "topics": [
        {"id": "IV.1", "name": "Administración del Sistema operativo y software de base. Actualización, mantenimiento y reparación del sistema operativo."},
        {"id": "IV.2", "name": "Administración de bases de datos. Sistemas de almacenamiento y su virtualización. Políticas, sistemas y procedimientos de backup y su recuperación. Backup de sistemas físicos y virtuales. Virtualización de sistemas y virtualización de puestos de usuario."},
        {"id": "IV.3", "name": "Administración de servidores de correo electrónico sus protocolos. Administración de contenedores y microservicios."},
        {"id": "IV.4", "name": "Administración de redes de área local. Gestión de usuarios. Gestión de dispositivos. Monitorización y control de tráfico."},
        {"id": "IV.5", "name": "Conceptos de seguridad de los sistemas de información. Seguridad física. Seguridad lógica. Amenazas y vulnerabilidades. Técnicas criptográficas y protocolos seguros. Mecanismos de firma digital. Infraestructura física de un CPD: acondicionamiento y equipamiento. Sistemas de gestión de incidencias. Control remoto de puestos de usuario."},
        {"id": "IV.6", "name": "Comunicaciones. Medios de transmisión. Modos de comunicación. Equipos terminales y equipos de interconexión y conmutación. Redes de comunicaciones. Redes de conmutación y redes de difusión. Comunicaciones móviles e inalámbricas."},
        {"id": "IV.7", "name": "El modelo TCP/IP y el modelo de referencia de interconexión de sistemas abiertos (OSI) de ISO. Protocolos TCP/IP."},
        {"id": "IV.8", "name": "Internet: arquitectura de red. Origen, evolución y estado actual. Principales servicios. Protocolos HTTP, HTTPS y SSL/TLS."},
        {"id": "IV.9", "name": "Seguridad y protección en redes de comunicaciones. Seguridad perimetral. Acceso remoto seguro a redes. Redes privadas virtuales (VPN). Seguridad en el puesto del usuario."},
        {"id": "IV.10", "name": "Redes locales. Tipología. Técnicas de transmisión. Métodos de acceso. Dispositivos de interconexión."},
    ]},
]


PATTERNS: dict[str, list[str]] = {
    "I.1": ["constitucion", "derecho fundamental", "libertad", "corona", "rey", "reina", "trono", "estado de sitio", "estado de excepcion", "reforma constitucional"],
    "I.2": ["cortes generales", "congreso", "senado", "diputado", "senador", "tribunal constitucional", "defensor del pueblo", "recurso de amparo", "diputacion permanente"],
    "I.3": ["gobierno", "consejo de ministros", "presidente del gobierno", "ministro", "mocion de censura", "cuestion de confianza", "investidura"],
    "I.4": ["empleado publico", "funcionario", "estatuto basico", "provision de puestos", "carrera profesional", "incompatibilidad", "regimen disciplinario", "transparencia", "publicidad activa", "agenda 2030", "desarrollo sostenible"],
    "I.5": ["igualdad", "violencia de genero", "lgtbi", "persona trans", "discriminacion", "discapacidad", "dependencia", "accesibilidad universal"],
    "I.6": ["firma electronica", "certificado electronico", "certificado reconocido", "prestador de servicios", "dni electronico", "dnie", "eidas", "sociedad de la informacion", "agenda digital"],
    "I.7": ["proteccion de datos", "datos personales", "responsable del fichero", "encargado del tratamiento", "agencia espanola de proteccion", "lopd", "rgpd", "derechos digitales", "consentimiento del interesado"],
    "I.8": ["procedimiento administrativo", "registro electronico", "notificacion electronica", "expediente electronico", "esquema nacional de seguridad", "esquema nacional de interoperabilidad", "norma tecnica de interoperabilidad", "documento electronico"],
    "I.9": ["sede electronica", "punto de acceso", "carpeta ciudadana", "clave ", "cl@ve", "plataforma de intermediacion", "identificacion", "autenticacion", "red sara", "inside", "apodera"],
    "II.1": ["arquitectura de ordenador", "procesador", "cpu", "unidad aritmetica", "memoria ram", "memoria cache", "bus ", "placa base", "codigo binario", "representacion de la informacion", "bit ", "byte"],
    "II.2": ["periferico", "impresora", "scanner", "digitalizacion", "pantalla", "monitor", "almacenamiento", "disco ssd", "usb", "hdmi", "thunderbolt", "blu-ray"],
    "II.3": ["estructura de datos", "lista", "pila", "cola", "arbol", "grafo", "algoritmo", "fichero", "archivo", "json", "formato", "ordenacion", "complejidad"],
    "II.4": ["sistema operativo", "windows", "unix", "linux", "android", "ios", "proceso", "hilo", "kernel", "shell", "powershell", "directorio", "sistema de archivos"],
    "II.5": ["sistema gestor de base", "sgbd", "dbms", "base de datos relacional", "nosql", "mongodb", "mysql", "oracle", "sql server"],
    "III.1": ["modelo de datos", "entidad", "atributo", "relacion", "diagrama e/r", "modelo relacional", "normalizacion", "forma normal", "clave primaria", "clave ajena", "integridad referencial"],
    "III.2": ["lenguaje de programacion", "algoritmo", "pseudocodigo", "variable", "operador", "bucle", "recurs", "vector", "registro", "procedimiento", "funcion", "parametro", "compilador"],
    "III.3": [" sql", "select ", "insert ", "update ", "delete ", "create table", "alter table", "trigger", "procedimiento almacenado", "consulta", "transaccion"],
    "III.4": ["orientad", "objeto", "clase", "herencia", "encapsul", "polimorf", "uml", "caso de uso", "patron de diseno", "singleton", "factory", "diagrama de clases"],
    "III.5": ["java", "jakarta", " j2ee", "java ee", "ejb", "servlet", "jsp", "spring", ".net", "ado.net", " c#", "visual basic", "maven", "glassfish"],
    "III.6": ["cliente-servidor", "cliente/servidor", "multicapa", "tres capas", "servicio web", "soap", "wsdl", "rest", "api ", "arquitectura orientada a servicios"],
    "III.7": ["html", " xhtml", "css", "javascript", "typescript", "php", "xml", "xsl", "navegador", "pagina web", "dom ", "cookie", "script"],
    "III.8": ["accesibilidad", "usabilidad", "wcag", "wai", "aria", "diseno universal", "xss", "inyeccion", "seguridad en el desarrollo", "puesto de usuario"],
    "III.9": ["repositorio", "git", "svn", "control de versiones", "prueba", "testing", "scrum", "metodologia", "integracion continua", "jenkins", "sonarqube", "desarrollo colaborativo"],
    "IV.1": ["administrador de sistemas", "administracion del sistema", "software de base", "systemctl", "servicio", "actualizacion", "parche", "mantenimiento", "arranque", "registro de windows", "active directory"],
    "IV.2": ["administracion de base", "backup", "copia de seguridad", "recuperacion", "snapshot", "raid", "san ", "nas ", "almacenamiento", "virtualizacion", "hipervisor", "maquina virtual", "lto", "lvm"],
    "IV.3": ["correo electronico", "smtp", "pop3", "imap", "exchange", "postfix", "contenedor", "docker", "kubernetes", "microservicio"],
    "IV.4": ["administracion de red", "monitorizacion", "snmp", "gestion de usuarios", "directorio activo", "control de trafico", "vlan", "dhcp", "switch", "router"],
    "IV.5": ["seguridad", "amenaza", "vulnerabilidad", "riesgo", "cifrado", "criptograf", "certificado digital", "cpd", "incidencia", "malware", "virus", "auditoria", "control remoto"],
    "IV.6": ["comunicacion", "medio de transmision", "fibra", "cable", "modem", "conmutacion", "wifi", "wi-fi", "bluetooth", "wimax", "inalambric", "telefonia", "adsl", "rdsi", "atm"],
    "IV.7": ["modelo osi", "tcp/ip", "capa de", "ipv4", "ipv6", "direccion ip", "subred", "mascara", "tcp ", "udp ", "icmp", "arp ", "enrutamiento"],
    "IV.8": ["internet", "http", "https", "ssl", "tls", "url", "uri", "dns", "ftp", "telnet", "www", "navegacion"],
    "IV.9": ["vpn", "firewall", "cortafuegos", "seguridad perimetral", "dmz", "acceso remoto", "ipsec", "tunel", "proxy", "ids", "ips", "phishing", "spoofing"],
    "IV.10": ["red local", "lan", "ethernet", "802.", "topologia", "metodo de acceso", "csma", "token ring", "interconexion", "mac ", "cableado estructurado", "hub"],
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


def folded(value: str) -> str:
    return "".join(character for character in unicodedata.normalize("NFD", value.casefold()) if unicodedata.category(character) != "Mn")


PAGE_REFERENCE_RE = re.compile(r"\bp[aá]gina\s+\d+\s+de\s+\d+\b", re.IGNORECASE)
FOOTER_ANCHOR_RE = re.compile(
    r"(?:ejercicio\s+[uú]nico|[12]\s*[-.]\s*(?:test|cp)|20\d{2}\s*[-—–].{0,24}?tai)",
    re.IGNORECASE,
)


def clean(value: str) -> str:
    """Normaliza espacios y elimina únicamente pies de página terminales seguros.

    Si tras una referencia de página hay texto sustantivo, no se recorta: el
    detector de calidad lo pondrá en revisión OCR para evitar ocultar una mezcla
    accidental con la pregunta siguiente.
    """
    value = re.sub(r"\s+", " ", value).strip()
    matches = list(PAGE_REFERENCE_RE.finditer(value))
    if not matches:
        return value
    marker = matches[-1]
    tail = value[marker.end():]
    harmless_tail = re.sub(r"\bbloque\s+[ivx]+\b", "", tail, flags=re.IGNORECASE)
    if re.search(r"[a-záéíóúñ]{3,}", harmless_tail, re.IGNORECASE):
        return value
    window_start = max(0, marker.start() - 110)
    anchors = list(FOOTER_ANCHOR_RE.finditer(value[window_start:marker.start()]))
    cut = window_start + anchors[0].start() if anchors else marker.start()
    return value[:cut].rstrip(" \t\n|,:;*-—–[]()€")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(item: ExtractedQuestion, allowed_blocks: list[str]) -> tuple[str, float, str]:
    prompt = folded(item.prompt)
    all_text = folded(item.prompt + " " + " ".join(item.options))
    scores: dict[str, float] = {}
    for topic, patterns in PATTERNS.items():
        if topic.split(".")[0] not in allowed_blocks:
            continue
        score = 0.0
        for pattern in patterns:
            term = folded(pattern)
            if term in prompt:
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
    return topic, confidence, "taxonomia_reglas_2025"


def dedupe_candidates(items: list[ExtractedQuestion]) -> list[ExtractedQuestion]:
    result: list[ExtractedQuestion] = []
    seen: set[tuple[int, int, str]] = set()
    for item in sorted(items, key=lambda question: (question.page, question.order)):
        signature = re.sub(r"\W+", "", folded(item.prompt))[:160]
        key = (item.page, item.original_number, signature)
        # Hay enunciados oficiales deliberadamente cortos (p. ej. "AV1 es
        # un:"). Solo descartamos cadenas realmente vacias; la presencia de
        # las cuatro opciones ya aporta la estructura necesaria.
        if key in seen or len(signature) < 4:
            continue
        seen.add(key)
        result.append(item)
    return result


def align_sections(items: list[ExtractedQuestion], specs: list[dict]) -> tuple[list[tuple[dict, ExtractedQuestion]], list[dict]]:
    items = dedupe_candidates(items)
    items.sort(key=lambda item: (item.page, item.order))
    expected = [(spec, number) for spec in specs for number in range(1, spec["count"] + 1)]

    # Alinear la secuencia impresa completa es mas robusto que confiar en los
    # reinicios detectados por OCR. Un 1 puede leerse como "i" y partir una
    # seccion, o un 2 como "422" y crear un salto. La subsecuencia comun mas
    # larga conserva el orden fisico y utiliza los reinicios oficiales del
    # manifiesto como autoridad, sin tomar preguntas de una seccion posterior.
    rows, columns = len(items), len(expected)
    scores = [[0] * (columns + 1) for _ in range(rows + 1)]
    for row in range(1, rows + 1):
        observed = items[row - 1].original_number
        for column in range(1, columns + 1):
            value = max(scores[row - 1][column], scores[row][column - 1])
            if observed == expected[column - 1][1]:
                value = max(value, scores[row - 1][column - 1] + 1)
            scores[row][column] = value

    matches: list[tuple[dict, ExtractedQuestion]] = []
    row, column = rows, columns
    while row and column:
        if items[row - 1].original_number == expected[column - 1][1] and scores[row][column] == scores[row - 1][column - 1] + 1:
            matches.append((expected[column - 1][0], items[row - 1]))
            row -= 1
            column -= 1
        elif scores[row - 1][column] >= scores[row][column - 1]:
            row -= 1
        else:
            column -= 1
    matches.reverse()
    matched = {(spec["key"], item.original_number) for spec, item in matches}

    # Segunda vista: cuando los reinicios 1..N si fueron reconocidos, la
    # segmentacion aporta preguntas que una LCS puede omitir al existir varios
    # tramos con la misma numeracion (casos practicos y reservas). Solo rellena
    # huecos y nunca reemplaza una coincidencia ya establecida.
    groups = []
    for segment in sorted({item.segment for item in items}):
        group = [item for item in items if item.segment == segment]
        if group:
            groups.append(group)
    cursor = 0
    for spec in specs:
        selected = groups[cursor] if cursor < len(groups) else []
        if selected:
            cursor += 1
        while spec["count"] > 5 and selected and max(item.original_number for item in selected) < spec["count"] * 0.65 and cursor < len(groups):
            selected = [*selected, *groups[cursor]]
            cursor += 1
        for item in selected:
            key = (spec["key"], item.original_number)
            if 1 <= item.original_number <= spec["count"] and key not in matched:
                matches.append((spec, item))
                matched.add(key)
    expected_position = {(spec["key"], number): index for index, (spec, number) in enumerate(expected)}
    matches.sort(key=lambda pair: expected_position[(pair[0]["key"], pair[1].original_number)])
    missing = [
        {"section": spec["key"], "number": number}
        for spec, number in expected
        if (spec["key"], number) not in matched
    ]
    return matches, missing


ANSWERS_2005 = (
    "a d a d a d b c d d d a c b d a d d c b a d a c b d d anulada c d c a c c a d c d b b d "
    "b a b a anulada b c c c d d b c d c c a c d c c b c b c anulada c d c b b c anulada c b d c c a c c b c "
    "anulada anulada b c a b c a a b c b b b d "
    "b c b d d c a d a b d c a d a b c d "
    "c d b c d a b c c b d d b anulada anulada d anulada b "
    "d a anulada d d c d a c b a b d c a c a a"
).split()


# Reparaciones visuales puntuales. Se usan solo cuando todas las lecturas OCR
# dejan el numero sin pregunta. El texto procede de la pagina indicada; no se
# modifica ninguna fuente. La pregunta grafica de Access se conserva como
# referencia auditable y queda excluida del banco jugable.
MANUAL_REPAIRS: dict[tuple[str, str, int], ExtractedQuestion] = {
    ("2005-libre", "case_v", 5): ExtractedQuestion(
        0, 5,
        "Se debate también sobre los problemas que a menudo ocasiona la conexión de servidores a switches cuando ambos se configuran en el modo de negociación automática o auto-negociación. Elija una de las siguientes afirmaciones para indicar qué es lo que se negocia entre el interfaz de red del servidor y el puerto del switch al que se le conecta.",
        ["El tamaño de ventana, el modo de transmisión y la velocidad.", "La velocidad y el control de flujo.", "La dirección IP y el modo de transmisión.", "La velocidad y el modo de transmisión."],
        10, "transcripcion_visual_verificada",
    ),
    ("2008-libre", "case_iii", 12): ExtractedQuestion(
        0, 12,
        "El código del Programa2 se ejecuta en un entorno basado en un:",
        ["Terminal en modo texto.", "Modo gráfico de ventanas.", "Servidor de aplicaciones en una plataforma .NET.", "Servidor de aplicaciones en un entorno J2EE."],
        5, "transcripcion_visual_verificada",
    ),
    ("2010-promocion-interna", "first_v", 16): ExtractedQuestion(
        0, 16,
        "Cuando utilizamos nuestra firma digital mediante una tarjeta criptográfica:",
        ["El certificado se instala en el navegador y se desinstala al extraer la tarjeta del lector.", "La tarjeta criptográfica realiza parte de las operaciones de cifrado y descifrado, las claves nunca salen de la tarjeta.", "El certificado digital está almacenado en el sitio web de la Autoridad de Certificación, y la tarjeta sólo realiza las operaciones de cifrado y descifrado.", "La operativa es similar a cuando se utiliza un pendrive o un disco USB, con la seguridad añadida que ofrece el tener que teclear el PIN de la tarjeta."],
        11, "transcripcion_visual_verificada",
    ),
    ("2010-promocion-interna", "first_v_reserve", 1): ExtractedQuestion(
        0, 1,
        "SPF (Sender Policy Framework) es:",
        ["Una protección contra los ataques de phising en la organización.", "Una protección contra ataques por ingeniería social.", "Una protección contra los virus y bombas lógicas.", "Una protección contra la falsificación de direcciones en el envío de correo electrónico."],
        12, "transcripcion_visual_verificada",
    ),
    ("2010-promocion-interna", "case_v", 20): ExtractedQuestion(
        0, 20,
        "Se desea obtener una relación de los billetes adquiridos por el comprador cuyo dni es 00000012. Los campos que se quieren obtener son: dni, nombre, origen, destino y fecha del viaje. Con Microsoft Access, ¿cuál de las siguientes consultas lo permite?:",
        ["Consulta gráfica A (véase el PDF original).", "Consulta gráfica B (véase el PDF original).", "Consulta gráfica C (véase el PDF original).", "Consulta gráfica D (véase el PDF original)."],
        13, "manual_graphic_reference",
    ),
    ("2016-libre", "case_iv", 1): ExtractedQuestion(
        0, 1,
        "De cara a las pertinentes configuraciones de firewall, de los siguientes, ¿cuál es un puerto utilizado, por defecto, por Salt?",
        ["4505", "389", "445", "3389"],
        7, "transcripcion_visual_verificada",
    ),
    ("2018-promocion-interna", "first_reserve", 1): ExtractedQuestion(
        0, 1,
        "Según la Ley Orgánica 3/2018, de Protección de Datos Personales y Garantía de los Derechos Digitales, ¿en cuál de las siguientes entidades los responsables y encargados del tratamiento NO están obligados a la designación de un Delegado de Protección de Datos?",
        ["Los establecimientos financieros de crédito.", "Los colegios profesionales.", "Las federaciones deportivas cuando traten datos de menores de edad.", "Los profesionales de la salud que ejerzan su actividad a título individual."],
        5, "transcripcion_visual_verificada",
    ),
}


def answer_mapping(exam: dict) -> tuple[dict[tuple[str, int], str], set[Path]]:
    mapping: dict[tuple[str, int], str] = {}
    used: set[Path] = set()
    template_specs = [exam.get("template"), *exam.get("extraTemplates", [])]
    if exam["id"] == "2005-libre":
        specs = exam["template"]["sections"]
        groups = []
        cursor = 0
        for spec in specs:
            groups.append(ANSWERS_2005[cursor:cursor + spec["count"]])
            cursor += spec["count"]
        if cursor != len(ANSWERS_2005):
            raise ValueError("Transcripción 2005 incompleta")
        used.add(SOURCE / exam["template"]["path"])
        for spec, values in zip(specs, groups):
            mapping.update({(spec["key"], number): answer for number, answer in enumerate(values, 1)})
        return mapping, used
    for template_spec in template_specs:
        if not template_spec:
            continue
        path = SOURCE / template_spec["path"]
        stream = answer_stream(path, template_spec["page"])
        groups = split_answers(stream, [spec["count"] for spec in template_spec["sections"]])
        used.add(path)
        for spec, values in zip(template_spec["sections"], groups):
            for number, answer in enumerate(values, 1):
                mapping[(spec["key"], number)] = answer
    return mapping, used


INTERNAL_OPTION_MARKER_RE = re.compile(r"(?:^|\s)[a-d][.)]\s+", re.IGNORECASE)


def extraction_quality_issue(prompt: str, options: list[str]) -> str | None:
    full_text = prompt + " " + " ".join(options)
    normalized = folded(full_text)
    if PAGE_REFERENCE_RE.search(full_text) or re.search(r"plantilla\s+(?:provisional|definitiva)\s+de\s+respuestas", normalized):
        return "Mezcla de página o plantilla detectada en la extracción"
    if any(INTERNAL_OPTION_MARKER_RE.search(option) for option in options):
        return "Una opción contiene marcadores de otra pregunta"
    if any(noise in normalized for noise in ("map map map", "5 1 1 1")):
        return "Ruido OCR detectado"
    if len(prompt) > 2400 or any(len(option) > 1200 for option in options):
        return "Extensión anómala compatible con mezcla de preguntas"
    return None


def status_for(question_text: str, answer: str | None, confidence: float, extraction: str, quality_issue: str | None = None) -> tuple[str, str, bool]:
    normalized = folded(question_text)
    if answer is None:
        return "missing_official_answer", "No hay plantilla oficial en la recopilación", False
    if answer == "anulada":
        return "annulled", "Anulada por la plantilla oficial", False
    if extraction == "manual_graphic_reference":
        return "ocr_review", "Las opciones son imágenes; se conserva la referencia al PDF y no entra en test", False
    if quality_issue:
        return "ocr_review", quality_issue, False
    for term, reason in OUTDATED.items():
        if term in normalized:
            return "outdated", reason, False
    if confidence < MIN_CLASSIFICATION_CONFIDENCE:
        return "classification_review", "Tema asignado con indicios insuficientes para el banco vigente", False
    return "valid", "Respuesta oficial enlazada y clasificación compatible con el programa vigente", True


def document_role(path: Path) -> str:
    name = folded(path.name)
    if path == OFFICIAL_CALL or "convocatoria" in name:
        return "convocatoria"
    if "respuesta" in name or "plant" in name:
        return "plantilla"
    if "cuestionario" in name:
        return "cuestionario"
    return "recopilatorio"


def build_inventory(imported_paths: set[Path]) -> list[dict]:
    documents = []
    for path in sorted(SOURCE.rglob("*.pdf"), key=lambda value: str(value).casefold()) + [OFFICIAL_CALL]:
        reader = PdfReader(str(path))
        relative = str(path.relative_to(ROOT))
        if path == OFFICIAL_CALL:
            status, note = "official_reference", "Programa y reglas oficiales usados para todo el banco"
        elif path in imported_paths:
            status, note = "imported", "Revisado e incorporado al banco o a sus respuestas"
        elif path.name == "CONVOCATORIA_2025.pdf":
            status, note = "duplicate_official_reference", "Misma huella que TAILI.pdf; TAILI.pdf prevalece"
        else:
            status, note = "reviewed_reference", "Inventariado y revisado; no contiene preguntas adicionales"
        year_match = re.search(r"20\d{2}", relative)
        documents.append({
            "id": hashlib.sha1(relative.encode()).hexdigest()[:12], "path": relative,
            "sha256": sha256(path), "pages": len(reader.pages), "bytes": path.stat().st_size,
            "textMode": "ocr_cache" if path != OFFICIAL_CALL and path.is_relative_to(SOURCE) and needs_ocr(path) else "embedded",
            "role": document_role(path), "year": int(year_match.group()) if year_match else None,
            "status": status, "note": note,
        })
    return documents


def write_sqlite(bank: dict) -> None:
    path = DATA / "bank.sqlite"
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE documents (id TEXT PRIMARY KEY, path TEXT, role TEXT, status TEXT, sha256 TEXT, pages INTEGER);
            CREATE TABLE questions (id TEXT PRIMARY KEY, exam_id TEXT, section TEXT, original_number INTEGER, prompt TEXT,
              options_json TEXT, correct_answer TEXT, block_id TEXT, topic_id TEXT, status TEXT, active INTEGER, source_page INTEGER);
            CREATE INDEX questions_topic_idx ON questions(topic_id);
            CREATE INDEX questions_exam_idx ON questions(exam_id);
        """)
        connection.executemany("INSERT INTO documents VALUES(?,?,?,?,?,?)", [(d["id"], d["path"], d["role"], d["status"], d["sha256"], d["pages"]) for d in bank["documents"]])
        connection.executemany("INSERT INTO questions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", [
            (q["id"], q["examId"], q["section"], q["originalNumber"], q["prompt"], json.dumps(q["options"], ensure_ascii=False), q["correctAnswer"], q["blockId"], q["topicId"], q["status"], int(q["active"]), q["source"]["page"])
            for q in bank["questions"]
        ])


def write_reports(bank: dict, coverage: list[dict]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    question_status = Counter(question["status"] for question in bank["questions"])
    active_topics = Counter(question["topicId"] for question in bank["questions"] if question["active"])
    lines = [
        "# Informe final del banco TAI AGE", "", f"Construido: {bank['meta']['builtAt']}",
        f"Referencia oficial: `{bank['meta']['officialCall']}`", "",
        "## Cobertura", "", f"- Exámenes: {len(bank['exams'])}", f"- PDF inventariados: {len(bank['documents'])}",
        f"- Preguntas esperadas: {sum(row['expected'] for row in coverage)}",
        f"- Preguntas extraídas: {len(bank['questions'])}", f"- Banco vigente activo: {sum(q['active'] for q in bank['questions'])}", "",
        "## Estado de las preguntas", "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in sorted(question_status.items()))
    lines += ["", "## Cobertura por examen", ""]
    lines.extend(f"- {row['examId']}: {row['extracted']}/{row['expected']} preguntas; {row['answers']} respuestas enlazadas; faltan {len(row['missing'])}" for row in coverage)
    lines += ["", "## Distribución vigente por tema", ""]
    lines.extend(f"- {topic['id']}: {active_topics.get(topic['id'], 0)}" for block in PROGRAM for topic in block["topics"])
    lines += ["", "## Criterio", "", "El modo vigente excluye anuladas, normativa expresamente derogada, preguntas sin respuesta oficial, ruido OCR y clasificaciones de baja confianza. Todas se conservan con trazabilidad en el explorador y en la cola de revisión; los tests históricos usan solo el subconjunto validado."]
    (REPORTS / "final-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTS / "coverage-matrix.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORTS / "review-queue.json").write_text(json.dumps([q for q in bank["questions"] if not q["active"]], ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORTS / "document-inventory.json").write_text(json.dumps(bank["documents"], ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    if not SOURCE.exists() or not OFFICIAL_CALL.exists():
        raise SystemExit("Faltan TAI AGE/ o TAILI.pdf")
    DATA.mkdir(parents=True, exist_ok=True)
    questions: list[dict] = []
    coverage: list[dict] = []
    imported_paths: set[Path] = set()
    exam_summaries = []
    for exam in EXAMS:
        answers, answer_paths = answer_mapping(exam)
        imported_paths.update(answer_paths)
        exam_missing: list[dict] = []
        extracted_count = 0
        for questionnaire in exam["questionnaires"]:
            path = SOURCE / questionnaire["path"]
            imported_paths.add(path)
            combined: dict[tuple[str, int], tuple[dict, ExtractedQuestion]] = {}
            for candidates in extract_question_sources(path):
                source_aligned, _ = align_sections(candidates, questionnaire["sections"])
                for spec, item in source_aligned:
                    combined.setdefault((spec["key"], item.original_number), (spec, item))
            for spec in questionnaire["sections"]:
                # Las reparaciones se recorren por la numeracion oficial y
                # solo rellenan huecos que las lecturas automaticas no cubren.
                for number in range(1, spec["count"] + 1):
                    repair = MANUAL_REPAIRS.get((exam["id"], spec["key"], number))
                    if repair:
                        combined.setdefault((spec["key"], number), (spec, repair))
            aligned = []
            missing = []
            for spec in questionnaire["sections"]:
                for number in range(1, spec["count"] + 1):
                    value = combined.get((spec["key"], number))
                    if value:
                        aligned.append(value)
                    else:
                        missing.append({"section": spec["key"], "number": number})
            exam_missing.extend({**item, "pdf": questionnaire["path"]} for item in missing)
            extracted_count += len(aligned)
            for spec, item in aligned:
                answer = answers.get((spec["key"], item.original_number))
                cleaned_prompt = clean(item.prompt)
                cleaned_options = [clean(option) for option in item.options]
                cleaned_item = ExtractedQuestion(
                    segment=item.segment,
                    original_number=item.original_number,
                    prompt=cleaned_prompt,
                    options=cleaned_options,
                    page=item.page,
                    extraction=item.extraction,
                    order=item.order,
                )
                topic, confidence, method = classify(cleaned_item, spec["blocks"])
                block = topic.split(".")[0]
                full_text = cleaned_prompt + " " + " ".join(cleaned_options)
                quality_issue = extraction_quality_issue(cleaned_prompt, cleaned_options)
                status, reason, active = status_for(full_text, answer, confidence, item.extraction, quality_issue)
                qid = f"{exam['id']}:{spec['key']}:{item.original_number}"
                questions.append({
                    "id": qid, "examId": exam["id"], "year": exam["year"], "access": exam["access"], "sitting": exam["sitting"],
                    "exercise": spec["exercise"], "section": spec["key"], "isReserve": spec["reserve"], "originalNumber": item.original_number,
                    "prompt": cleaned_prompt, "options": cleaned_options, "correctAnswer": answer,
                    "answerStatus": exam["answerStatus"] if answer else "missing", "blockId": block, "topicId": topic,
                    "classificationConfidence": round(confidence, 2), "classificationMethod": method,
                    "status": status, "statusReason": reason, "active": active, "duplicateOf": None,
                    "source": {"pdf": str(path.relative_to(ROOT)), "page": item.page, "answerPdf": str(next(iter(answer_paths)).relative_to(ROOT)) if answer_paths else None, "extraction": item.extraction},
                })
        expected = sum(spec["count"] for questionnaire in exam["questionnaires"] for spec in questionnaire["sections"])
        coverage.append({"examId": exam["id"], "expected": expected, "extracted": extracted_count, "answers": sum(1 for q in questions if q["examId"] == exam["id"] and q["correctAnswer"]), "missing": exam_missing})
        exam_summaries.append({key: exam[key] for key in ("id", "name", "year", "access", "sitting")})

    seen: dict[str, str] = {}
    for question in questions:
        normalized = re.sub(r"\W+", "", folded(question["prompt"]))
        if normalized in seen:
            question["duplicateOf"] = seen[normalized]
            if question["active"]:
                question["status"], question["statusReason"], question["active"] = "duplicate", "Duplicada literalmente; se conserva la primera aparición", False
        else:
            seen[normalized] = question["id"]

    bank = {
        "meta": {"schemaVersion": 2, "builtAt": date.today().isoformat(), "officialCall": "TAILI.pdf", "officialCallSha256": sha256(OFFICIAL_CALL), "sourceFolder": "TAI AGE/ (solo lectura)", "scoringNote": "Directa = aciertos - errores/3. La nota oficial requiere la transformación de la CPS."},
        "examConfig": {"durationMinutes": 120, "firstPartQuestions": 80, "firstPartReserve": 5, "practicalQuestions": 20, "practicalReserve": 5, "wrongPenalty": 1 / 3, "blankPenalty": 0, "officialMaximum": 100, "partMaximum": 50, "officialCutNote": "Cada parte exige 25/50 tras la transformación de la CPS; la puntuación directa mínima se publica por separado."},
        "program": PROGRAM, "documents": build_inventory(imported_paths), "exams": exam_summaries, "questions": questions,
    }
    (DATA / "bank.json").write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "program.json").write_text(json.dumps(PROGRAM, ensure_ascii=False, indent=2), encoding="utf-8")
    write_sqlite(bank)
    write_reports(bank, coverage)
    missing_total = sum(len(row["missing"]) for row in coverage)
    print(f"Banco: {len(questions)} preguntas; {sum(q['active'] for q in questions)} vigentes; {missing_total} huecos de extracción")


if __name__ == "__main__":
    main()
