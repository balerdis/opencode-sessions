from __future__ import annotations

import pytest

from opencode_session_navigator.text import (
    DESCRIPTION_PLACEHOLDER,
    SUMMARY_PLACEHOLDER,
    derive_description,
    derive_summary,
    normalize_search_text,
    normalize_text,
    truncate_text,
)


def test_normalize_text_compacta_espacios() -> None:
    assert normalize_text("  hola\n\tmundo  ") == "hola mundo"
    assert normalize_search_text("Título Útil") == "título útil"


def test_normalize_text_elimina_secuencias_de_control() -> None:
    assert normalize_text("\x1b[31mError\x1b[0m\x07\nnormal") == "Error normal"
    assert normalize_search_text("\x1b]0;título\x07Visible") == "visible"


def test_truncate_text_termina_en_tres_puntos_si_recorta() -> None:
    assert truncate_text("abcdef", 5) == "ab..."
    assert truncate_text("abc", 5) == "abc"
    assert truncate_text("abcdef", 3) == "..."
    assert truncate_text("abcdef", 2) == ".."
    assert truncate_text("abcdef", 1) == "."


def test_truncate_text_rechaza_limite_invalido() -> None:
    with pytest.raises(ValueError, match="mayor a cero"):
        truncate_text("abc", 0)


def test_derive_description_usa_primer_texto_de_usuario() -> None:
    assert derive_description(("", " primer prompt ", "segundo"), 20) == "primer prompt"


def test_derive_description_usa_placeholder_si_faltan_textos() -> None:
    assert derive_description(("",), 80) == DESCRIPTION_PLACEHOLDER


def test_derive_summary_usa_ultimo_assistant_y_fallback_barato() -> None:
    assert derive_summary(("primero", " último "), ("prompt",), 80) == "último"
    assert derive_summary((), ("prompt disponible",), 80) == "prompt disponible"
    assert derive_summary((), (), 80) == SUMMARY_PLACEHOLDER
