# Sentence Diagramm

Interactive sentence diagramming framework for English and German (starting point for other languages).

Highlights placement of sentence elements (subjects, verbs, objects, modifiers) using dependency parsing and visual diagrams.

## Features
- Support for English and German
- Interactive token table with highlighting
- Dependency tree visualization (text + visual)
- Side-by-side comparison mode for word order differences (e.g. English SVO vs German V2)
- Example sentences
- CLI for batch processing

## Run Locally

**Important:** The first time you must download the spaCy language models.

```bash
pixi install
pixi run download-models   # downloads en_core_web_sm + de_core_news_sm
pixi run app
```

If you see `OSError: [E050] Can't find model 'en_core_web_sm'` (or similar for German), just run the `download-models` task and restart the app.

## CLI

```bash
pixi run cli -- --lang en "The quick brown fox jumps over the lazy dog."
```

## Tech

- Streamlit for UI
- spaCy for parsing (en_core_web_sm, de_core_news_sm)
- Pixi for reproducible environment

Extensible parser framework in `src/parsers.py` — easy to add more languages.

## DoltHub

Credential registered under altustd. You can create a Dolt database on DoltHub (e.g. "sentence-examples") and use the CLI to version example sentences + parses.

## Next Steps / Extending

- Add more languages in `src/parsers.py`
- Improve diagram rendering (traditional Reed-Kellogg style, interactive graphs)
- Add export, more highlighting, corpus features
