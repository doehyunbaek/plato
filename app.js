const data = window.SYMPOSIUM_DATA;

const languageList = data.meta.languages;
const defaultLanguage = languageList.find((lang) => lang.id === "en")?.id ?? languageList[0]?.id ?? "en";

const state = {
  currentPage: data.pages[0]?.id ?? "172",
  currentLanguage: defaultLanguage,
  query: "",
  locked: null,
};

const pageListEl = document.getElementById("page-list");
const sectionsEl = document.getElementById("sections");
const viewTitleEl = document.getElementById("view-title");
const viewSubtitleEl = document.getElementById("view-subtitle");
const searchInputEl = document.getElementById("search-input");
const searchSummaryEl = document.getElementById("search-summary");
const translationSelectEl = document.getElementById("translation-select");
const translationSummaryEl = document.getElementById("translation-summary");
const infoBannerCopyEl = document.getElementById("info-banner-copy");
const prevPageEl = document.getElementById("prev-page");
const nextPageEl = document.getElementById("next-page");
const clearSearchEl = document.getElementById("clear-search");
const clearHighlightEl = document.getElementById("clear-highlight");

const sectionsByPage = new Map(data.pages.map((page) => [page.id, page.sectionIds]));
const sectionById = new Map(data.sections.map((section) => [section.id, section]));
const pageIds = data.pages.map((page) => page.id);
const languageById = new Map(languageList.map((lang) => [lang.id, lang]));

function currentLanguageMeta() {
  return languageById.get(state.currentLanguage) ?? languageList[0];
}

function translationForSection(section, langId = state.currentLanguage) {
  return section.translations[langId];
}

function normalizeForSearch(value) {
  return String(value)
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
}

function matchesQuery(section, query) {
  if (!query) return true;
  const q = normalizeForSearch(query.trim());
  if (!q) return true;

  const values = [section.id, section.greek];
  for (const lang of languageList) {
    values.push(section.translations[lang.id].text);
  }

  return values.some((value) => normalizeForSearch(value).includes(q));
}

function currentSections() {
  if (state.query.trim()) {
    return data.sections.filter((section) => matchesQuery(section, state.query));
  }

  const ids = sectionsByPage.get(state.currentPage) ?? [];
  return ids.map((id) => sectionById.get(id)).filter(Boolean);
}

function clearHighlightClasses() {
  sectionsEl
    .querySelectorAll(".phrase.is-active, .phrase.is-linked")
    .forEach((node) => node.classList.remove("is-active", "is-linked"));
}

function clearHighlightState() {
  state.locked = null;
  clearHighlightClasses();
}

function highlightPhrase(phraseEl) {
  clearHighlightClasses();
  if (!phraseEl) return;

  const sectionId = phraseEl.dataset.sectionId;
  const side = phraseEl.dataset.side;
  const mapsTo = (phraseEl.dataset.mapsTo || "")
    .split(",")
    .filter(Boolean)
    .map((value) => Number(value));

  phraseEl.classList.add("is-active");

  const oppositeSide = side === "greek" ? "translation" : "greek";
  mapsTo.forEach((index) => {
    const linked = sectionsEl.querySelector(
      `.phrase[data-section-id="${sectionId}"][data-side="${oppositeSide}"][data-index="${index}"]`,
    );
    if (linked) linked.classList.add("is-linked");
  });
}

function phraseSpan(text, sectionId, side, index, mapsTo) {
  const span = document.createElement("span");
  span.className = "phrase";
  span.dataset.sectionId = sectionId;
  span.dataset.side = side;
  span.dataset.index = String(index);
  span.dataset.mapsTo = mapsTo.join(",");
  span.tabIndex = 0;
  span.textContent = `${text} `;
  return span;
}

function renderColumn(title, sideClass, sideKey, phrases, sectionId) {
  const column = document.createElement("section");
  column.className = "column";

  const heading = document.createElement("h4");
  heading.textContent = title;

  const text = document.createElement("p");
  text.className = `text-block ${sideClass}`;

  phrases.forEach((phrase, index) => {
    text.appendChild(phraseSpan(phrase.text, sectionId, sideKey, index, phrase.mapsTo));
  });

  column.append(heading, text);
  return column;
}

function renderSection(section) {
  const card = document.createElement("article");
  card.className = "section-card";
  card.id = `section-${section.id}`;

  const header = document.createElement("header");
  header.className = "section-header";

  const title = document.createElement("h3");
  title.textContent = `Section ${section.id}`;

  const badge = document.createElement("span");
  badge.className = "section-badge";
  badge.textContent = `Stephanus ${section.id}`;

  header.append(title, badge);

  const selectedLanguage = currentLanguageMeta();
  const translation = translationForSection(section);

  const columns = document.createElement("div");
  columns.className = "columns";
  columns.append(
    renderColumn("Greek", "greek", "greek", section.greekPhrases, section.id),
    renderColumn(selectedLanguage.nativeLabel, "english", "translation", translation.phrases, section.id),
  );

  card.append(header, columns);
  return card;
}

function renderTranslationSelector() {
  translationSelectEl.innerHTML = "";
  languageList.forEach((lang) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `translation-button${lang.id === state.currentLanguage ? " active" : ""}`;
    button.textContent = lang.nativeLabel;
    button.title = `${lang.label} — ${lang.note}`;
    button.addEventListener("click", () => {
      state.currentLanguage = lang.id;
      clearHighlightState();
      render();
    });
    translationSelectEl.appendChild(button);
  });
}

function renderPageList() {
  pageListEl.innerHTML = "";
  pageIds.forEach((pageId) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `page-button${pageId === state.currentPage && !state.query.trim() ? " active" : ""}`;
    button.textContent = pageId;
    button.dataset.page = pageId;
    button.addEventListener("click", () => {
      state.currentPage = pageId;
      state.query = "";
      searchInputEl.value = "";
      clearHighlightState();
      render();
    });
    pageListEl.appendChild(button);
  });
}

function renderSummary(sections) {
  const selectedLanguage = currentLanguageMeta();
  translationSummaryEl.textContent = `${selectedLanguage.nativeLabel}: ${selectedLanguage.note}`;

  if (state.query.trim()) {
    viewTitleEl.textContent = `Search results for “${state.query.trim()}”`;
    viewSubtitleEl.textContent = `${sections.length} matching section${sections.length === 1 ? "" : "s"} across Greek and all translations.`;
    searchSummaryEl.textContent = `${sections.length} result${sections.length === 1 ? "" : "s"}`;
  } else {
    const ids = sections.map((section) => section.id);
    viewTitleEl.textContent = `Stephanus ${state.currentPage}`;
    viewSubtitleEl.textContent = ids.length
      ? `Showing ${ids.join(", ")} in Greek + ${selectedLanguage.label}. Hover phrases for approximate cross-language alignment.`
      : "No sections available for this page.";
    searchSummaryEl.textContent = data.meta.alignmentNote;
  }

  const base = "Greek text from Greek Wikisource. English translation from W. R. M. Lamb (1925).";
  if (state.currentLanguage === "en") {
    infoBannerCopyEl.textContent = `${base} Phrase alignment is approximate and intended as a reading aid.`;
  } else {
    infoBannerCopyEl.textContent = `${base} ${selectedLanguage.label} is machine-generated from the English source. Phrase alignment is approximate and intended as a reading aid.`;
  }
}

function renderSections() {
  const sections = currentSections();
  renderSummary(sections);
  sectionsEl.innerHTML = "";

  if (!sections.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No sections matched your search.";
    sectionsEl.appendChild(empty);
    return;
  }

  sections.forEach((section) => sectionsEl.appendChild(renderSection(section)));
}

function updatePageButtons() {
  const currentIndex = pageIds.indexOf(state.currentPage);
  prevPageEl.disabled = currentIndex <= 0;
  nextPageEl.disabled = currentIndex === -1 || currentIndex >= pageIds.length - 1;
}

function render() {
  renderTranslationSelector();
  renderPageList();
  renderSections();
  updatePageButtons();
}

searchInputEl.addEventListener("input", (event) => {
  state.query = event.target.value;
  clearHighlightState();
  render();
});

prevPageEl.addEventListener("click", () => {
  const index = pageIds.indexOf(state.currentPage);
  if (index > 0) {
    state.currentPage = pageIds[index - 1];
    clearHighlightState();
    render();
  }
});

nextPageEl.addEventListener("click", () => {
  const index = pageIds.indexOf(state.currentPage);
  if (index >= 0 && index < pageIds.length - 1) {
    state.currentPage = pageIds[index + 1];
    clearHighlightState();
    render();
  }
});

clearSearchEl.addEventListener("click", () => {
  state.query = "";
  searchInputEl.value = "";
  render();
});

clearHighlightEl.addEventListener("click", () => {
  clearHighlightState();
});

sectionsEl.addEventListener("mouseover", (event) => {
  if (state.locked) return;
  const phrase = event.target.closest(".phrase");
  if (phrase) highlightPhrase(phrase);
});

sectionsEl.addEventListener("focusin", (event) => {
  if (state.locked) return;
  const phrase = event.target.closest(".phrase");
  if (phrase) highlightPhrase(phrase);
});

sectionsEl.addEventListener("mouseout", (event) => {
  if (state.locked) return;
  const next = event.relatedTarget;
  if (!next || !sectionsEl.contains(next)) {
    clearHighlightState();
  }
});

sectionsEl.addEventListener("focusout", () => {
  if (!state.locked) {
    setTimeout(() => {
      if (!sectionsEl.contains(document.activeElement)) clearHighlightState();
    }, 0);
  }
});

sectionsEl.addEventListener("click", (event) => {
  const phrase = event.target.closest(".phrase");
  if (!phrase) return;

  const sameLocked =
    state.locked &&
    state.locked.sectionId === phrase.dataset.sectionId &&
    state.locked.side === phrase.dataset.side &&
    state.locked.index === phrase.dataset.index;

  if (sameLocked) {
    clearHighlightState();
    return;
  }

  state.locked = {
    sectionId: phrase.dataset.sectionId,
    side: phrase.dataset.side,
    index: phrase.dataset.index,
  };
  highlightPhrase(phrase);
});

render();
