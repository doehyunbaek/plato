# Copyright and source notes

This repository mixes original app code with reused source texts.

## File-level overview

- `index.html`, `styles.css`, `app.js`, `scripts/build_data.py`: MIT-licensed original code.
- `data/symposium.json`, `data/symposium-data.js`: mixed-content data files built from the Greek source text plus new normalization/alignment metadata and generated English/German/Korean/Japanese translations.
- `data/translation-cache.json`: build cache for generated translations.

## Greek text

Greek text was obtained from the Greek Wikisource page:

- Page: https://el.wikisource.org/wiki/%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)
- History: https://el.wikisource.org/w/index.php?title=%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)&action=history
- Site license notice: CC BY-SA 4.0

Conservative reuse approach used here:

- The Greek text is treated as CC BY-SA 4.0 material.
- Attribution is provided by linking to the page and its history.
- Changes have been made: source markup removal, whitespace normalization, splitting into Stephanus sections, and addition of phrase-alignment metadata.
- The resulting data files (`data/symposium.json` and `data/symposium-data.js`) should therefore be treated, at minimum, as containing CC BY-SA 4.0 material.

License URL: https://creativecommons.org/licenses/by-sa/4.0/

## Machine-generated translations

This repository also includes English, German, Korean, and Japanese translations generated during the build step.

- Single source of truth: the Greek Wikisource text described above.
- Build method: phrase-by-phrase machine translation directly from the Greek source using an online translation service endpoint from within `scripts/build_data.py`.
- These translations are provided as convenience reading aids only.
- They may contain inaccuracies, awkward phrasing, or interpretation errors.
- If you regenerate them yourself, you are responsible for checking any service terms that apply at build time.

## New material added in this repository

New material includes:

- the static web UI,
- build scripts,
- source cleanup/normalization,
- sectioning metadata,
- approximate phrase-level Greek↔translation alignment metadata,
- generated English/German/Korean/Japanese phrase-level translations derived directly from the Greek source.

Because the alignment metadata is distributed together with and derived in part from the CC BY-SA Greek text, the generated data files should be reused conservatively under CC BY-SA 4.0 or later.

## Practical summary

- **Code**: MIT
- **Generated multilingual data**: conservatively treat as **CC BY-SA 4.0**
