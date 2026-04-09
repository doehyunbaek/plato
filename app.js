const data = window.SYMPOSIUM_DATA;

const greekLanguage = {
  id: "gr",
  label: "Greek",
  nativeLabel: "Ελληνικά",
  type: "source",
  note: "Greek source text from Greek Wikisource.",
};

const languageList = [greekLanguage, ...data.meta.languages];
const defaultSelectedLanguages = ["gr", "en"];
const STORAGE_KEY = "plato-symposium-reader-state";

function readStoredState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function sanitizeSelectedLanguages(value) {
  if (!Array.isArray(value)) {
    return defaultSelectedLanguages.filter((id) => languageList.some((lang) => lang.id === id));
  }

  const sanitized = languageList
    .map((lang) => lang.id)
    .filter((id) => value.includes(id));

  return sanitized.length
    ? sanitized
    : defaultSelectedLanguages.filter((id) => languageList.some((lang) => lang.id === id));
}

function sanitizeCurrentPage(value) {
  return pageIds.includes(value) ? value : data.pages[0]?.id ?? "172";
}

const storedState = readStoredState();
const state = {
  currentPage: data.pages[0]?.id ?? "172",
  selectedLanguages: defaultSelectedLanguages.filter((id) => languageList.some((lang) => lang.id === id)),
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

state.currentPage = sanitizeCurrentPage(storedState?.currentPage);
state.selectedLanguages = sanitizeSelectedLanguages(storedState?.selectedLanguages);

function persistState() {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        currentPage: state.currentPage,
        selectedLanguages: state.selectedLanguages,
      }),
    );
  } catch {
    // ignore storage failures
  }
}

function orderedSelectedLanguages() {
  return languageList.filter((lang) => state.selectedLanguages.includes(lang.id));
}

function languageContent(section, langId) {
  if (langId === "gr") {
    return {
      text: section.greek,
      phrases: section.greekPhrases,
    };
  }
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

  const values = [section.id];
  for (const lang of orderedSelectedLanguages()) {
    values.push(languageContent(section, lang.id).text);
  }

  return values.some((value) => normalizeForSearch(value).includes(q));
}

function currentSections() {
  if (state.query.trim()) {
    return data.sections.filter((section) => matchesQuery(section, state.query));
  }

  return data.sections;
}

function firstSectionIdForPage(pageId) {
  return sectionsByPage.get(pageId)?.[0] ?? null;
}

function scrollToPage(pageId) {
  const firstSectionId = firstSectionIdForPage(pageId);
  if (!firstSectionId) return;

  const target = document.getElementById(`section-${firstSectionId}`);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function currentPageFromScroll() {
  if (state.query.trim()) return state.currentPage;

  const threshold = 140;
  let currentSectionId = null;

  for (const section of data.sections) {
    const element = document.getElementById(`section-${section.id}`);
    if (!element) continue;
    if (element.getBoundingClientRect().top <= threshold) {
      currentSectionId = section.id;
    } else {
      break;
    }
  }

  if (!currentSectionId) {
    return data.sections[0]?.page ?? state.currentPage;
  }

  return sectionById.get(currentSectionId)?.page ?? state.currentPage;
}

function syncPageSelectionFromScroll() {
  const scrolledPage = currentPageFromScroll();
  if (scrolledPage === state.currentPage) return;

  state.currentPage = scrolledPage;
  persistState();
  renderPageList();
  updatePageButtons();
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
  const lang = phraseEl.dataset.lang;
  const index = Number(phraseEl.dataset.index);
  const mapsTo = (phraseEl.dataset.mapsTo || "")
    .split(",")
    .filter(Boolean)
    .map((value) => Number(value));

  phraseEl.classList.add("is-active");

  const selected = orderedSelectedLanguages().map((entry) => entry.id);

  if (lang === "gr") {
    for (const otherLang of selected) {
      if (otherLang === "gr") continue;
      mapsTo.forEach((mappedIndex) => {
        const linked = sectionsEl.querySelector(
          `.phrase[data-section-id="${sectionId}"][data-lang="${otherLang}"][data-index="${mappedIndex}"]`,
        );
        if (linked) linked.classList.add("is-linked");
      });
    }
    return;
  }

  mapsTo.forEach((mappedIndex) => {
    const greekPhrase = sectionsEl.querySelector(
      `.phrase[data-section-id="${sectionId}"][data-lang="gr"][data-index="${mappedIndex}"]`,
    );
    if (greekPhrase) greekPhrase.classList.add("is-linked");
  });

  for (const otherLang of selected) {
    if (otherLang === "gr" || otherLang === lang) continue;
    const sibling = sectionsEl.querySelector(
      `.phrase[data-section-id="${sectionId}"][data-lang="${otherLang}"][data-index="${index}"]`,
    );
    if (sibling) sibling.classList.add("is-linked");
  }
}

function phraseSpan(text, sectionId, langId, index, mapsTo) {
  const span = document.createElement("span");
  span.className = "phrase";
  span.dataset.sectionId = sectionId;
  span.dataset.lang = langId;
  span.dataset.index = String(index);
  span.dataset.mapsTo = mapsTo.join(",");
  span.tabIndex = 0;
  span.textContent = `${text} `;
  return span;
}

function renderColumn(language, section) {
  const content = languageContent(section, language.id);

  const column = document.createElement("section");
  column.className = "column";

  const heading = document.createElement("h4");
  heading.textContent = language.nativeLabel;

  const text = document.createElement("p");
  text.className = `text-block lang-${language.id}`;

  content.phrases.forEach((phrase, index) => {
    text.appendChild(phraseSpan(phrase.text, section.id, language.id, index, phrase.mapsTo));
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

  const selected = orderedSelectedLanguages();
  const columns = document.createElement("div");
  columns.className = "columns";
  columns.style.setProperty("--column-count", String(Math.max(selected.length, 1)));

  selected.forEach((language) => {
    columns.appendChild(renderColumn(language, section));
  });

  card.append(header, columns);
  return card;
}

function toggleLanguage(langId) {
  const isSelected = state.selectedLanguages.includes(langId);
  if (isSelected) {
    if (state.selectedLanguages.length === 1) return false;
    state.selectedLanguages = state.selectedLanguages.filter((id) => id !== langId);
  } else {
    state.selectedLanguages = languageList
      .map((lang) => lang.id)
      .filter((id) => state.selectedLanguages.includes(id) || id === langId);
  }
  persistState();
  return true;
}

function renderTranslationSelector() {
  translationSelectEl.innerHTML = "";

  languageList.forEach((lang) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `translation-button${state.selectedLanguages.includes(lang.id) ? " active" : ""}`;
    button.textContent = lang.nativeLabel;
    button.title = `${lang.label} — ${lang.note}`;
    button.setAttribute("aria-pressed", state.selectedLanguages.includes(lang.id) ? "true" : "false");
    button.addEventListener("click", () => {
      const changed = toggleLanguage(lang.id);
      if (!changed) return;
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
    button.className = `page-button${pageId === state.currentPage ? " active" : ""}`;
    button.textContent = pageId;
    button.dataset.page = pageId;
    button.addEventListener("click", () => {
      state.currentPage = pageId;
      persistState();
      clearHighlightState();
      renderPageList();
      if (state.query.trim()) {
        state.query = "";
        searchInputEl.value = "";
        renderSections();
      }
      updatePageButtons();
      requestAnimationFrame(() => scrollToPage(pageId));
    });
    pageListEl.appendChild(button);
  });
}

function renderSummary(sections) {
  const selected = orderedSelectedLanguages();
  const names = selected.map((lang) => lang.nativeLabel).join(" · ");
  const machineLanguages = selected.filter((lang) => lang.type === "machine-generated");

  translationSummaryEl.textContent = `Selected: ${names}`;

  if (state.query.trim()) {
    viewTitleEl.textContent = `Search results for “${state.query.trim()}”`;
    viewSubtitleEl.textContent = `${sections.length} matching section${sections.length === 1 ? "" : "s"} across the currently displayed languages.`;
    searchSummaryEl.textContent = `${sections.length} result${sections.length === 1 ? "" : "s"}`;
  } else {
    viewTitleEl.textContent = "Entire dialogue";
    viewSubtitleEl.textContent = `Showing all Stephanus sections side by side in ${names}. Use the page buttons to jump within the text.`;
    searchSummaryEl.textContent = data.meta.alignmentNote;
  }

  const base = "Greek text from Greek Wikisource.";
  if (!machineLanguages.length) {
    infoBannerCopyEl.textContent = `${base} Phrase alignment is approximate and intended as a reading aid.`;
  } else {
    const machineNames = machineLanguages.map((lang) => lang.label).join(", ");
    infoBannerCopyEl.textContent = `${base} ${machineNames} ${machineLanguages.length === 1 ? "is" : "are"} machine-generated directly from the Greek source. Phrase alignment is approximate and intended as a reading aid.`;
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

let scrollSyncScheduled = false;

function scheduleScrollSync() {
  if (scrollSyncScheduled) return;
  scrollSyncScheduled = true;
  window.requestAnimationFrame(() => {
    scrollSyncScheduled = false;
    syncPageSelectionFromScroll();
  });
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
    persistState();
    clearHighlightState();
    renderPageList();
    updatePageButtons();
    if (state.query.trim()) {
      state.query = "";
      searchInputEl.value = "";
      renderSections();
    }
    requestAnimationFrame(() => scrollToPage(state.currentPage));
  }
});

nextPageEl.addEventListener("click", () => {
  const index = pageIds.indexOf(state.currentPage);
  if (index >= 0 && index < pageIds.length - 1) {
    state.currentPage = pageIds[index + 1];
    persistState();
    clearHighlightState();
    renderPageList();
    updatePageButtons();
    if (state.query.trim()) {
      state.query = "";
      searchInputEl.value = "";
      renderSections();
    }
    requestAnimationFrame(() => scrollToPage(state.currentPage));
  }
});

clearSearchEl.addEventListener("click", () => {
  state.query = "";
  searchInputEl.value = "";
  render();
  requestAnimationFrame(() => scrollToPage(state.currentPage));
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
    state.locked.lang === phrase.dataset.lang &&
    state.locked.index === phrase.dataset.index;

  if (sameLocked) {
    clearHighlightState();
    return;
  }

  state.locked = {
    sectionId: phrase.dataset.sectionId,
    lang: phrase.dataset.lang,
    index: phrase.dataset.index,
  };
  highlightPhrase(phrase);
});

window.addEventListener("storage", (event) => {
  if (event.key !== STORAGE_KEY || !event.newValue) return;

  try {
    const incoming = JSON.parse(event.newValue);
    state.currentPage = sanitizeCurrentPage(incoming.currentPage);
    state.selectedLanguages = sanitizeSelectedLanguages(incoming.selectedLanguages);
    clearHighlightState();
    render();
    if (!state.query.trim()) {
      requestAnimationFrame(() => scrollToPage(state.currentPage));
    }
  } catch {
    // ignore malformed storage updates
  }
});

window.addEventListener("scroll", scheduleScrollSync, { passive: true });
window.addEventListener("resize", scheduleScrollSync);

persistState();
render();
requestAnimationFrame(() => {
  scrollToPage(state.currentPage);
  scheduleScrollSync();
});
