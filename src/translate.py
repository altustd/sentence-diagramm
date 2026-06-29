"""English ↔ German/Spanish translation for the study workflow."""

from __future__ import annotations

from deep_translator import GoogleTranslator

_SUPPORTED = {
    ("en", "de"): GoogleTranslator(source="en", target="de"),
    ("de", "en"): GoogleTranslator(source="de", target="en"),
    ("en", "es"): GoogleTranslator(source="en", target="es"),
    ("es", "en"): GoogleTranslator(source="es", target="en"),
}

TARGET_LANGUAGES = {
    "de": "German",
    "es": "Spanish",
}


def translate(text: str, source: str, target: str) -> str:
    """Translate *text* between English, German (de), and Spanish (es)."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Cannot translate an empty sentence.")

    key = (source, target)
    if key not in _SUPPORTED:
        raise ValueError(f"Unsupported translation pair: {source} → {target}")

    result = _SUPPORTED[key].translate(cleaned)
    if not result:
        raise RuntimeError("Translation service returned an empty result.")
    return result