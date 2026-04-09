#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import date
from pathlib import Path

GREEK_SOURCE_URL = "https://el.wikisource.org/w/index.php?title=%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)&action=raw"
GREEK_PAGE_URL = "https://el.wikisource.org/wiki/%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)"
GREEK_HISTORY_URL = "https://el.wikisource.org/w/index.php?title=%CE%A3%CF%85%CE%BC%CF%80%CF%8C%CF%83%CE%B9%CE%BF%CE%BD_(%CE%A0%CE%BB%CE%AC%CF%84%CF%89%CE%BD)&action=history"
ENGLISH_SOURCE_URL = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/tlg0059/tlg011/tlg0059.tlg011.perseus-eng2.xml"
ENGLISH_WORK_URL = "https://github.com/PerseusDL/canonical-greekLit/blob/master/data/tlg0059/tlg011/tlg0059.tlg011.perseus-eng2.xml"
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&dt=t"
OUTPUT_JSON = Path("data/symposium.json")
OUTPUT_JS = Path("data/symposium-data.js")
TRANSLATION_CACHE = Path("data/translation-cache.json")

TARGET_LANGUAGES = OrderedDict(
    {
        "en": {
            "label": "English",
            "nativeLabel": "English",
            "type": "source",
            "note": "Public-domain translation by W. R. M. Lamb (1925).",
        },
        "de": {
            "label": "German",
            "nativeLabel": "Deutsch",
            "type": "machine-generated",
            "note": "Machine-generated from the Lamb English translation during the build step.",
        },
        "ko": {
            "label": "Korean",
            "nativeLabel": "한국어",
            "type": "machine-generated",
            "note": "Machine-generated from the Lamb English translation during the build step.",
        },
        "ja": {
            "label": "Japanese",
            "nativeLabel": "日本語",
            "type": "machine-generated",
            "note": "Machine-generated from the Lamb English translation during the build step.",
        },
    }
)

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
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


def repair_english_sections(sections: OrderedDict[str, str]) -> OrderedDict[str, str]:
    if "181a" in sections and "181b" not in sections:
        split_on = "Now the Love that belongs to the Popular Aphrodite"
        text = sections["181a"]
        if split_on in text:
            before, after = text.split(split_on, 1)
            sections["181a"] = before.strip()
            sections["181b"] = f"{split_on}{after}".strip()

    desired_order = [f"{page}{letter}" for page in range(172, 224) for letter in "abcde"]
    return OrderedDict((key, sections[key]) for key in desired_order if key in sections)


def parse_english_sections(xml_text: str) -> OrderedDict[str, str]:
    root = ET.fromstring(xml_text)
    body = root.find(".//tei:body", NS)
    if body is None:
        raise RuntimeError("Could not find TEI body in English source")

    sections: OrderedDict[str, list[str]] = OrderedDict()
    current: str | None = None

    def walk(node: ET.Element) -> None:
        nonlocal current
        tag = node.tag.split("}")[-1]

        if tag in {"note", "label", "head"}:
            return

        if tag == "milestone" and node.attrib.get("unit") == "section":
            current = node.attrib.get("n")
            if current is not None:
                sections.setdefault(current, [])
            return

        if node.text and current:
            sections[current].append(node.text)

        for child in node:
            walk(child)
            if child.tail and current:
                sections[current].append(child.tail)

    walk(body)
    normalized = OrderedDict((key, normalize_whitespace(" ".join(value))) for key, value in sections.items())
    return repair_english_sections(normalized)


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


def phrase_chunks(text: str) -> list[str]:
    base_segments = [part.strip() for part in STRONG_BREAK.split(text.strip()) if part.strip()]
    chunks: list[str] = []
    for segment in base_segments:
        chunks.extend(split_long_segment(segment))
    chunks = merge_short_segments(chunks)
    return chunks or [text.strip()]


def chunk_intervals(chunks: list[str]) -> list[tuple[float, float]]:
    lengths = [max(len(chunk), 1) for chunk in chunks]
    total = sum(lengths)
    start = 0
    intervals = []
    for length in lengths:
        end = start + length
        intervals.append((start / total, end / total))
        start = end
    return intervals


def interval_center(interval: tuple[float, float]) -> float:
    return (interval[0] + interval[1]) / 2


def build_phrase_alignment(greek_text: str, english_text: str) -> tuple[list[dict], list[dict]]:
    greek_chunks = phrase_chunks(greek_text)
    english_chunks = phrase_chunks(english_text)

    greek_intervals = chunk_intervals(greek_chunks)
    english_intervals = chunk_intervals(english_chunks)

    greek_phrase_data = []
    english_links: list[list[int]] = [[] for _ in english_chunks]

    for greek_index, greek_interval in enumerate(greek_intervals):
        overlaps = []
        for english_index, english_interval in enumerate(english_intervals):
            overlap = min(greek_interval[1], english_interval[1]) - max(greek_interval[0], english_interval[0])
            if overlap > 0.08:
                overlaps.append(english_index)

        if not overlaps:
            center = interval_center(greek_interval)
            overlaps = [
                min(
                    range(len(english_intervals)),
                    key=lambda i: abs(interval_center(english_intervals[i]) - center),
                )
            ]

        greek_phrase_data.append({"text": greek_chunks[greek_index], "mapsTo": overlaps})
        for english_index in overlaps:
            english_links[english_index].append(greek_index)

    english_phrase_data = [
        {"text": english_chunks[index], "mapsTo": links}
        for index, links in enumerate(english_links)
    ]

    return greek_phrase_data, english_phrase_data


def load_translation_cache() -> dict:
    if TRANSLATION_CACHE.exists():
        return json.loads(TRANSLATION_CACHE.read_text())
    return {}


def save_translation_cache(cache: dict) -> None:
    TRANSLATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATION_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")


def cache_key(text: str, target_lang: str) -> str:
    return hashlib.sha1(f"{target_lang}\u241f{text}".encode("utf-8")).hexdigest()


def google_translate_text(text: str, target_lang: str) -> str:
    query = urllib.parse.urlencode({"tl": target_lang, "q": text})
    url = f"{GOOGLE_TRANSLATE_URL}&{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(request).read().decode("utf-8")
    payload = json.loads(raw)
    return "".join(part[0] for part in payload[0])


def translate_lines(lines: list[str], target_lang: str, cache: dict) -> list[str]:
    if target_lang == "en":
        return lines

    joined = "\n".join(lines)
    joined_key = cache_key(joined, target_lang)

    if joined_key in cache:
        translated = cache[joined_key]
    else:
        translated = google_translate_text(joined, target_lang)
        cache[joined_key] = translated

    split_lines = translated.split("\n")
    if len(split_lines) == len(lines):
        return [normalize_whitespace(line) for line in split_lines]

    output = []
    for line in lines:
        line_key = cache_key(line, target_lang)
        if line_key in cache:
            translated_line = cache[line_key]
        else:
            translated_line = google_translate_text(line, target_lang)
            cache[line_key] = translated_line
        output.append(normalize_whitespace(translated_line))
    return output


def translation_phrase_data(english_phrases: list[dict], target_lang: str, cache: dict) -> dict:
    source_lines = [phrase["text"] for phrase in english_phrases]
    translated_lines = translate_lines(source_lines, target_lang, cache)
    translated_phrases = [
        {"text": translated_lines[index], "mapsTo": phrase["mapsTo"]}
        for index, phrase in enumerate(english_phrases)
    ]
    return {
        "text": normalize_whitespace(" ".join(translated_lines)),
        "phrases": translated_phrases,
    }


def page_id(section_id: str) -> str:
    return re.match(r"\d+", section_id).group(0)  # type: ignore[union-attr]


def build_dataset() -> dict:
    greek_sections = parse_greek_sections(fetch_text(GREEK_SOURCE_URL))
    english_sections = parse_english_sections(fetch_text(ENGLISH_SOURCE_URL))

    if list(greek_sections.keys()) != list(english_sections.keys()):
        raise RuntimeError("Greek and English section ids do not match")

    cache = load_translation_cache()
    sections = []

    for order, section_id in enumerate(greek_sections.keys()):
        greek_text = greek_sections[section_id]
        english_text = english_sections[section_id]
        greek_phrases, english_phrases = build_phrase_alignment(greek_text, english_text)

        translations = OrderedDict()
        translations["en"] = {
            "text": english_text,
            "phrases": english_phrases,
        }
        for lang in ("de", "ko", "ja"):
            translations[lang] = translation_phrase_data(english_phrases, lang, cache)

        sections.append(
            {
                "id": section_id,
                "page": page_id(section_id),
                "order": order,
                "greek": greek_text,
                "greekPhrases": greek_phrases,
                "translations": translations,
            }
        )

    save_translation_cache(cache)

    pages = OrderedDict()
    for section in sections:
        pages.setdefault(section["page"], []).append(section["id"])

    return {
        "meta": {
            "title": "Plato — Symposium",
            "subtitle": "Greek from Greek Wikisource; English source translation from W. R. M. Lamb (1925); German, Korean, and Japanese generated client-side data from the English source.",
            "builtAt": str(date.today()),
            "alignmentNote": "Phrase alignment is approximate and order-preserving. It is intended as a reading aid, not as a formal interlinear translation.",
            "translationNote": "German, Korean, and Japanese texts were machine-generated from the Lamb English translation on a phrase-by-phrase basis during the build step. They are convenience translations and may be inaccurate or stylistically uneven.",
            "modifications": [
                "Normalized whitespace and removed source markup.",
                "Split both texts into Stephanus sections (172a–223d).",
                "Added approximate phrase-level alignment metadata for hover highlighting.",
                "Generated German, Korean, and Japanese phrase-level translations from the English source for multilingual reading.",
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
            "englishSource": {
                "label": "PerseusDL TEI — Plato, Symposium, trans. W. R. M. Lamb",
                "url": ENGLISH_WORK_URL,
                "rawUrl": ENGLISH_SOURCE_URL,
                "translator": "Walter Rangeley Maitland Lamb",
                "edition": "Plato in Twelve Volumes, Vol. 3 (1925)",
                "rightsNote": "Treated here as a public-domain English translation in the United States. Check local copyright law before wider redistribution outside the U.S.",
            },
            "generatedTranslations": {
                "langs": ["de", "ko", "ja"],
                "method": "Machine-generated at build time from the English source using an online translation service endpoint.",
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
