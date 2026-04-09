#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import date
from pathlib import Path

GREEK_SOURCE_URL = "https://el.wikisource.org/w/index.php?title=%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)&action=raw"
GREEK_PAGE_URL = "https://el.wikisource.org/wiki/%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)"
GREEK_HISTORY_URL = "https://el.wikisource.org/w/index.php?title=%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)&action=history"
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&dt=t"
OUTPUT_JSON = Path("data/symposium.json")
OUTPUT_JS = Path("data/symposium-data.js")
TRANSLATION_CACHE = Path("data/translation-cache.json")

TARGET_LANGUAGES = OrderedDict(
    {
        "en": {
            "label": "English",
            "nativeLabel": "English",
            "type": "machine-generated",
            "note": "Machine-generated from the Greek source during the build step.",
        },
        "de": {
            "label": "German",
            "nativeLabel": "Deutsch",
            "type": "machine-generated",
            "note": "Machine-generated from the Greek source during the build step.",
        },
        "ko": {
            "label": "Korean",
            "nativeLabel": "한국어",
            "type": "machine-generated",
            "note": "Machine-generated from the Greek source during the build step.",
        },
        "ja": {
            "label": "Japanese",
            "nativeLabel": "日本語",
            "type": "machine-generated",
            "note": "Machine-generated from the Greek source during the build step.",
        },
    }
)

STRONG_BREAK = re.compile(r"(?<=[\.;:!?·])\s+")
ROMAN_HEADING = re.compile(r"\b[IVXLCDM]+\.")
SECTION_MARKER = re.compile(r"(\{\{χ\|[^}]+\}\})")
MARKER_VALUE = re.compile(r"\{\{χ\|([^}]+)\}\}")


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def clean_wikisource_greek(text: str) -> str:
    text = text.split("[[Κατηγορία:")[0]
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = text.replace("'''", "")
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = ROMAN_HEADING.sub(" ", text)
    return normalize_whitespace(text)


def repair_greek_sections(sections: OrderedDict[str, str]) -> OrderedDict[str, str]:
    if "207b" in sections and "207c" not in sections:
        split_on = "τὰ δὲ θηρία τίς αἰτία οὕτως ἐρωτικῶς διατίθεσθαι;"
        text = sections["207b"]
        if split_on in text:
            before, after = text.split(split_on, 1)
            sections["207b"] = before.strip()
            sections["207c"] = f"{split_on} {after.strip()}".strip()

    desired_order = [f"{page}{letter}" for page in range(172, 224) for letter in "abcde"]
    return OrderedDict((key, sections[key]) for key in desired_order if key in sections)


def parse_greek_sections(raw_text: str) -> OrderedDict[str, str]:
    raw_text = raw_text.split("[[Κατηγορία:")[0]
    sections: OrderedDict[str, str] = OrderedDict()
    current = None

    for part in SECTION_MARKER.split(raw_text):
        marker = MARKER_VALUE.fullmatch(part)
        if marker:
            current = marker.group(1)
            sections[current] = ""
        elif current:
            sections[current] += part

    cleaned = OrderedDict((key, clean_wikisource_greek(value)) for key, value in sections.items())
    return repair_greek_sections(cleaned)


def split_long_segment(segment: str, max_words: int = 28) -> list[str]:
    words = segment.split()
    if len(words) <= max_words:
        return [segment]

    midpoint = len(words) // 2
    return [" ".join(words[:midpoint]), " ".join(words[midpoint:])]


def merge_short_segments(segments: list[str], min_words: int = 4) -> list[str]:
    merged: list[str] = []
    for index, segment in enumerate(segments):
        if len(segment.split()) < min_words:
            if merged:
                merged[-1] = f"{merged[-1]} {segment}".strip()
            elif index + 1 < len(segments):
                segments[index + 1] = f"{segment} {segments[index + 1]}".strip()
            else:
                merged.append(segment)
        else:
            merged.append(segment)
    return merged


def greek_phrase_chunks(text: str) -> list[str]:
    base_segments = [part.strip() for part in STRONG_BREAK.split(text.strip()) if part.strip()]
    chunks: list[str] = []
    for segment in base_segments:
        chunks.extend(split_long_segment(segment))
    chunks = merge_short_segments(chunks)
    return chunks or [text.strip()]


def load_translation_cache() -> dict:
    if TRANSLATION_CACHE.exists():
        return json.loads(TRANSLATION_CACHE.read_text())
    return {}


def save_translation_cache(cache: dict) -> None:
    TRANSLATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATION_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")


def cache_key(text: str, target_lang: str) -> str:
    return hashlib.sha1(f"{target_lang}\u241f{text}".encode("utf-8")).hexdigest()


def translate_text(text: str, target_lang: str) -> str:
    query = urllib.parse.urlencode({"tl": target_lang, "q": text})
    url = f"{GOOGLE_TRANSLATE_URL}&{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(request).read().decode("utf-8")
    payload = json.loads(raw)
    return "".join(part[0] for part in payload[0])


def translate_lines(lines: list[str], target_lang: str, cache: dict) -> list[str]:
    output: list[str] = []
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_size = 0
    max_chars = 1200

    for line in lines:
        addition = len(line) + (1 if current_batch else 0)
        if current_batch and current_size + addition > max_chars:
            batches.append(current_batch)
            current_batch = [line]
            current_size = len(line)
        else:
            current_batch.append(line)
            current_size += addition
    if current_batch:
        batches.append(current_batch)

    for batch in batches:
        joined = "\n".join(batch)
        joined_key = cache_key(joined, target_lang)

        if joined_key in cache:
            translated = cache[joined_key]
        else:
            translated = translate_text(joined, target_lang)
            cache[joined_key] = translated

        split_lines = translated.split("\n")
        if len(split_lines) == len(batch):
            normalized_batch = [normalize_whitespace(line) for line in split_lines]
            output.extend(normalized_batch)
            for source_line, translated_line in zip(batch, normalized_batch):
                cache[cache_key(source_line, target_lang)] = translated_line
            continue

        for line in batch:
            line_key = cache_key(line, target_lang)
            if line_key in cache:
                translated_line = cache[line_key]
            else:
                translated_line = translate_text(line, target_lang)
                cache[line_key] = translated_line
            output.append(normalize_whitespace(translated_line))

    return output


def page_id(section_id: str) -> str:
    return re.match(r"\d+", section_id).group(0)  # type: ignore[union-attr]


def build_dataset() -> dict:
    greek_sections = parse_greek_sections(fetch_text(GREEK_SOURCE_URL))
    cache = load_translation_cache()
    sections = []

    prepared_sections = []
    for order, section_id in enumerate(greek_sections.keys()):
        greek_text = greek_sections[section_id]
        greek_phrases = greek_phrase_chunks(greek_text)
        prepared_sections.append(
            {
                "id": section_id,
                "page": page_id(section_id),
                "order": order,
                "greek": greek_text,
                "greek_phrases": greek_phrases,
            }
        )

    all_greek_phrases = [phrase for section in prepared_sections for phrase in section["greek_phrases"]]
    all_translations = {
        lang_id: translate_lines(all_greek_phrases, lang_id, cache)
        for lang_id in TARGET_LANGUAGES
    }

    offset = 0
    for section in prepared_sections:
        greek_phrases = section["greek_phrases"]
        greek_phrase_data = [{"text": phrase, "mapsTo": [index]} for index, phrase in enumerate(greek_phrases)]
        phrase_count = len(greek_phrases)

        translations = OrderedDict()
        for lang_id in TARGET_LANGUAGES:
            translated_lines = all_translations[lang_id][offset : offset + phrase_count]
            translations[lang_id] = {
                "text": normalize_whitespace(" ".join(translated_lines)),
                "phrases": [
                    {"text": translated_lines[index], "mapsTo": [index]}
                    for index in range(len(translated_lines))
                ],
            }

        sections.append(
            {
                "id": section["id"],
                "page": section["page"],
                "order": section["order"],
                "greek": section["greek"],
                "greekPhrases": greek_phrase_data,
                "translations": translations,
            }
        )
        offset += phrase_count

    save_translation_cache(cache)

    pages = OrderedDict()
    for section in sections:
        pages.setdefault(section["page"], []).append(section["id"])

    return {
        "meta": {
            "title": "Plato — Symposium",
            "subtitle": "Greek from Greek Wikisource; English, German, Korean, and Japanese machine-generated directly from the Greek source.",
            "builtAt": str(date.today()),
            "alignmentNote": "Phrase alignment is approximate and order-preserving. It is intended as a reading aid, not as a formal interlinear translation.",
            "translationNote": "English, German, Korean, and Japanese texts were machine-generated directly from the Greek source on a phrase-by-phrase basis during the build step. They are convenience translations and may be inaccurate or stylistically uneven.",
            "modifications": [
                "Normalized whitespace and removed source markup.",
                "Split the Greek text into Stephanus sections (172a–223d).",
                "Added approximate phrase-level alignment metadata for hover highlighting.",
                "Generated English, German, Korean, and Japanese phrase-level translations directly from the Greek source.",
            ],
            "languages": [
                {"id": lang_id, **details} for lang_id, details in TARGET_LANGUAGES.items()
            ],
            "greekSource": {
                "label": "Greek Wikisource — Συμπόσιον (Πλάτων)",
                "url": GREEK_PAGE_URL,
                "historyUrl": GREEK_HISTORY_URL,
                "rawUrl": GREEK_SOURCE_URL,
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
            "generatedTranslations": {
                "langs": ["en", "de", "ko", "ja"],
                "method": "Machine-generated at build time directly from the Greek source using an online translation service endpoint.",
                "rightsNote": "Treat these generated texts conservatively as derivative repository data bundled with the CC BY-SA Greek source and related alignment metadata.",
            },
        },
        "pages": [{"id": key, "sectionIds": value} for key, value in pages.items()],
        "sections": sections,
    }


def main() -> None:
    dataset = build_dataset()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n")
    OUTPUT_JS.write_text(
        "window.SYMPOSIUM_DATA = " + json.dumps(dataset, ensure_ascii=False, indent=2) + ";\n"
    )
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_JS}")
    print(f"Wrote {TRANSLATION_CACHE}")


if __name__ == "__main__":
    main()
