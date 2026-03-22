"""Parse ONPE-style 'Listado de Candidatos' OCR/plain text into structured rows.

Layout is stable across parties: section headers ``Presentación …`` and table
headers ``N* DE LISTA ORDEN …``.  This module is intentionally regex- and
state-machine based (no LLM).
"""
from __future__ import annotations

import re
import unicodedata
from enum import Enum, auto
from typing import Any


class _Section(Enum):
    NONE = auto()
    FORMULA = auto()
    SENADO_UNICO = auto()
    PARLAMENTO = auto()
    SENADO_MULTI = auto()
    DIPUTADOS = auto()


# Canonical department names for ``scope`` (Title Case); longest first for prefix match.
_DEPT_CANONICAL = [
    "Residentes en el Extranjero",
    "Lima Metropolitana",
    "Lima Provincias",
    "La Libertad",
    "Madre de Dios",
    "San Martín",
    "Huancavelica",
    "Amazonas",
    "Apurímac",
    "Ayacucho",
    "Cajamarca",
    "Lambayeque",
    "Arequipa",
    "Callao",
    "Huánuco",
    "Junín",
    "Loreto",
    "Pasco",
    "Piura",
    "Puno",
    "Tacna",
    "Tumbes",
    "Ucayali",
    "Ica",
    "Cusco",
    "Áncash",
    "Moquegua",
]


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.casefold()


def _build_dept_prefixes() -> list[tuple[str, str]]:
    """Return (uppercase_folded_prefix, canonical_title) sorted by prefix length desc."""
    pairs: list[tuple[str, str]] = []
    for canon in _DEPT_CANONICAL:
        u = canon.upper()
        pairs.append((_fold(u), canon))
        # OCR often drops accents on the last vowel
        pairs.append(
            (_fold(
                u.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ",
                                                                                                                    "N")),
             canon),
        )
    # Dedup by folded prefix, keep longest canonical spelling
    by_fold: dict[str, str] = {}
    for folded, canon in pairs:
        if folded not in by_fold or len(canon) > len(by_fold[folded]):
            by_fold[folded] = canon
    out = [(k, v) for k, v in by_fold.items()]
    out.sort(key=lambda x: len(x[0]), reverse=True)
    return out


_DEPT_PREFIXES = _build_dept_prefixes()

_ROW_TYPES = frozenset({"TITULAR", "DESIGNADO", "CANDIDATO", "REEMPLAZANTE"})
_FORMULA_CARGOS = (
    "PRESIDENTE",
    "VICEPRESIDENTE",
    "SEGUNDO VICEPRESIDENTE",
    "REEMPLAZANTE",
)


def _normalize_lines(raw: str) -> list[str]:
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or re.match(r"^Página\s+\d+\s*$", s, re.I):
            continue
        s = re.sub(r"^Ccusco\b", "Cusco", s, flags=re.I)
        lines.append(s)
    return _merge_residentes_exterior(lines)


def _merge_residentes_exterior(lines: list[str]) -> list[str]:
    """Fix ``RESIDENTES EN EL`` / ``EXTRANJERO`` split across lines."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line == "EXTRANJERO" and out:
            prev = out[-1]
            if _fold(prev).rstrip().endswith(_fold("RESIDENTES EN EL")):
                out[-1] = prev + " EXTRANJERO"
                i += 1
                continue
        out.append(line)
        i += 1
    return out


def _section_from_presentacion(line: str, next_line: str | None) -> _Section | None:
    u = line.upper()
    n = (next_line or "").upper()
    if "PRESIDENCIAL" in u or (
            u.strip() in ("PRESENTACIÓN", "PRESENTACION") and "PRESIDENCIAL" in n
    ):
        return _Section.FORMULA
    if "SENADORES DISTRITO ELECTORAL ÚNICO" in u or "SENADORES DISTRITO ELECTORAL UNICO" in u:
        return _Section.SENADO_UNICO
    if "PARLAMENTO ANDINO" in u:
        return _Section.PARLAMENTO
    if "SENADORES DISTRITO ELECTORAL MÚLTIPLE" in u or "SENADORES DISTRITO ELECTORAL MULTIPLE" in u:
        return _Section.SENADO_MULTI
    if "DIPUTADOS" in u:
        return _Section.DIPUTADOS
    if u.rstrip() == "PRESENTACIÓN" or u.rstrip() == "PRESENTACION":
        n = (next_line or "").upper()
        if "SENADORES DISTRITO ELECTORAL MÚLTIPLE" in n or "SENADORES DISTRITO ELECTORAL MULTIPLE" in n:
            return _Section.SENADO_MULTI
    return None


def _strip_folded_prefix(line: str, prefix_fold: str) -> str | None:
    """If *line* starts with *prefix_fold* (accent-insensitive), return remainder."""
    if not _fold(line).startswith(prefix_fold):
        return None
    for i in range(len(line) + 1):
        if _fold(line[:i]) == prefix_fold:
            return line[i:].lstrip()
    return None


def _match_department(line: str) -> tuple[str, str] | None:
    """If *line* starts with a known department, return (canonical_scope, rest)."""
    folded_line = _fold(line)
    for prefix_fold, canon in _DEPT_PREFIXES:
        rest = _strip_folded_prefix(line, prefix_fold)
        if rest is not None:
            return (canon, rest)
    ref = _fold("RESIDENTES EN EL")
    if folded_line.startswith(ref):
        rest = _strip_folded_prefix(line, ref)
        if rest is not None:
            return ("Residentes en el Extranjero", rest)
    return None


def _split_trailing_type(rest: str) -> tuple[str, str] | None:
    """Return (name, TYPE) where TYPE is one of _ROW_TYPES."""
    rest = rest.rstrip()
    for t in sorted(_ROW_TYPES, key=len, reverse=True):
        suf = " " + t
        if rest.upper().endswith(suf):
            name = rest[: -len(suf)].strip()
            return (name, t)
    return None


def _parse_scoped_row(
        scope: str,
        rest: str,
        *,
        position: str,
) -> dict[str, Any] | None:
    """Parse ``list# order# name TYPE`` or ``list# name TYPE`` (missing order)."""
    rest = rest.strip()
    m = re.match(r"^(\d+)\s+(\d+)\s+(.+)$", rest)
    if m:
        list_no = int(m.group(1))
        order = int(m.group(2))
        body = m.group(3)
        st = _split_trailing_type(body)
        if not st:
            return None
        name, kind = st
        if kind == "DESIGNADO" and not name:
            return None
        if not name.strip():
            return None
        return {
            "name": _title_name(name),
            "position": position,
            "scope": scope,
            "list_order": order,
        }
    m = re.match(r"^(\d+)\s+(.+)$", rest)
    if m:
        list_no = int(m.group(1))
        body = m.group(2)
        st = _split_trailing_type(body)
        if not st:
            return None
        name, kind = st
        if kind != "REEMPLAZANTE":
            return None
        if not name.strip():
            return None
        return {
            "name": _title_name(name),
            "position": position,
            "scope": scope,
            "list_order": None,
        }
    return None


def _title_name(name: str) -> str:
    """Normalize whitespace; keep ONPE all-caps style as single title-ish string."""
    return " ".join(name.split())


def _parse_list_order_row(
        rest: str,
        *,
        position: str,
        scope: str,
) -> dict[str, Any] | None:
    """Senado único / Parlamento: ``list order name TYPE``."""
    m = re.match(r"^(\d+)\s+(\d+)\s+(.+)$", rest.strip())
    if not m:
        return None
    order = int(m.group(2))
    body = m.group(3)
    st = _split_trailing_type(body)
    if not st:
        return None
    name, kind = st
    if kind == "DESIGNADO" and not name:
        return None
    if not name.strip():
        return None
    return {
        "name": _title_name(name),
        "position": position,
        "scope": scope,
        "list_order": order,
    }


def _map_formula_cargo(cargo: str) -> str:
    u = cargo.upper().strip()
    if u == "PRESIDENTE":
        return "Presidente"
    if u in {"VICEPRESIDENTE", "SEGUNDO VICEPRESIDENTE", "REEMPLAZANTE"}:
        return "Vicepresidente"
    return "Vicepresidente"


def parse_listado_text(raw_text: str) -> list[dict[str, Any]]:
    """Return candidate dicts: name, position, scope (or None), list_order (or None)."""
    lines = _normalize_lines(raw_text)
    section = _Section.NONE
    in_table = False
    out: list[dict[str, Any]] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None

        if line.startswith("Presentación") or line.startswith("Presentacion"):
            new_sec = _section_from_presentacion(line, nxt)
            if new_sec:
                section = new_sec
                in_table = False
            i += 1
            continue

        if "N* DE FÓRMULA" in line or "N* DE FORMULA" in line or "NOMBRES Y APELLIDOS CARGO" in line:
            if section == _Section.FORMULA:
                in_table = True
            i += 1
            continue

        if "N* DE LISTA ORDEN NOMBRES" in line or "N* DE LISTA ORDEN" in line:
            if section in (
                    _Section.SENADO_UNICO,
                    _Section.PARLAMENTO,
                    _Section.SENADO_MULTI,
                    _Section.DIPUTADOS,
            ):
                in_table = True
            i += 1
            continue

        # Section metadata lines
        if line.startswith("Modalidad ") or line.startswith("Tipo de ") or line.startswith("ipo de "):
            i += 1
            continue
        if line.startswith("Posiciones de Designados") or re.match(r"^[A-ZÁÉÍÓÚÑ][^:]{0,40}:\s*[\d\-,\s]+$", line):
            i += 1
            continue
        if line.startswith("Datos Generales") or line.startswith("Nombre de la Organización"):
            i += 1
            continue

        # --- Formula (presidential ticket) ---
        if section == _Section.FORMULA and in_table:
            m1 = re.match(r"^(\d+)\s+(.+)$", line)
            if m1:
                rest = m1.group(2).strip()
                cargo_hit = None
                for cargo in _FORMULA_CARGOS:
                    if rest.upper().endswith(" " + cargo):
                        cargo_hit = cargo
                        name = rest[: -(len(cargo) + 1)].strip()
                        break
                if cargo_hit:
                    out.append({
                        "name": _title_name(name),
                        "position": _map_formula_cargo(cargo_hit),
                        "scope": "nacional",
                        "list_order": int(m1.group(1)),
                    })
                    i += 1
                    continue
            mnum = re.match(r"^(\d+)$", line)
            if mnum and nxt:
                name_line = nxt
                cargo_line = lines[i + 2] if i + 2 < len(lines) else None
                if cargo_line and cargo_line.upper() in _FORMULA_CARGOS:
                    out.append({
                        "name": _title_name(name_line),
                        "position": _map_formula_cargo(cargo_line),
                        "scope": "nacional",
                        "list_order": int(mnum.group(1)),
                    })
                    i += 3
                    continue
            i += 1
            continue

        # --- National list tables (senadores único, parlamento) ---
        if section in (_Section.SENADO_UNICO, _Section.PARLAMENTO) and in_table:
            pos = "Senador" if section == _Section.SENADO_UNICO else "Parlamento Andino"
            row = _parse_list_order_row(line, position=pos, scope="nacional")
            if row:
                out.append(row)
            i += 1
            continue

        # --- Scoped tables (senadores múltiple, diputados) ---
        if section in (_Section.SENADO_MULTI, _Section.DIPUTADOS) and in_table:
            pos = "Senador" if section == _Section.SENADO_MULTI else "Congresista"
            if "N* DE LISTA" in line and "ORDEN" in line and "NOMBRES" in line:
                i += 1
                continue
            dept = _match_department(line)
            if dept:
                scope, rest = dept
                row = _parse_scoped_row(scope, rest, position=pos)
                if row:
                    out.append(row)
                i += 1
                continue
            # Name continuation (OCR split): short ALL CAPS fragment
            if (
                    out
                    and line.isupper()
                    and 3 < len(line) < 72
                    and not re.match(r"^\d", line)
                    and "*" not in line
                    and "LISTA" not in line
            ):
                out[-1]["name"] = _title_name(out[-1]["name"] + " " + line)
                i += 1
                continue
            i += 1
            continue

        i += 1

    return out
