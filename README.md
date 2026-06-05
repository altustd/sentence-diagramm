# Sentence Diagramm

Interactive sentence diagramming framework for English and German (starting point for other languages).

Highlights placement of sentence elements (subjects, verbs, objects, modifiers) using dependency parsing and visual diagrams.

## Features
- Support for English and German
- Interactive token table with highlighting
- Dependency tree visualization
- Side-by-side comparison mode for word order differences
- Example sentences
- CLI for batch processing

## Run Locally

```bash
pixi install
pixi run download-models
pixi run app
```

## CLI

```bash
pixi run cli -- --lang en "The quick brown fox jumps over the lazy dog."
```

## Tech

- Streamlit for UI
- spaCy for parsing (en_core_web_sm, de_core_news_sm)
- Pixi for environment

Extensible parser framework in `src/parsers.py`.

## DoltHub

Credential registered under altustd. Future: versioned example corpora.