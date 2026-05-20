document$.subscribe(() => {
  const container = document.querySelector("[data-recent-notes]");
  const recentFilter = document.querySelector("[data-recent-filter]");
  const statsContainer = document.querySelector("[data-site-stats]");
  const randomLink = document.querySelector("[data-random-note]");
  const knowledgeMap = document.querySelector("[data-knowledge-map]");
  const publicArchive = document.querySelector("[data-public-archive]");
  const tagsBrowser = document.querySelector("[data-tags-browser]");
  const relationPanel = document.querySelector("[data-page-relations]");

  setupReadingProgress();

  if (statsContainer || randomLink || knowledgeMap || publicArchive) {
    fetch(resolveDataPath("assets/data/site_stats.json"))
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load site stats: ${response.status}`);
        }
        return response.json();
      })
      .then((stats) => {
        if (statsContainer) {
          renderSiteStats(statsContainer, stats);
        }
        if (knowledgeMap) {
          renderKnowledgeMap(knowledgeMap, stats);
        }
        if (publicArchive) {
          renderPublicArchive(publicArchive, stats);
        }
        const randomPages = Array.isArray(stats.random_pages) ? stats.random_pages : stats.pages;
        if (randomLink && Array.isArray(randomPages) && randomPages.length) {
          randomLink.addEventListener("click", (event) => {
            event.preventDefault();
            const page = randomPages[Math.floor(Math.random() * randomPages.length)];
            window.location.href = resolveSiteUrl(page.url);
          });
        }
      })
      .catch(() => {
        if (statsContainer) {
          statsContainer.innerHTML = '<span class="home-stat home-stat--empty">站点概览暂时没有加载出来。</span>';
        }
        if (knowledgeMap) {
          knowledgeMap.innerHTML = '<span class="home-update-card home-update-card--empty">知识地图暂时没有加载出来。</span>';
        }
        if (publicArchive) {
          publicArchive.innerHTML = '<span class="home-update-card home-update-card--empty">公开文章归档暂时没有加载出来。</span>';
        }
      });
  }

  if (!container && !recentFilter && !tagsBrowser && !relationPanel) {
    return;
  }

  fetch(resolveDataPath("assets/data/garden.json"))
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to load garden data: ${response.status}`);
      }
      return response.json();
    })
    .then((garden) => {
      if (container) {
        renderRecentNotes(container, recentFilter, garden);
      }
      if (tagsBrowser) {
        renderTagsBrowser(tagsBrowser, garden);
      }
      if (relationPanel) {
        renderPageRelations(relationPanel, garden);
      }
    })
    .catch(() => {
      if (container) {
        container.innerHTML = '<span class="home-update-card home-update-card--empty">最近更新暂时没有加载出来。</span>';
      }
      if (tagsBrowser) {
        tagsBrowser.innerHTML = '<span class="home-update-card home-update-card--empty">标签暂时没有加载出来。</span>';
      }
      if (relationPanel) {
        const body = relationPanel.querySelector(".garden-relations__body") || relationPanel;
        body.innerHTML = '<span class="home-update-card home-update-card--empty">关联笔记暂时没有加载出来。</span>';
      }
    });
});

function resolveDataPath(path) {
  return resolveSiteUrl(path);
}

function resolveSiteUrl(path) {
  if (!path) {
    return "#";
  }
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(path) || path.startsWith("//")) {
    return path;
  }

  const normalized = path.replace(/^\/+/, "");
  const base = document.querySelector("base[href]");
  if (base) {
    return new URL(normalized, base.href).toString();
  }
  return new URL(normalized, document.location.origin + "/").toString();
}

function setupReadingProgress() {
  if (document.querySelector(".reading-progress")) {
    return;
  }

  const bar = document.createElement("div");
  bar.className = "reading-progress";
  bar.setAttribute("aria-hidden", "true");
  document.body.append(bar);

  const update = () => {
    const root = document.documentElement;
    const scrollTop = root.scrollTop || document.body.scrollTop;
    const maxScroll = root.scrollHeight - root.clientHeight;
    const progress = maxScroll > 0 ? Math.min(1, Math.max(0, scrollTop / maxScroll)) : 0;
    bar.style.transform = `scaleX(${progress})`;
  };

  update();
  document.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
}

function renderRecentNotes(container, filterContainer, garden) {
  const pages = sortedPages(garden.pages);
  const sections = Array.isArray(garden.sections) ? garden.sections : buildSections(pages);
  let activeSection = "全部";
  const buttons = [];

  const renderList = () => {
    const items =
      activeSection === "全部"
        ? pages
        : pages.filter((page) => page.section === activeSection);

    container.innerHTML = "";
    if (!items.length) {
      container.innerHTML = '<span class="home-update-card home-update-card--empty">这个分区暂时没有公开笔记。</span>';
      return;
    }

    items.slice(0, 6).forEach((note) => {
      container.append(createUpdateCard(note));
    });
  };

  if (filterContainer) {
    filterContainer.innerHTML = "";

    const addButton = (label, count) => {
      const button = document.createElement("button");
      button.className = "home-filter__button";
      button.type = "button";
      button.setAttribute("aria-pressed", label === activeSection ? "true" : "false");
      button.textContent = `${label} ${count}`;
      button.addEventListener("click", () => {
        activeSection = label;
        buttons.forEach((item) => {
          const active = item.label === activeSection;
          item.button.classList.toggle("is-active", active);
          item.button.setAttribute("aria-pressed", active ? "true" : "false");
        });
        renderList();
      });
      buttons.push({ label, button });
      filterContainer.append(button);
    };

    addButton("全部", pages.length);
    sections.forEach((section) => addButton(section.name, section.count));
    if (buttons[0]) {
      buttons[0].button.classList.add("is-active");
    }
  }

  renderList();
}

function renderTagsBrowser(container, garden) {
  const tags = Array.isArray(garden.tags) ? garden.tags.filter((tag) => tag.count) : [];
  if (!tags.length) {
    container.innerHTML = '<span class="home-update-card home-update-card--empty">还没有整理出可展示的标签。</span>';
    return;
  }

  container.innerHTML = "";

  const layout = document.createElement("div");
  layout.className = "tags-browser__layout";

  const tagList = document.createElement("div");
  tagList.className = "tags-browser__tags";
  tagList.setAttribute("aria-label", "标签列表");

  const results = document.createElement("div");
  results.className = "tags-browser__results";

  const buttons = [];
  let activeTag = tags[0].name;

  const renderResults = () => {
    const tag = tags.find((item) => item.name === activeTag);
    results.innerHTML = "";

    if (!tag) {
      results.innerHTML = '<span class="home-update-card home-update-card--empty">没有找到这个标签。</span>';
      return;
    }

    const heading = document.createElement("div");
    heading.className = "tags-browser__heading";

    const title = document.createElement("h2");
    title.textContent = `# ${tag.name}`;

    const count = document.createElement("span");
    count.textContent = `${tag.count} 篇公开笔记`;

    heading.append(title, count);

    const grid = document.createElement("div");
    grid.className = "garden-relations__grid";
    tag.pages.forEach((page) => {
      grid.append(createNoteCard(page));
    });

    results.append(heading, grid);
  };

  tags.forEach((tag) => {
    const button = document.createElement("button");
    button.className = "tags-browser__tag";
    button.type = "button";
    button.setAttribute("aria-pressed", tag.name === activeTag ? "true" : "false");
    button.textContent = `${tag.name} ${tag.count}`;
    button.addEventListener("click", () => {
      activeTag = tag.name;
      buttons.forEach((item) => {
        const active = item.tag === activeTag;
        item.button.classList.toggle("is-active", active);
        item.button.setAttribute("aria-pressed", active ? "true" : "false");
      });
      renderResults();
    });
    buttons.push({ tag: tag.name, button });
    tagList.append(button);
  });

  if (buttons[0]) {
    buttons[0].button.classList.add("is-active");
  }

  layout.append(tagList, results);
  container.append(layout);
  renderResults();
}

function renderPageRelations(panel, garden) {
  const pages = Array.isArray(garden.pages) ? garden.pages : [];
  const src = panel.dataset.pageSrc;
  const page = pages.find((item) => item.src === src);
  const body = panel.querySelector(".garden-relations__body") || panel;

  if (!page) {
    body.innerHTML = '<span class="home-update-card home-update-card--empty">没有找到这篇笔记的关联数据。</span>';
    return;
  }

  const groups = [
    ["正向链接", Array.isArray(page.outgoing) ? page.outgoing : []],
    ["反向链接", Array.isArray(page.backlinks) ? page.backlinks : []],
    ["同标签关联", Array.isArray(page.related) ? page.related : []],
  ].filter(([, items]) => items.length);

  body.innerHTML = "";

  if (!groups.length) {
    body.innerHTML = '<span class="home-update-card home-update-card--empty">这篇笔记暂时还没有公开关联。</span>';
    return;
  }

  groups.forEach(([title, items]) => {
    const section = document.createElement("section");
    section.className = "garden-relations__section";

    const heading = document.createElement("h3");
    heading.textContent = title;

    const grid = document.createElement("div");
    grid.className = "garden-relations__grid";
    items.forEach((item) => {
      grid.append(createNoteCard(item));
    });

    section.append(heading, grid);
    body.append(section);
  });
}

function createUpdateCard(note) {
  const link = document.createElement("a");
  link.className = "home-update-card";
  link.href = resolveSiteUrl(note.url);

  const title = document.createElement("span");
  title.className = "home-update-card__title";
  title.textContent = note.title;

  const tags = document.createElement("span");
  tags.className = "home-update-card__tags";
  (note.tags || []).slice(0, 3).forEach((tag) => {
    const tagEl = document.createElement("span");
    tagEl.textContent = tag;
    tags.append(tagEl);
  });

  const meta = document.createElement("span");
  meta.className = "home-update-card__meta";
  meta.textContent = `${note.section} · ${note.date} · 约 ${note.minutes} 分钟`;

  link.append(title);
  if (tags.children.length) {
    link.append(tags);
  }
  link.append(meta);
  return link;
}

function createNoteCard(page) {
  const link = document.createElement("a");
  link.className = "garden-note-card";
  link.href = resolveSiteUrl(page.url);

  const title = document.createElement("span");
  title.className = "garden-note-card__title";
  title.textContent = page.title;

  const meta = document.createElement("span");
  meta.className = "garden-note-card__meta";
  meta.textContent = `${page.section} · ${page.date || "未知"} · ${page.word_count || "约 0 字"}`;

  const tags = document.createElement("span");
  tags.className = "garden-note-card__tags";
  (page.tags || []).slice(0, 3).forEach((tag) => {
    const tagEl = document.createElement("span");
    tagEl.textContent = tag;
    tags.append(tagEl);
  });

  link.append(title, meta);
  if (tags.children.length) {
    link.append(tags);
  }
  return link;
}

function sortedPages(pages) {
  return Array.isArray(pages)
    ? [...pages].sort((a, b) => (b.updated || "").localeCompare(a.updated || ""))
    : [];
}

function buildSections(pages) {
  const map = new Map();
  pages.forEach((page) => {
    const section = page.section || "未分类";
    map.set(section, (map.get(section) || 0) + 1);
  });
  return Array.from(map.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "zh-Hans-CN"));
}

function renderSiteStats(container, stats) {
  const items = [
    ["笔记", `${stats.article_count || 0} 篇`],
    ["总字数", stats.total_word_count || "约 0 字"],
    ["大类", `${stats.section_count || 0} 个`],
    ["最近更新", stats.date || "未知"],
  ];

  container.innerHTML = "";
  items.forEach(([label, value]) => {
    const item = document.createElement("span");
    item.className = "home-stat";

    const valueEl = document.createElement("strong");
    valueEl.textContent = value;

    const labelEl = document.createElement("small");
    labelEl.textContent = label;

    item.append(valueEl, labelEl);
    container.append(item);
  });
}

function renderKnowledgeMap(container, stats) {
  const pages = Array.isArray(stats.random_pages) ? stats.random_pages : [];
  const grouped = new Map();

  pages.forEach((page) => {
    const directory = page.directory || "未分类";
    if (!grouped.has(directory)) {
      grouped.set(directory, []);
    }
    grouped.get(directory).push(page);
  });

  container.innerHTML = "";

  Array.from(grouped.entries())
    .sort(([a], [b]) => a.localeCompare(b, "zh-Hans-CN"))
    .forEach(([directory, items]) => {
      items.sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));

      const section = document.createElement("section");
      section.className = "knowledge-map__section";

      const heading = document.createElement("h2");
      heading.textContent = formatDirectoryName(directory);

      const list = document.createElement("div");
      list.className = "knowledge-map__list";

      items.forEach((page) => {
        const link = document.createElement("a");
        link.className = "knowledge-map__item";
        link.href = resolveSiteUrl(page.url);

        const title = document.createElement("span");
        title.className = "knowledge-map__title";
        title.textContent = page.title;

        const meta = document.createElement("span");
        meta.className = "knowledge-map__meta";
        meta.textContent = `${page.date} · ${page.word_count} · 约 ${page.minutes} 分钟`;

        link.append(title, meta);
        list.append(link);
      });

      section.append(heading, list);
      container.append(section);
    });
}

function renderPublicArchive(container, stats) {
  const pages = Array.isArray(stats.random_pages) ? [...stats.random_pages] : [];
  pages.sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));

  container.innerHTML = "";

  pages.forEach((page) => {
    const link = document.createElement("a");
    link.className = "home-archive__item";
    link.href = resolveSiteUrl(page.url);

    const date = document.createElement("time");
    date.className = "home-archive__date";
    date.dateTime = page.date || "";
    date.textContent = page.date || "未知";

    const main = document.createElement("span");
    main.className = "home-archive__main";

    const title = document.createElement("span");
    title.className = "home-archive__title";
    title.textContent = page.title;

    const section = document.createElement("span");
    section.className = "home-archive__section";
    section.textContent = page.section;

    const meta = document.createElement("span");
    meta.className = "home-archive__meta";
    meta.textContent = `${page.word_count} · 约 ${page.minutes} 分钟`;

    main.append(title, section);
    link.append(date, main, meta);
    container.append(link);
  });
}

function formatDirectoryName(directory) {
  return directory
    .split("/")
    .filter(Boolean)
    .map((part) => part.replace(/-/g, " "))
    .join(" / ");
}
