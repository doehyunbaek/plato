# Multilingual Plato reading

A client-side web app for reading Plato's *Symposium* in Greek with machine-generated translations.

## Features

- Multi-select languages shown side by side, including Greek, English, German, Korean, and Japanese
- Entire dialogue rendered at once by default
- Stephanus page jump navigation
- Approximate phrase-level hover alignment
- Client-side search across the currently displayed languages
- Static files only

## Run locally

Open `index.html` in a browser, or serve the directory with any static file server.

## Rebuild the data

```bash
python3 scripts/build_data.py
```

## Sources and copyright

See `COPYRIGHT.md`.

## Translation note

- Greek is the single source of truth.
- English, German, Korean, and Japanese are machine-generated directly from the Greek source during `scripts/build_data.py`.
- These translations are convenience translations and should not be treated as scholarly editions.
