document$.subscribe(() => {
  const container = document.querySelector("[data-recent-notes]");
  const statsContainer = document.querySelector("[data-site-stats]");
  const randomLink = document.querySelector("[data-random-note]");
  const tagsBrowser = document.querySelector("[data-tags-browser]");
  const relationPanel = document.querySelector("[data-page-relations]");

  if (statsContainer || randomLink) {
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
        const randomPages = Array.isArray(stats.random_pages) ? stats.random_pages : stats.pages;
        if (randomLink && Array.isArray(randomPages) && randomPages.length) {
          randomLink.addEventListener("click", (event) => {
            event.preventDefault();
            const page = randomPages[Math.floor(Math.random() * randomPages.length)];
            const label = randomLink.querySelector("[data-random-label]");
            randomLink.classList.add("is-rolling");
            if (label) {
              label.textContent = "正在寻找一篇笔记…";
            }
            window.setTimeout(() => {
              window.location.href = resolveSiteUrl(page.url);
            }, 280);
          });
        }
      })
      .catch(() => {
        if (statsContainer) {
          statsContainer.innerHTML = '<span class="home-stat home-stat--empty">站点概览暂时没有加载出来。</span>';
        }
      });
  }

  if (!container && !tagsBrowser && !relationPanel) {
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
        renderRecentNotes(container, garden);
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
        relationPanel.hidden = true;
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

function renderRecentNotes(container, garden) {
  const pages = sortedPages(garden.pages);
  container.innerHTML = "";
  if (!pages.length) {
    container.innerHTML = '<span class="home-update-card home-update-card--empty">这座花园还没有公开笔记。</span>';
    return;
  }

  pages.slice(0, 5).forEach((note, index) => {
    container.append(createUpdateCard(note, index));
  });
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
    panel.hidden = true;
    return;
  }

  const groups = [
    ["正向链接", Array.isArray(page.outgoing) ? page.outgoing : []],
    ["反向链接", Array.isArray(page.backlinks) ? page.backlinks : []],
    ["同标签关联", Array.isArray(page.related) ? page.related : []],
  ].filter(([, items]) => items.length);

  body.innerHTML = "";

  if (!groups.length) {
    panel.hidden = true;
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

function createUpdateCard(note, index = 0) {
  const link = document.createElement("a");
  link.className = index === 0 ? "home-update-card home-update-card--featured" : "home-update-card";
  link.href = resolveSiteUrl(note.url);

  const number = document.createElement("span");
  number.className = "home-update-card__number";
  number.textContent = String(index + 1).padStart(2, "0");

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
  meta.textContent = `${note.section} · ${note.date} · ${note.word_count || ""} · 约 ${note.minutes} 分钟`;

  const arrow = document.createElement("span");
  arrow.className = "home-update-card__arrow";
  arrow.setAttribute("aria-hidden", "true");
  arrow.textContent = "↗";

  link.append(number, title, arrow);
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

function renderSiteStats(container, stats) {
  const items = [
    ["公开笔记", `${stats.article_count || 0} 篇`],
    ["已记录", stats.total_word_count || "约 0 字"],
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
