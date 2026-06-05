import streamlit as st
import spacy
from src.parsers import get_parser

st.set_page_config(page_title="Sentence Diagramm", layout="wide")
st.title("Sentence Diagramm")
st.markdown("Interactive diagramming for English & German — highlight placement of elements.")

col1, col2 = st.columns(2)
with col1:
    lang = st.selectbox("Language", ["English", "German"])
    sentence = st.text_area("Enter a sentence", "The cat sat on the mat.", height=100)
    compare = st.checkbox("Compare with other language", value=False)
with col2:
    if compare:
        other_lang = "German" if lang == "English" else "English"
        other_sentence = st.text_area(f"Equivalent in {other_lang}", "", height=100)

if st.button("Diagram", type="primary"):
    parser = get_parser(lang)
    doc = parser.parse(sentence)
    
    st.subheader(f"{lang} Parse")
    
    # Token table with highlight
    st.markdown("### Tokens (click to highlight in mind)")
    tokens_data = []
    for i, token in enumerate(doc):
        tokens_data.append({
            "#": i,
            "Text": token.text,
            "POS": token.pos_,
            "Dep": token.dep_,
            "Head": token.head.text
        })
    st.dataframe(tokens_data, use_container_width=True)
    
    # Simple dep diagram using text
    st.markdown("### Dependency View")
    st.code(parser.to_text_diagram(doc))
    
    # Try displacy if available
    try:
        from spacy import displacy
        html = displacy.render(doc, style="dep", page=False)
        st.components.v1.html(html, height=400, scrolling=True)
    except:
        st.info("Install spacy for full visual.")
    
    if compare and other_sentence:
        other_parser = get_parser(other_lang)
        other_doc = other_parser.parse(other_sentence)
        st.subheader(f"{other_lang} Parse")
        st.code(other_parser.to_text_diagram(other_doc))
        st.dataframe([{"#":i, "Text":t.text, "POS":t.pos_, "Dep":t.dep_} for i,t in enumerate(other_doc)])
        
        st.markdown("**Word order note:** English is typically SVO. German main clauses are V2 (verb second).")
