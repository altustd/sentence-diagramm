import json
from pathlib import Path

import streamlit as st

from src.diagrams import get_baseline_words
from src.parsers import get_parser
from src.translate import translate

DATA_DIR = Path(__file__).parent / "data"
EXAMPLE_PAIRS = json.loads((DATA_DIR / "example_pairs.json").read_text(encoding="utf-8"))


def render_token_table(doc):
    tokens_data = [
        {
            "#": i + 1,
            "Text": token.text,
            "POS": token.pos_,
            "Dep": token.dep_,
            "Head": token.head.text,
        }
        for i, token in enumerate(doc)
    ]
    st.dataframe(tokens_data, use_container_width=True, hide_index=True)


def render_diagram(parser, doc, language: str, diagram_style: str):
    if "Classic" in diagram_style:
        st.markdown("#### Classic Reed-Kellogg diagram")
        try:
            svg = parser.to_classic_diagram_svg(doc)
            st.components.v1.html(svg, height=320, scrolling=False)
        except Exception as exc:
            st.error(f"Could not generate classic diagram: {exc}")
            st.code(parser.to_text_diagram(doc))
    else:
        st.markdown("#### Dependency tree")
        st.code(parser.to_text_diagram(doc))
        try:
            from spacy import displacy

            html = displacy.render(doc, style="dep", page=False)
            st.components.v1.html(html, height=420, scrolling=True)
        except Exception:
            st.info("Visual displacy view unavailable.")


def render_word_order_strip(en_doc, de_doc):
    en_words = get_baseline_words(en_doc)
    de_words = get_baseline_words(de_doc)
    left, right = st.columns(2)
    with left:
        st.markdown("**English baseline**")
        st.code(" | ".join(en_words) if en_words else "(none)")
    with right:
        st.markdown("**German baseline**")
        st.code(" | ".join(de_words) if de_words else "(none)")


st.set_page_config(page_title="Sentence Diagramm", layout="wide")
st.title("Sentence Diagramm")
st.markdown(
    "Enter an **English** sentence. The app **translates it to German**, then diagrams "
    "both side by side so you can see how word order changes after translation."
)

example_labels = ["Custom sentence"] + [pair["label"] for pair in EXAMPLE_PAIRS]
selected_label = st.selectbox("Example", example_labels, index=1)
selected_pair = None
if selected_label != "Custom sentence":
    selected_pair = next(pair for pair in EXAMPLE_PAIRS if pair["label"] == selected_label)

default_english = selected_pair["english"] if selected_pair else "The cat sat on the mat."
english_sentence = st.text_area("English sentence", default_english, height=90)

diagram_style = st.radio(
    "Diagram style",
    ["Classic Reed-Kellogg (traditional)", "Modern Dependency Tree"],
    horizontal=True,
    index=0,
)

show_token_tables = st.checkbox("Show token tables", value=False)

if st.button("Translate & Diagram", type="primary"):
    st.session_state["run"] = True
    st.session_state["english_sentence"] = english_sentence
    st.session_state.pop("german_sentence", None)

if st.session_state.get("run"):
    english = st.session_state.get("english_sentence", english_sentence).strip()
    if not english:
        st.warning("Enter an English sentence first.")
        st.stop()

    if "german_sentence" not in st.session_state:
        try:
            st.session_state["german_sentence"] = translate(english, "en", "de")
        except Exception as exc:
            st.error(f"Translation failed: {exc}")
            st.info("Check your network connection, or type the German sentence manually below.")
            st.session_state["german_sentence"] = (
                selected_pair["german"] if selected_pair else ""
            )

    st.subheader("Translation")
    german = st.text_area(
        "German translation (auto-generated — edit if the machine got it wrong)",
        st.session_state["german_sentence"],
        height=90,
    )
    st.session_state["german_sentence"] = german

    if not german.strip():
        st.warning("A German sentence is required before diagramming.")
        st.stop()

    try:
        en_parser = get_parser("English")
        de_parser = get_parser("German")
        en_doc = en_parser.parse(english)
        de_doc = de_parser.parse(german)

        st.subheader("Word order on the diagram baseline")
        render_word_order_strip(en_doc, de_doc)
        if selected_pair:
            st.caption(selected_pair["compare_note"])
        else:
            st.caption(
                "English diagrams use canonical subject | verb | object order. "
                "German diagrams follow surface word order (V2 where applicable)."
            )

        left, right = st.columns(2)
        with left:
            st.subheader("English")
            st.markdown(f"*{english}*")
            if show_token_tables:
                render_token_table(en_doc)
            render_diagram(en_parser, en_doc, "English", diagram_style)

        with right:
            st.subheader("German")
            st.markdown(f"*{german}*")
            if show_token_tables:
                render_token_table(de_doc)
            render_diagram(de_parser, de_doc, "German", diagram_style)
            st.caption(
                "German baseline preserves translated word order — the whole point of the exercise."
            )

    except OSError as e:
        if "Can't find model" in str(e):
            st.error("spaCy language model not found.")
            st.markdown(
                """
                **Fix:** run `pixi install` (models install automatically) or:

                ```bash
                pixi run download-models
                ```

                Then restart the app.
                """
            )
        else:
            st.error(f"Unexpected error loading parser: {e}")
            raise