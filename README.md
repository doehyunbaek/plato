# Multilingual Plato reading

A client-side web app for reading Plato's *Symposium* in Greek and English.

## Features

- Greek side-by-side with English, German, Korean, or Japanese
- Entire dialogue rendered at once by default
- Stephanus page jump navigation
- Approximate phrase-level hover alignment
- Client-side search across Greek and all loaded translations
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

- English uses the public-domain W. R. M. Lamb translation.
- German, Korean, and Japanese are machine-generated from the English source during `scripts/build_data.py` and should be treated as convenience translations.
