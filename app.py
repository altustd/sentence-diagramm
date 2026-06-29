import json
from pathlib import Path

import streamlit as st

from src.diagrams import get_baseline_words
from src.parsers import get_parser
from src.translate import TARGET_LANGUAGES, translate

DATA_DIR = Path(__file__).parent / "data"
EXAMPLE_PAIRS = json.loads((DATA_DIR / "example_pairs.json").read_text(encoding="utf-8"))

TARGET_OPTIONS = {
    "de": "German",
    "es": "Spanish",
}


PAIR_KEYS = {"de": "german", "es": "spanish"}


def fallback_translation(pair: dict | None, code: str) -> str:
    if not pair:
        return ""
    return pair.get(PAIR_KEYS[code], "")


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


def render_diagram(parser, doc, diagram_style: str):
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


def render_baseline_comparison(en_doc, translated_docs: dict[str, object]):
    rows = [("English", " | ".join(get_baseline_words(en_doc)))]
    for code, doc in translated_docs.items():
        rows.append((TARGET_OPTIONS[code], " | ".join(get_baseline_words(doc))))
    for label, text in rows:
        st.markdown(f"**{label} baseline**")
        st.code(text or "(none)")


st.set_page_config(page_title="Sentence Diagramm", layout="wide")
st.title("Sentence Diagramm")
st.markdown(
    "Enter an **English** sentence. The app **translates** it, then diagrams English "
    "and each translation side by side so you can see how **word order** changes."
)

example_labels = ["Custom sentence"] + [pair["label"] for pair in EXAMPLE_PAIRS]
selected_label = st.selectbox("Example", example_labels, index=1)
selected_pair = None
if selected_label != "Custom sentence":
    selected_pair = next(pair for pair in EXAMPLE_PAIRS if pair["label"] == selected_label)

default_english = selected_pair["english"] if selected_pair else "The cat sat on the mat."
english_sentence = st.text_area("English sentence", default_english, height=90)

target_codes = st.multiselect(
    "Translate and diagram into",
    options=list(TARGET_OPTIONS.keys()),
    default=["de", "es"],
    format_func=lambda code: TARGET_OPTIONS[code],
)

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
    st.session_state["target_codes"] = target_codes
    for code in target_codes:
        st.session_state.pop(f"translation_{code}", None)

if st.session_state.get("run"):
    english = st.session_state.get("english_sentence", english_sentence).strip()
    active_targets = st.session_state.get("target_codes", target_codes)

    if not english:
        st.warning("Enter an English sentence first.")
        st.stop()
    if not active_targets:
        st.warning("Select at least one target language.")
        st.stop()

    translations: dict[str, str] = {}
    for code in active_targets:
        key = f"translation_{code}"
        if key not in st.session_state:
            try:
                st.session_state[key] = translate(english, "en", code)
            except Exception as exc:
                st.error(f"{TARGET_OPTIONS[code]} translation failed: {exc}")
                st.session_state[key] = fallback_translation(selected_pair, code)
        translations[code] = st.text_area(
            f"{TARGET_OPTIONS[code]} translation (auto-generated — edit if needed)",
            st.session_state[key],
            height=90,
            key=f"textarea_{code}",
        )
        st.session_state[key] = translations[code]

    if not all(translations[code].strip() for code in active_targets):
        st.warning("Each target language needs a non-empty sentence.")
        st.stop()

    try:
        en_parser = get_parser("English")
        en_doc = en_parser.parse(english)

        st.subheader("Word order on the diagram baseline")
        translated_docs = {
            code: get_parser(TARGET_OPTIONS[code]).parse(translations[code])
            for code in active_targets
        }
        render_baseline_comparison(en_doc, translated_docs)
        if selected_pair:
            st.caption(selected_pair["compare_note"])

        columns = st.columns(1 + len(active_targets))
        with columns[0]:
            st.subheader("English")
            st.markdown(f"*{english}*")
            if show_token_tables:
                render_token_table(en_doc)
            render_diagram(en_parser, en_doc, diagram_style)

        for idx, code in enumerate(active_targets, start=1):
            label = TARGET_OPTIONS[code]
            parser = get_parser(label)
            doc = translated_docs[code]
            with columns[idx]:
                st.subheader(label)
                st.markdown(f"*{translations[code]}*")
                if show_token_tables:
                    render_token_table(doc)
                render_diagram(parser, doc, diagram_style)
                if code == "de":
                    st.caption("German baseline preserves surface/V2 word order.")
                elif code == "es":
                    st.caption("Spanish baseline follows surface reading order.")

    except OSError as e:
        if "Can't find model" in str(e):
            st.error("spaCy language model not found.")
            st.markdown("Run `pixi install` locally, or redeploy on Streamlit Cloud after updating `requirements.txt`.")
        else:
            st.error(f"Unexpected error loading parser: {e}")
            raise