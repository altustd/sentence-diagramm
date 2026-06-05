import streamlit as st
from src.parsers import get_parser

st.set_page_config(page_title="Sentence Diagramm", layout="wide")
st.title("Sentence Diagramm")
st.markdown("Interactive diagramming for English & German — highlight placement of elements.")

lang = st.selectbox("Language", ["English", "German"])
sentence = st.text_area("Enter a sentence", "The cat sat on the mat.", height=100)

compare = st.checkbox("Compare with equivalent in the other language (for word order)", value=False)
other_sentence = ""
if compare:
    other_lang = "German" if lang == "English" else "English"
    other_sentence = st.text_area(f"Equivalent sentence in {other_lang}", "Gestern a\u00df ich einen Apfel." if lang == "English" else "Yesterday I ate an apple.", height=100)

if st.button("Diagram", type="primary"):
    try:
        parser = get_parser(lang)
        doc = parser.parse(sentence)
        
        st.subheader(f"{lang} Analysis")
        
        # Token table
        st.markdown("### Token Table (POS & Dependencies)")
        tokens_data = []
        for i, token in enumerate(doc):
            tokens_data.append({
                "#": i+1,
                "Text": token.text,
                "POS": token.pos_,
                "Dep": token.dep_,
                "Head": token.head.text
            })
        st.dataframe(tokens_data, use_container_width=True, hide_index=True)
        
        # Text diagram
        st.markdown("### Text Dependency Diagram")
        st.code(parser.to_text_diagram(doc))
        
        # Visual (displacy)
        try:
            from spacy import displacy
            html = displacy.render(doc, style="dep", page=False)
            st.components.v1.html(html, height=450, scrolling=True)
        except Exception as e:
            st.info("Full visual requires spaCy displacy (usually works after model download).")
        
        if compare and other_sentence:
            other_parser = get_parser(other_lang)
            other_doc = other_parser.parse(other_sentence)
            st.subheader(f"{other_lang} Analysis (for comparison)")
            st.code(other_parser.to_text_diagram(other_doc))
            st.dataframe([{"#":i+1, "Text":t.text, "POS":t.pos_, "Dep":t.dep_ , "Head":t.head.text} for i,t in enumerate(other_doc)], use_container_width=True, hide_index=True)
            
            st.info("**Key difference to explore:** English is rigidly SVO. German main clauses are often V2 (verb in second position), with more flexible word order due to case marking.")
    except OSError as e:
        if "Can't find model" in str(e):
            st.error("spaCy language model not found.")
            st.markdown("""
            **Fix:**
            
            1. Make sure you are in the project directory (`cd sentence-diagramm`)
            2. Run:
               ```bash
               pixi run download-models
               ```
            3. Restart the app (`pixi run app` or Ctrl+C and run again).
            
            This downloads the required models (`en_core_web_sm` and `de_core_news_sm`).
            """)
        else:
            st.error(f"Unexpected error loading parser: {e}")
            raise
