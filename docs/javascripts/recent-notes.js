document$.subscribe(() => {
  const container = document.querySelector("[data-recent-notes]");
  if (!container) {
    return;
  }

  fetch("assets/data/recent_notes.json")
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
        meta.textContent = `${note.section} · ${note.date}`;

        link.append(title, meta);
        container.append(link);
      });
    })
    .catch(() => {
      container.innerHTML = '<span class="home-update-card home-update-card--empty">最近更新暂时没有加载出来。</span>';
    });
});
