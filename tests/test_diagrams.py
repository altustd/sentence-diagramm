import spacy
import pytest

from src.diagrams import generate_classic_diagram_svg, get_baseline_words


@pytest.fixture(scope="module")
def en_nlp():
    return spacy.load("en_core_web_sm")


@pytest.fixture(scope="module")
def de_nlp():
    return spacy.load("de_core_news_sm")


def _svg_contains_roles(doc, *roles):
    svg = generate_classic_diagram_svg(doc)
    for role in roles:
        assert f">{role}</text>" in svg or f'>{role} ' in svg or role in svg


def test_english_simple_sentence(en_nlp):
    doc = en_nlp("The cat sat on the mat.")
    _svg_contains_roles(doc, "cat", "sat")


def test_german_simple_sentence(de_nlp):
    doc = de_nlp("Die Katze sitzt auf der Matte.")
    _svg_contains_roles(doc, "Katze", "sitzt", "auf", "Matte")


def test_german_v2_word_order(de_nlp):
    doc = de_nlp("Gestern aß ich einen Apfel.")
    svg = generate_classic_diagram_svg(doc)
    for word in ("Gestern", "aß", "ich", "Apfel"):
        assert word in svg
    gestern_idx = svg.index(">Gestern</text>")
    ass_idx = svg.index(">aß</text>")
    ich_idx = svg.index(">ich</text>")
    apfel_idx = svg.index(">Apfel</text>")
    assert gestern_idx < ass_idx < ich_idx < apfel_idx


def test_german_dative_and_accusative(de_nlp):
    doc = de_nlp("Der Mann gibt dem Kind einen Ball.")
    _svg_contains_roles(doc, "Mann", "gibt", "Kind", "Ball")


def test_german_predicate_complement(de_nlp):
    doc = de_nlp("Das Buch ist interessant.")
    _svg_contains_roles(doc, "Buch", "ist", "interessant")


def test_baseline_words_v2_pair(en_nlp, de_nlp):
    en_doc = en_nlp("Yesterday I ate an apple.")
    de_doc = de_nlp("Gestern aß ich einen Apfel.")
    assert get_baseline_words(en_doc) == ["I", "ate", "apple"]
    assert get_baseline_words(de_doc) == ["Gestern", "aß", "ich", "Apfel"]


def test_baseline_words_perfect_tense(de_nlp):
    doc = de_nlp("Gestern habe ich einen Apfel gegessen.")
    assert get_baseline_words(doc) == ["Gestern", "habe gegessen", "ich", "Apfel"]