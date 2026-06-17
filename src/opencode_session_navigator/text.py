from __future__ import annotations

import re

DESCRIPTION_PLACEHOLDER = "Sin descripción disponible."
SUMMARY_PLACEHOLDER = "Sin resumen disponible."

ANSI_SEQUENCE_RE = re.compile(
    r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    r"|\x1b\[[0-?]*[ -/]*[@-~]"
    r"|\x1b[@-_]"
)
CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def normalize_text(value: str | None) -> str:
    """Normaliza espacios para mostrar y buscar texto de sesiones."""
    if value is None:
        return ""
    without_sequences = ANSI_SEQUENCE_RE.sub("", value)
    without_controls = CONTROL_CHARACTER_RE.sub("", without_sequences)
    return " ".join(without_controls.split())


def normalize_search_text(value: str | None) -> str:
    """Normaliza texto para búsquedas simples en memoria."""
    return normalize_text(value).casefold()


def truncate_text(value: str, max_length: int) -> str:
    """Recorta texto largo y usa puntos suspensivos ASCII cuando hay truncado."""
    if max_length < 1:
        raise ValueError("El límite de truncado debe ser mayor a cero.")

    normalized = normalize_text(value)
    if len(normalized) <= max_length:
        return normalized

    if max_length <= 3:
        return "." * max_length

    return normalized[: max_length - 3].rstrip() + "..."


def first_useful_text(texts: tuple[str, ...] | list[str]) -> str | None:
    """Devuelve el primer texto no vacío luego de normalizar espacios."""
    for text in texts:
        normalized = normalize_text(text)
        if normalized:
            return normalized
    return None


def last_useful_text(texts: tuple[str, ...] | list[str]) -> str | None:
    """Devuelve el último texto no vacío luego de normalizar espacios."""
    for text in reversed(texts):
        normalized = normalize_text(text)
        if normalized:
            return normalized
    return None


def derive_description(user_texts: tuple[str, ...] | list[str], max_length: int) -> str:
    """Construye la descripción v1 desde el primer texto de usuario disponible."""
    source = first_useful_text(user_texts) or DESCRIPTION_PLACEHOLDER
    return truncate_text(source, max_length)


def derive_summary(
    assistant_texts: tuple[str, ...] | list[str],
    user_texts: tuple[str, ...] | list[str],
    max_length: int,
) -> str:
    """Construye un resumen heurístico barato sin LLM ni servicios externos."""
    source = (
        last_useful_text(assistant_texts) or first_useful_text(user_texts) or SUMMARY_PLACEHOLDER
    )
    return truncate_text(source, max_length)
