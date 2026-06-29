from unittest.mock import patch

import pytest

from src.translate import translate


def test_translate_en_to_de():
    with patch("src.translate._SUPPORTED", {("en", "de"): type("T", (), {"translate": lambda self, text: "Die Katze sitzt auf der Matte."})()}):
        result = translate("The cat sat on the mat.", "en", "de")
    assert result == "Die Katze sitzt auf der Matte."


def test_translate_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        translate("   ", "en", "de")


def test_translate_rejects_unsupported_pair():
    with pytest.raises(ValueError, match="Unsupported"):
        translate("Hello", "en", "fr")


def test_translate_en_to_es():
    with patch("src.translate._SUPPORTED", {("en", "es"): type("T", (), {"translate": lambda self, text: "El gato se sentó en la alfombra."})()}):
        result = translate("The cat sat on the mat.", "en", "es")
    assert result == "El gato se sentó en la alfombra."