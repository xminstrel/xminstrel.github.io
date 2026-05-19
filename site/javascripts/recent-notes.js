document$.subscribe(() => {
  const container = document.querySelector("[data-recent-notes]");
  const statsContainer = document.querySelector("[data-site-stats]");
  const randomLink = document.querySelector("[data-random-note]");
  const knowledgeMap = document.querySelector("[data-knowledge-map]");

  setupReadingProgress();

  if (statsContainer || randomLink || knowledgeMap) {
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
        const randomPages = Array.isArray(stats.random_pages) ? stats.random_pages : stats.pages;
        if (randomLink && Array.isArray(randomPages) && randomPages.length) {
          randomLink.addEventListener("click", (event) => {
            event.preventDefault();
            const page = randomPages[Math.floor(Math.random() * randomPages.length)];
            window.location.href = page.url;
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
      });
  }

  if (!container) {
    return;
  }

  fetch(resolveDataPath("assets/data/recent_notes.json"))
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to load recent notes: ${response.status}`);
      }
      return response.json();
    })
    .then((notes) => {
      container.innerHTML = "";

      notes.forEach((note) => {
        const link = document.createElement("a");
        link.className = "home-update-card";
        link.href = note.url;

        const title = document.createElement("span");
        title.className = "home-update-card__title";
        title.textContent = note.title;

        const meta = document.createElement("span");
        meta.className = "home-update-card__meta";
        meta.textContent = `${note.section} · ${note.date} · 约 ${note.minutes} 分钟`;

        link.append(title, meta);
        container.append(link);
      });
    })
    .catch(() => {
      container.innerHTML = '<span class="home-update-card home-update-card--empty">最近更新暂时没有加载出来。</span>';
    });
});

function resolveDataPath(path) {
  const base = document.querySelector("base[href]");
  if (base) {
    return new URL(path, base.href).toString();
  }
  return new URL(path, document.location.origin + "/").toString();
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
        link.href = page.url;

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

function formatDirectoryName(directory) {
  return directory
    .split("/")
    .filter(Boolean)
    .map((part) => part.replace(/-/g, " "))
    .join(" / ");
}
