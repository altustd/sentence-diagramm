# Sentence Diagramm

Interactive sentence diagramming for English, German, and Spanish.

Enter an English sentence → the app **translates** it → diagrams English and each translation **side by side** with baseline word-order comparison. Built for language study: see how German V2 and Spanish surface order differ from English after translation.

## Features

- **Translate & Diagram** workflow (English → German / Spanish)
- Classic **Reed-Kellogg** SVG diagrams + modern dependency trees
- German **V2 surface word order** on the baseline
- Spanish **UD parsing** (reflexives, `obl`, copula)
- Editable machine translations
- Example sentence pairs
- CLI for quick parsing checks

## Run Locally

```bash
pixi install          # installs spaCy models + dependencies
pixi run app            # http://localhost:8501
```

Models install automatically via `pixi install`. If needed manually:

```bash
pixi run download-models
```

## Streamlit Cloud Deploy

The repo includes `requirements.txt` and `streamlit_app.py` for [Streamlit Community Cloud](https://share.streamlit.io/):

1. Go to **share.streamlit.io** → **New app**
2. Repo: `altustd/sentence-diagramm`, branch `main`
3. Main file: `streamlit_app.py`
4. Deploy (first build takes a few minutes — three spaCy models)

Translation requires network access at runtime.

## CLI

```bash
pixi run cli -- --lang en "The cat sat on the mat."
pixi run cli -- --lang de "Die Katze sitzt auf der Matte."
pixi run cli -- --lang es "El gato se sentó en la alfombra."
```

## Tests

```bash
pixi run test
```

## Tech

- Streamlit UI
- spaCy (`en_core_web_sm`, `de_core_news_sm`, `es_core_news_sm`)
- deep-translator (Google Translate API)
- Pixi for local dev; pip `requirements.txt` for cloud deploy