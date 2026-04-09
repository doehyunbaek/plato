# Copyright and source notes

This repository mixes original app code with reused source texts.

## File-level overview

- `index.html`, `styles.css`, `app.js`, `scripts/build_data.py`: MIT-licensed original code.
- `data/symposium.json`, `data/symposium-data.js`: mixed-content data files built from third-party texts plus new normalization/alignment metadata.

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

## English translation

English translation source:

- TEI source: https://github.com/PerseusDL/canonical-greekLit/blob/master/data/tlg0059/tlg011/tlg0059.tlg011.perseus-eng2.xml
- Raw XML: https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/tlg0059/tlg011/tlg0059.tlg011.perseus-eng2.xml
- Translator: Walter Rangeley Maitland Lamb
- Edition: *Plato in Twelve Volumes*, Vol. 3 (1925)

This project uses the Lamb translation because the TEI markup preserves Stephanus section boundaries, which makes client-side Greek/English alignment possible.

Copyright note used here:

- The 1925 translation is treated as public domain in the United States.
- If you deploy or redistribute outside the United States, verify local copyright status before reuse.

## New material added in this repository

New material includes:

- the static web UI,
- build scripts,
- source cleanup/normalization,
- sectioning metadata,
- approximate phrase-level Greek↔English alignment metadata.

Because the alignment metadata is distributed together with and derived in part from the CC BY-SA Greek text, the generated data files should be reused conservatively under CC BY-SA 4.0 or later.

## Practical summary

- **Code**: MIT
- **Generated bilingual data**: conservatively treat as **CC BY-SA 4.0** (plus the jurisdiction note above for the Lamb translation)
