let siteStatsRequest;

document$.subscribe(() => {
  const container = document.querySelector("[data-recent-notes]");
  const statsContainer = document.querySelector("[data-site-stats]");
  const randomLink = document.querySelector("[data-random-note]");

  if (!container && !statsContainer && !randomLink) {
    return;
  }

  if (!siteStatsRequest) {
    siteStatsRequest = fetch(resolveDataPath("assets/data/site_stats.json"))
      .then((response) => {
        if (!response.ok) throw new Error(`Failed to load site stats: ${response.status}`);
        return response.json();
      })
      .catch((error) => { siteStatsRequest = null; throw error; });
  }

  siteStatsRequest
    .then((stats) => {
      if (statsContainer) {
        renderSiteStats(statsContainer, stats);
      }
      if (container) {
        renderRecentNotes(container, stats.pages);
      }

      const randomPages = Array.isArray(stats.random_pages) ? stats.random_pages : stats.pages;
      if (randomLink && Array.isArray(randomPages) && randomPages.length) {
        const chooseNote = () => {
          const page = randomPages[Math.floor(Math.random() * randomPages.length)];
          randomLink.href = resolveSiteUrl(page.url);
        };
        chooseNote();
        // Set the native link target before Material intercepts the click.
        randomLink.addEventListener("pointerdown", chooseNote);
        randomLink.addEventListener("keydown", (event) => {
          if (event.key === "Enter") chooseNote();
        });
      }
    })
    .catch(() => {
      if (statsContainer) {
        statsContainer.innerHTML = '<span class="home-stat home-stat--empty">站点概览暂时没有加载出来。</span>';
      }
      if (container) {
        container.innerHTML = '<span class="home-update-card home-update-card--empty">最近更新暂时没有加载出来。</span>';
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

function renderRecentNotes(container, pages) {
  const notes = sortedPages(pages);
  container.innerHTML = "";
  if (!notes.length) {
    container.innerHTML = '<span class="home-update-card home-update-card--empty">这座花园还没有公开笔记。</span>';
    return;
  }

  notes.slice(0, 5).forEach((note, index) => {
    container.append(createUpdateCard(note, index));
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

  const meta = document.createElement("span");
  meta.className = "home-update-card__meta";
  meta.textContent = `${note.section} · ${note.date} · ${note.word_count || ""} · 约 ${note.minutes} 分钟`;

  const arrow = document.createElement("span");
  arrow.className = "home-update-card__arrow";
  arrow.setAttribute("aria-hidden", "true");
  arrow.textContent = "↗";

  link.append(number, title, arrow, meta);
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
