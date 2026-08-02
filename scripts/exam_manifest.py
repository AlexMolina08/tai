"""Inventario lógico de exámenes y estructura oficial de cada cuestionario."""

from __future__ import annotations

from pathlib import Path


def section(key: str, count: int, blocks: str, *, reserve: bool = False, exercise: str = "primera_parte") -> dict:
    return {"key": key, "count": count, "blocks": blocks.split(","), "reserve": reserve, "exercise": exercise}


GENERAL_80 = [
    section("first", 80, "I,II,III,IV"), section("first_reserve", 5, "I,II,III,IV", reserve=True),
    section("case_iii", 20, "III", exercise="supuesto_practico"), section("case_iii_reserve", 5, "III", reserve=True, exercise="supuesto_practico"),
    section("case_iv", 20, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 5, "IV", reserve=True, exercise="supuesto_practico"),
]
PI_50 = [
    section("first", 50, "I,II,III,IV"), section("first_reserve", 5, "I,II,III,IV", reserve=True),
    section("case_iii", 12, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"),
    section("case_iv", 12, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico"),
]


def questionnaire(path: str, sections: list[dict]) -> dict:
    return {"path": path, "sections": sections}


def template(path: str, page: int, sections: list[dict]) -> dict:
    return {"path": path, "page": page, "sections": sections}


EXAMS = [
    {"id": "2005-libre", "name": "OEP 2005 · ingreso libre", "year": 2005, "access": "libre", "sitting": "ordinario",
     "questionnaires": [
         questionnaire("2005 libre/TAI 2005-LI-PRIMER EJERCICIO- CUESTIONARIO.pdf", [section("first", 99, "I,II,III,IV")]),
         questionnaire("2005 libre/TAI 2005-LI-SEGUNDO EJERCICIO- CUESTIONARIO Y RESPUESTAS DE AMBOS.pdf", [section("case_iii", 18, "III", exercise="supuesto_practico"), section("case_iv", 18, "IV", exercise="supuesto_practico"), section("case_v", 18, "IV", exercise="supuesto_practico")]),
     ], "template": template("2005 libre/TAI 2005-LI-SEGUNDO EJERCICIO- CUESTIONARIO Y RESPUESTAS DE AMBOS.pdf", 14, [section("first", 99, "I,II,III,IV"), section("case_iii", 18, "III"), section("case_iv", 18, "IV"), section("case_v", 18, "IV")]), "answerStatus": "oficial"},
    {"id": "2006-libre", "name": "OEP 2006 · ingreso libre", "year": 2006, "access": "libre", "sitting": "ordinario",
     "questionnaires": [questionnaire("2006 libre/TAI 2006-LI-CUESTIONARIO Y RESPUESTAS.pdf", [section("first", 99, "I,II,III,IV"), section("case_iii", 18, "III", exercise="supuesto_practico"), section("case_iv", 18, "IV", exercise="supuesto_practico"), section("case_v", 18, "IV", exercise="supuesto_practico")])],
     "template": template("2006 libre/TAI 2006-LI-CUESTIONARIO Y RESPUESTAS.pdf", 27, [section("first", 99, "I,II,III,IV"), section("case_iii", 18, "III"), section("case_iv", 18, "IV"), section("case_v", 18, "IV")]), "answerStatus": "oficial"},
    {"id": "2007-libre", "name": "OEP 2007 · ingreso libre", "year": 2007, "access": "libre", "sitting": "ordinario",
     "questionnaires": [questionnaire("2007 libre/TAI 2007-LI-CUESTIONARIO Y RESPUESTAS.pdf", [section("first", 99, "I,II,III,IV"), section("case_iii", 18, "III", exercise="supuesto_practico"), section("case_iv", 18, "IV", exercise="supuesto_practico"), section("case_v", 18, "IV", exercise="supuesto_practico")])],
     "template": template("2007 libre/TAI 2007-LI-CUESTIONARIO Y RESPUESTAS.pdf", 25, [section("first", 99, "I,II,III,IV"), section("case_iii", 18, "III"), section("case_iv", 18, "IV"), section("case_v", 18, "IV")]), "answerStatus": "oficial_definitiva"},
]


def add(exam_id: str, name: str, year: int, access: str, questionnaires: list[dict], template_spec: dict | None, answer_status: str = "oficial_definitiva") -> None:
    EXAMS.append({"id": exam_id, "name": name, "year": year, "access": access, "sitting": "ordinario", "questionnaires": questionnaires, "template": template_spec, "answerStatus": answer_status})


L08_FIRST = [section("first", 50, "I,II"), section("first_iii", 50, "III"), section("first_iii_reserve", 3, "III", reserve=True), section("first_iv", 50, "IV"), section("first_iv_reserve", 3, "IV", reserve=True)]
L08_SECOND = [section("case_iii", 40, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 40, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
add("2008-libre", "OEP 2008 · ingreso libre", 2008, "libre", [questionnaire("2008 libre/TAI 2008-LI-PRIMER EJERCICIO- CUESTIONARIO.pdf", L08_FIRST), questionnaire("2008 libre/TAI 2008-LI-SEGUNDO EJERCICIO- CUESTIONARIO.pdf.pdf", L08_SECOND)], template("2008 libre/TAI 2008-LI-RESPUESTAS.pdf", 1, L08_FIRST), "oficial_definitiva")
# La plantilla de 2008 libre tiene la segunda parte en su página 2.
EXAMS[-1]["extraTemplates"] = [template("2008 libre/TAI 2008-LI-RESPUESTAS.pdf", 2, L08_SECOND)]

PI_OLD_FIRST = [section("first", 25, "I,II"), section("first_iii", 25, "III"), section("first_iii_reserve", 3, "III", reserve=True), section("first_iv", 25, "IV"), section("first_iv_reserve", 3, "IV", reserve=True), section("first_v", 25, "IV"), section("first_v_reserve", 3, "IV", reserve=True)]
PI_OLD_SECOND = [section("case_iii", 20, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 20, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico"), section("case_v", 20, "IV", exercise="supuesto_practico"), section("case_v_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
for year, q1, q2, ans in [
    (2008, "2008 pi/TAI 2008-PI-CUESTIONARIO 1 PARTE.pdf", "2008 pi/TAI 2008-PI-CUESTIONARIO 2 PARTE.pdf", "2008 pi/TAI 2008-PI-RESPUESTAS.pdf"),
    (2009, "2009 pi/TAI 2009-PI-CUESTIONARIO Y RESPUESTAS.pdf", None, "2009 pi/TAI 2009-PI-CUESTIONARIO Y RESPUESTAS.pdf"),
    (2010, "2010 pi/TAI 2010-PI-CUESTIONARIO 1 PARTE.pdf", "2010 pi/TAI 2010-PI-CUESTIONARIO 2 PARTE.pdf", "2010 pi/TAI 2010-PI-RESPUESTAS.pdf"),
]:
    questionnaires = [questionnaire(q1, PI_OLD_FIRST + (PI_OLD_SECOND if year == 2009 else []))]
    if q2:
        questionnaires.append(questionnaire(q2, PI_OLD_SECOND))
    add(f"{year}-promocion-interna", f"OEP {year} · promoción interna", year, "promocion_interna", questionnaires, template(ans, 25 if year == 2009 else 1, PI_OLD_FIRST))
    EXAMS[-1]["extraTemplates"] = [template(ans, 26 if year == 2009 else 2, PI_OLD_SECOND)]

PI14 = [section("first", 25, "I,II"), section("first_iii", 25, "III"), section("first_iii_reserve", 3, "III", reserve=True), section("first_iv", 25, "IV"), section("first_iv_reserve", 3, "IV", reserve=True), section("case_iii", 12, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 12, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
add("2014-promocion-interna", "OEP 2014 · promoción interna", 2014, "promocion_interna", [questionnaire("2014 pi/TAI 2014-PI-CUESTIONARIO.pdf", PI14)], template("2014 pi/TAI 2014-PI-RESPUESTAS.pdf", 1, PI14))

L15_FIRST = [section("first", 50, "I,II"), section("first_iii", 50, "III"), section("first_iii_reserve", 3, "III", reserve=True), section("first_iv", 50, "IV"), section("first_iv_reserve", 3, "IV", reserve=True)]
L15_SECOND = [section("case_iii", 40, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 40, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
for year in (2015, 2016):
    first = ([section("first", 50, "I,II"), section("first_reserve", 3, "I,II", reserve=True)] if year == 2016 else [section("first", 50, "I,II")]) + L15_FIRST[1:]
    add(f"{year}-libre", f"OEP {year} · ingreso libre", year, "libre", [questionnaire(f"{year} libre/TAI {year}-LI-PRIMER EJERCICIO- CUESTIONARIO.pdf", first), questionnaire(f"{year} libre/TAI {year}-LI-SEGUNDO EJERCICIO- CUESTIONARIO.pdf", L15_SECOND)], template(f"{year} libre/TAI {year}-LI-PRIMER EJERCICIO-RESPUESTAS.pdf", 1, first))
    EXAMS[-1]["extraTemplates"] = [template(f"{year} libre/TAI {year}-LI-SEGUNDO EJERCICIO- RESPUESTAS.pdf", 1, L15_SECOND)]

PI15_BASE = [section("first", 25, "I,II"), section("first_iii", 25, "III"), section("first_iii_reserve", 3, "III", reserve=True), section("first_iv", 25, "IV"), section("first_iv_reserve", 3, "IV", reserve=True), section("case_iii", 12, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 12, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
add("2015-promocion-interna", "OEP 2015 · promoción interna", 2015, "promocion_interna", [questionnaire("2015 pi/TAI 2015-PI-CUESTIONARIO.pdf", PI15_BASE)], template("2015 pi/TAI 2015-PI-RESPUESTAS.pdf", 1, PI15_BASE))
PI16 = [section("first", 25, "I,II"), section("first_reserve", 3, "I,II", reserve=True)] + PI15_BASE[1:]
add("2016-promocion-interna", "OEP 2016 · promoción interna", 2016, "promocion_interna", [questionnaire("2016 pi/TA%2520PI%252016(1).pdf", PI16)], template("2016 pi/Plant_def_TAI-P_ej_unico_2016_154AB89SD658.pdf", 1, PI16))

L17_FIRST = [section("first", 100, "I,II,III,IV"), section("first_reserve", 3, "I,II,III,IV", reserve=True)]
L17_SECOND = [section("case_iii", 30, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 30, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
add("2017-libre", "OEP 2017 · ingreso libre", 2017, "libre", [questionnaire("2017 libre/TAI 2017-LI-PRIMER EJERCICIO- CUESTIONARIO.pdf", L17_FIRST), questionnaire("2017 libre/TAI 2017-LI-SEGUNDO EJERCICIO- CUESTIONARIO.pdf", L17_SECOND)], template("2017 libre/TAI 2017-LI-PRIMER EJERCICIO-RESPUESTAS.pdf", 1, L17_FIRST))
PI17 = [section("first", 50, "I,II,III,IV"), section("first_reserve", 3, "I,II,III,IV", reserve=True), section("case_iii", 12, "III", exercise="supuesto_practico"), section("case_iii_reserve", 3, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 12, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 3, "IV", reserve=True, exercise="supuesto_practico")]
add("2017-promocion-interna", "OEP 2017 · promoción interna", 2017, "promocion_interna", [questionnaire("2017 pi/TAI 2017-PI-CUESTIONARIO.pdf", PI17)], template("2017 pi/TAI 2017-PI-RESPUESTAS.pdf", 1, PI17))

L18_FIRST = [section("first", 100, "I,II,III,IV"), section("first_reserve", 5, "I,II,III,IV", reserve=True)]
L18_SECOND = [section("case_iii", 30, "III", exercise="supuesto_practico"), section("case_iii_reserve", 5, "III", reserve=True, exercise="supuesto_practico"), section("case_iv", 30, "IV", exercise="supuesto_practico"), section("case_iv_reserve", 5, "IV", reserve=True, exercise="supuesto_practico")]
add("2018-libre", "OEP 2018 · ingreso libre", 2018, "libre", [questionnaire("2018 libre/TAI LIBRE 2018.pdf", L18_FIRST), questionnaire("2018 libre/TAI LIBRE 2018_SEGUNDO EJERCICIO.pdf", L18_SECOND)], template("2018 libre/TAI LIBRE 2018.pdf", 11, L18_FIRST), "oficial_provisional")
EXAMS[-1]["extraTemplates"] = [template("2018 libre/TAI LIBRE 2018_SEGUNDO EJERCICIO.pdf", 11, L18_SECOND)]
add("2018-promocion-interna", "OEP 2018 · promoción interna", 2018, "promocion_interna", [questionnaire("2018 pi/TAI PI 2018.pdf", PI_50)], template("2018 pi/TAI PI 2018.pdf", 11, PI_50), "oficial_provisional")

for year, folder, libre_name, pi_name in [
    (2019, "2019", "TAI IL 2019.pdf", "TAI PI 2019.pdf"),
    (2022, "2020_21_22", "TAI IL 2020_2021_2022.pdf", "TAI PI 2020_2021_2022.pdf"),
    (2024, "2024", "TAI IL 2024.pdf", "TAI PI 2024.pdf"),
]:
    for access, suffix, filename, specs in [("libre", "libre", libre_name, GENERAL_80), ("promocion_interna", "pi", pi_name, PI_50)]:
        path = f"{folder} {suffix}/{filename}"
        add(f"{year}-{access.replace('_', '-')}", f"OEP {year} · {'ingreso libre' if access == 'libre' else 'promoción interna'}", year, access, [questionnaire(path, specs)], template(path, -1, specs))

for exam_id, name, questionnaire_name, template_name, answer_status, sitting in [
    ("2025-libre-ordinario-a", "Convocatoria 2025 · ordinario (modelo A)", "Cuestionario TAI-L-ModeloA.pdf", "Plantilla respuestas TAI-L-A_act.pdf", "oficial_provisional_actualizada", "ordinario"),
    ("2025-libre-extraordinario", "Convocatoria 2025 · extraordinario (celebrado en 2026)", "cuestionario_TAI-L_ext_9QVS9NM8ER_154AB89SD658.pdf", "Plantilla_respuestas_prov_TAI-L_ext_2Y6UHS3CF2_154AB89SD658.pdf", "oficial_provisional", "extraordinario"),
]:
    add(exam_id, name, 2025, "libre", [questionnaire(f"2025/{questionnaire_name}", GENERAL_80)], template(f"2025/{template_name}", 1, GENERAL_80), answer_status)
    EXAMS[-1]["sitting"] = sitting

